from __future__ import annotations

import uuid as uuid_lib

from django.http import HttpRequest

from airam_app.models import AiramConceptWeight, AiramSession
from ontologizar_app.models import Concept

WEIGHT_DELTAS = {
    "visited": 1,
    "revisit": 1,
    "relation_opened": 2,
    "note": 5,
    "interpretation": 10,
}


def default_workspace_state() -> dict:
    return {
        "explored_concept_uuids": [],
        "workspace_roots": [],
    }


def workspace_frame(session: AiramSession, *, limit: int = 12) -> list[dict]:
    rows = AiramConceptWeight.objects.filter(session=session).order_by(
        "-weight", "-updated_at",
    )[:limit]
    return [
        {
            "concept_uuid": str(row.concept_uuid),
            "label": row.concept_label,
            "weight": row.weight,
            "visit_count": row.visit_count,
            "subject_slug": row.subject_slug,
            "dictionary_slug": row.dictionary_slug,
            "taxonomy_slug": row.taxonomy_slug,
        }
        for row in rows
    ]


def record_concept_event(
    session: AiramSession,
    concept: Concept,
    event_type: str = "visited",
) -> AiramConceptWeight:
    if not session.is_workspace:
        raise ValueError("Solo aplica a sesiones workspace")

    row, created = AiramConceptWeight.objects.get_or_create(
        session=session,
        concept_uuid=concept.uuid,
        defaults={
            "concept_label": concept.label,
            "subject_slug": concept.dictionary.subject.slug,
            "dictionary_slug": concept.dictionary.slug,
            "taxonomy_slug": concept.primary_taxonomy_slug(),
        },
    )
    if not created:
        if not row.concept_label:
            row.concept_label = concept.label
            row.subject_slug = concept.dictionary.subject.slug
            row.dictionary_slug = concept.dictionary.slug
            row.taxonomy_slug = concept.primary_taxonomy_slug()

    if event_type == "visited" and row.visit_count > 0:
        event_type = "revisit"

    delta = WEIGHT_DELTAS.get(event_type, 1)
    row.weight += delta
    if event_type in ("visited", "revisit"):
        row.visit_count += 1
    row.save()

    state = dict(session.state or default_workspace_state())
    explored = list(state.get("explored_concept_uuids") or [])
    cu = str(concept.uuid)
    if cu not in explored:
        explored.append(cu)
    state["explored_concept_uuids"] = explored
    session.state = state
    session.save(update_fields=["state", "updated_at"])
    return row


def record_concept_uuid_event(
    session: AiramSession,
    concept_uuid: str,
    event_type: str = "visited",
) -> AiramConceptWeight | None:
    try:
        uuid_lib.UUID(str(concept_uuid))
    except ValueError:
        return None
    concept = Concept.objects.filter(uuid=concept_uuid).select_related(
        "dictionary__subject",
    ).first()
    if not concept:
        return None
    return record_concept_event(session, concept, event_type)


def link_workspace_project(session: AiramSession, project_uuid: str) -> AiramSession:
    from research_app.models import ProyectoInvestigacion

    if not session.is_workspace:
        raise ValueError("Solo aplica a sesiones workspace")
    try:
        parsed = uuid_lib.UUID(str(project_uuid))
    except ValueError as exc:
        raise ValueError("project_uuid inválido") from exc
    project = ProyectoInvestigacion.objects.get(uuid=parsed)
    session.project_uuid = project.uuid
    session.title = f"Marco — {project.acron or project.titulo}"
    session.save(update_fields=["project_uuid", "title", "updated_at"])
    return session


def promote_workspace_markers(
    session: AiramSession,
    *,
    min_weight: int = 5,
    status: str = "selected",
    created_by: str = "",
) -> list[dict]:
    from research_app.models import LearningMarker, ProyectoInvestigacion

    if not session.is_workspace or not session.project_uuid:
        raise ValueError("Workspace sin proyecto vinculado")

    project = ProyectoInvestigacion.objects.get(uuid=session.project_uuid)
    promoted = []
    for row in AiramConceptWeight.objects.filter(session=session, weight__gte=min_weight):
        concept = Concept.objects.filter(uuid=row.concept_uuid).first()
        if not concept:
            continue
        exists = LearningMarker.objects.filter(project=project, concept_uuid=row.concept_uuid).exists()
        marker = LearningMarker.upsert_for_concept(
            project,
            concept,
            status=status,
            note=f"Promovido desde AIRAM (peso {row.weight})",
            created_by=created_by,
        )
        if not exists:
            promoted.append({
                "concept_uuid": str(row.concept_uuid),
                "label": row.concept_label,
                "marker_uuid": str(marker.uuid),
            })
    return promoted


def workspace_to_dict(session: AiramSession) -> dict:
    project_title = ""
    if session.project_uuid:
        from research_app.models import ProyectoInvestigacion
        project = ProyectoInvestigacion.objects.filter(uuid=session.project_uuid).first()
        if project:
            project_title = project.acron or project.titulo

    return {
        "uuid": str(session.uuid),
        "session_kind": session.session_kind,
        "title": session.title,
        "project_uuid": str(session.project_uuid) if session.project_uuid else None,
        "project_title": project_title,
        "is_bookmarked": session.is_bookmarked,
        "updated_at": session.updated_at.isoformat(),
        "state": session.state,
        "frame": workspace_frame(session),
        "view": {
            "mode": "workspace",
            "frame": workspace_frame(session),
            "can_continue": False,
            "paragraphs": [],
        },
    }
