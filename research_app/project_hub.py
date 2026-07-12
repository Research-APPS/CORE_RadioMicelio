from __future__ import annotations
from dataclasses import dataclass, field
from uuid import UUID

from django.conf import settings
from django.urls import reverse

from research_app.capability_registry import ProjectCapabilityDescriptor, get_competency
from research_app.models import (
    LearningMarker, ProyectoInvestigacion, ProjectCurriculumDeclaration,
    ScientificActivity, ScientificResult,
)


@dataclass
class ProjectDigitalProfile:
    project_uuid: str
    titulo: str
    acron: str
    institute: str
    markers: list[dict] = field(default_factory=list)
    curriculum: dict = field(default_factory=dict)
    capabilities: list[ProjectCapabilityDescriptor] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "project_uuid": self.project_uuid,
            "titulo": self.titulo,
            "acron": self.acron,
            "institute": self.institute,
            "markers": self.markers,
            "curriculum": self.curriculum,
            "capabilities": [c.to_dict() for c in self.capabilities],
            "metrics": self.metrics,
        }


def _logs_descriptor(project_uuid):
    from logs_app.services.research_bridge import get_logs_descriptor
    return get_logs_descriptor(project_uuid)


def _distinct_project_markers(project):
    """Un marcador por concepto (el más reciente)."""
    seen = {}
    for marker in project.markers.order_by("-created_at", "-id"):
        key = str(marker.concept_uuid)
        if key not in seen:
            seen[key] = marker
    return seen.values()


def get_project_digital_profile(project_uuid: UUID) -> ProjectDigitalProfile | None:
    project = ProyectoInvestigacion.objects.filter(uuid=project_uuid, activo=True).first()
    if not project:
        return None

    markers = [
        {
            "concept_uuid": str(m.concept_uuid),
            "concept_label": m.concept_label,
            "subject": m.subject_slug,
            "dictionary": m.dictionary_slug,
            "taxonomy": m.taxonomy_slug,
            "status": m.status,
            "status_label": m.get_status_display(),
            "jsonld_url": reverse(
                "research:marker_jsonld",
                kwargs={"uuid": project.uuid, "concept_uuid": m.concept_uuid},
            ),
            "graph_url": reverse(
                "ontologizar:concept_jsonld",
                kwargs={"uuid": m.concept_uuid},
            ) + "?graph=1",
            "note": m.note,
            "topic_url": reverse("biblioteca:topic", kwargs={"uuid": m.concept_uuid}),
        }
        for m in _distinct_project_markers(project)
    ]

    declarations = list(
        project.declarations.values_list("capability_slug", flat=True)
    )
    activities = []
    for a in ScientificActivity.objects.filter(
        notebook_links__project=project,
    ).prefetch_related("capability_links", "results", "notebook_links__project").distinct():
        results_grouped = []
        by_slug: dict[str, list] = {}
        for r in a.results.all():
            by_slug.setdefault(r.capability_slug, []).append({
                "title": r.title,
                "type": r.result_type,
                "publish_url": r.publish_url,
            })
        for slug in a.get_capability_slugs():
            cap = get_competency(slug)
            items = by_slug.get(slug, [])
            if items:
                results_grouped.append({
                    "capability_slug": slug,
                    "capability_label": cap["label"] if cap else slug,
                    "items": items,
                })
        activities.append({
            "slug": a.slug,
            "title": a.title,
            "capability": a.capability_slug,
            "capabilities": a.get_capability_slugs(),
            "capability_labels": a.get_capability_labels(),
            "notebooks": [
                {"uuid": str(nb.uuid), "titulo": nb.titulo, "acron": nb.acron}
                for nb in a.get_notebooks()
            ],
            "status": a.status,
            "status_label": a.get_status_display(),
            "uuid": str(a.uuid),
            "results": [r.title for r in a.results.all()],
            "results_grouped": results_grouped,
        })

    capabilities = []
    if "logs" in getattr(settings, "CORE_ENABLED_MODULES", []):
        desc = _logs_descriptor(project_uuid)
        if desc:
            capabilities.append(desc)

    metrics = {"marker_count": len(markers), "activity_count": len(activities)}
    if capabilities and capabilities[0].summary.get("unique_users"):
        metrics["users"] = capabilities[0].summary.get("unique_users")
        metrics["visits"] = capabilities[0].summary.get("total_events")

    return ProjectDigitalProfile(
        project_uuid=str(project_uuid),
        titulo=project.titulo,
        acron=project.acron,
        institute=getattr(settings, "CORE_INSTITUTE_NAME", "CORE Radio Micelio"),
        markers=markers,
        curriculum={
            "declared_capabilities": declarations,
            "activities": activities,
        },
        capabilities=capabilities,
        metrics=metrics,
    )
