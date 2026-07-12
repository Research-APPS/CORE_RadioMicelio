from __future__ import annotations

import json
import uuid as uuid_lib

from django.http import HttpRequest
from django.utils import timezone

from airam_app.models import AiramSession
from airam_app.services.workspace import (
    default_workspace_state,
    link_workspace_project,
    promote_workspace_markers,
    record_concept_uuid_event,
    workspace_frame,
    workspace_to_dict,
)
from airam_app.services.temario import (
    GRANULARITIES,
    combined_subtree_nodes,
    narrate_concept,
    narrate_node,
    next_node_in_session,
    next_node_in_subtree,
    node_breadcrumb,
    segment_start_labels,
    session_nodes,
    subtree_nodes,
)
from ontologizar_app.models import Concept, Taxonomy, TaxonomyNode


def _session_key(request: HttpRequest) -> str:
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key or ""


def _can_access(session: AiramSession, request: HttpRequest) -> bool:
    if session.owner_username and request.user.is_authenticated:
        return session.owner_username == request.user.username
    return session.session_key == _session_key(request)


def _default_state() -> dict:
    return {"explored_concept_uuids": [], "exploring_concept_uuid": None, "combined_node_uuids": []}


def _combined_title(nodes: list[TaxonomyNode], taxonomy: Taxonomy) -> str:
    if len(nodes) == 1:
        return f"{nodes[0].label} — {taxonomy.name}"
    labels = [n.label for n in nodes[:3]]
    title = " + ".join(labels)
    if len(nodes) > 3:
        title += f" (+{len(nodes) - 3})"
    return f"{title} — {taxonomy.name}"


def _resolve_session_nodes(taxonomy: Taxonomy, node_uuids: list[str]) -> list[TaxonomyNode]:
    nodes: list[TaxonomyNode] = []
    for uuid in node_uuids:
        nodes.append(
            TaxonomyNode.objects.select_related("taxonomy").get(uuid=uuid, taxonomy=taxonomy)
        )
    return nodes


def create_session(
    request: HttpRequest,
    *,
    taxonomy_slug: str,
    node_uuid: str = "",
    node_uuids: list[str] | None = None,
    granularity: str = "normal",
) -> AiramSession:
    taxonomy = Taxonomy.objects.get(slug=taxonomy_slug, is_active=True)
    uuids = [u.strip() for u in (node_uuids or []) if u and u.strip()]
    if not uuids and node_uuid:
        uuids = [node_uuid.strip()]
    if not uuids:
        raise ValueError("Se requiere al menos una clase (node_uuid o node_uuids).")

    nodes = _resolve_session_nodes(taxonomy, uuids)
    root_node = nodes[0]
    if granularity not in GRANULARITIES:
        granularity = "normal"

    state = _default_state()
    state["combined_node_uuids"] = [str(n.uuid) for n in nodes]

    session = AiramSession.objects.create(
        title=_combined_title(nodes, taxonomy),
        session_kind="temario",
        taxonomy=taxonomy,
        root_node=root_node,
        last_node=root_node,
        granularity=granularity,
        state=state,
        owner_username=request.user.username if request.user.is_authenticated else "",
        session_key=_session_key(request),
    )
    return session


def create_workspace(request: HttpRequest, *, project_uuid: str = "") -> AiramSession:
    parsed_project = None
    if project_uuid:
        try:
            parsed_project = uuid_lib.UUID(project_uuid.strip())
        except ValueError:
            parsed_project = None

    title = "Marco de trabajo"
    if parsed_project:
        from research_app.models import ProyectoInvestigacion
        project = ProyectoInvestigacion.objects.filter(uuid=parsed_project).first()
        if project:
            title = f"Marco — {project.acron or project.titulo}"

    return AiramSession.objects.create(
        title=title,
        session_kind="workspace",
        taxonomy=None,
        root_node=None,
        project_uuid=parsed_project,
        state=default_workspace_state(),
        owner_username=request.user.username if request.user.is_authenticated else "",
        session_key=_session_key(request),
    )


def get_or_create_workspace(request: HttpRequest) -> AiramSession:
    sk = _session_key(request)
    session = AiramSession.objects.filter(
        session_kind="workspace", session_key=sk, is_bookmarked=False,
    ).order_by("-updated_at").first()
    if session:
        return session
    return create_workspace(request)


def session_to_dict(session: AiramSession, *, include_view: bool = True) -> dict:
    if session.is_workspace:
        data = workspace_to_dict(session)
        if not include_view:
            data.pop("view", None)
        return data

    combined_uuids = list((session.state or {}).get("combined_node_uuids") or [])
    if not combined_uuids:
        combined_uuids = [str(session.root_node.uuid)]

    combined_nodes = []
    nodes_by_uuid = {
        str(n.uuid): n
        for n in TaxonomyNode.objects.filter(
            taxonomy_id=session.taxonomy_id,
            uuid__in=combined_uuids,
        )
    }
    for uuid in combined_uuids:
        node = nodes_by_uuid.get(str(uuid))
        if node:
            combined_nodes.append({"uuid": str(node.uuid), "label": node.label})

    data = {
        "uuid": str(session.uuid),
        "title": session.title,
        "taxonomy_slug": session.taxonomy.slug,
        "taxonomy_name": session.taxonomy.name,
        "root_node_uuid": str(session.root_node.uuid),
        "last_node_uuid": str(session.last_node.uuid) if session.last_node_id else None,
        "combined_nodes": combined_nodes,
        "granularity": session.granularity,
        "is_bookmarked": session.is_bookmarked,
        "bookmarked_at": session.bookmarked_at.isoformat() if session.bookmarked_at else None,
        "updated_at": session.updated_at.isoformat(),
        "state": session.state,
    }
    if include_view:
        data["view"] = build_session_view(session)
    return data


def build_session_view(session: AiramSession) -> dict:
    if session.is_workspace:
        frame = workspace_frame(session)
        return {
            "mode": "workspace",
            "frame": frame,
            "can_continue": False,
            "paragraphs": [
                "Tu marco de trabajo emerge mientras exploras conceptos entre taxonomías.",
            ],
        }

    state = session.state or _default_state()
    exploring = state.get("exploring_concept_uuid")

    if exploring:
        concept = Concept.objects.filter(uuid=exploring).select_related("dictionary").first()
        if concept:
            block = narrate_concept(concept, session.granularity)
            block["mode"] = "explore"
            block["can_continue"] = True
            return block

    node = session.last_node or session.root_node
    block = narrate_node(node, session.granularity)
    nodes = session_nodes(session)
    node_pks = [n.pk for n in nodes]
    try:
        current_idx = node_pks.index(node.pk)
    except ValueError:
        current_idx = 0

    segment_labels = segment_start_labels(session)
    segment_label = segment_labels.get(str(node.uuid))
    if segment_label and current_idx > 0:
        block["paragraphs"].insert(0, f"Clase: {segment_label}.")

    at_end = next_node_in_session(session, node) is None
    block["mode"] = "temario"
    block["can_continue"] = not at_end
    block["progress"] = {"current": current_idx + 1, "total": len(nodes)}
    return block


def patch_session(session: AiramSession, payload: dict) -> AiramSession:
    if session.is_workspace:
        return patch_workspace(session, payload)

    action = payload.get("action", "continue")
    state = dict(session.state or _default_state())

    if action == "set_granularity":
        g = payload.get("granularity", session.granularity)
        if g in GRANULARITIES:
            session.granularity = g
        state["exploring_concept_uuid"] = None

    elif action == "explore_concept":
        cu = payload.get("concept_uuid", "").strip()
        if cu:
            try:
                uuid_lib.UUID(cu)
            except ValueError:
                pass
            else:
                state["exploring_concept_uuid"] = cu
                explored = list(state.get("explored_concept_uuids") or [])
                if cu not in explored:
                    explored.append(cu)
                state["explored_concept_uuids"] = explored

    elif action == "continue":
        state["exploring_concept_uuid"] = None
        current = session.last_node or session.root_node
        nxt = next_node_in_session(session, current)
        if nxt:
            session.last_node = nxt

    elif action == "add_class":
        nu = payload.get("node_uuid", "").strip()
        if nu:
            try:
                uuid_lib.UUID(nu)
            except ValueError:
                pass
            else:
                TaxonomyNode.objects.get(uuid=nu, taxonomy=session.taxonomy)
                combined = list(state.get("combined_node_uuids") or [str(session.root_node.uuid)])
                if nu not in combined:
                    combined.append(nu)
                state["combined_node_uuids"] = combined
                nodes = _resolve_session_nodes(session.taxonomy, combined)
                session.title = _combined_title(nodes, session.taxonomy)

    elif action == "remove_class":
        nu = payload.get("node_uuid", "").strip()
        combined = list(state.get("combined_node_uuids") or [str(session.root_node.uuid)])
        if nu and nu in combined and len(combined) > 1:
            combined.remove(nu)
            state["combined_node_uuids"] = combined
            nodes = _resolve_session_nodes(session.taxonomy, combined)
            session.title = _combined_title(nodes, session.taxonomy)
            session.root_node = nodes[0]
            flat = combined_subtree_nodes(session.taxonomy_id, combined)
            flat_pks = [n.pk for n in flat]
            if session.last_node_id and session.last_node_id not in flat_pks:
                session.last_node = flat[0] if flat else session.root_node

    session.state = state
    session.save(update_fields=["granularity", "last_node", "root_node", "title", "state", "updated_at"])
    return session


def patch_workspace(session: AiramSession, payload: dict) -> AiramSession:
    action = payload.get("action", "")
    created_by = payload.get("created_by", "")

    if action == "record_concept":
        record_concept_uuid_event(
            session,
            str(payload.get("concept_uuid", "")).strip(),
            str(payload.get("event_type", "visited")).strip() or "visited",
        )
    elif action == "link_project":
        link_workspace_project(session, str(payload.get("project_uuid", "")).strip())
    elif action == "promote_markers":
        min_weight = int(payload.get("min_weight", 5) or 5)
        promote_workspace_markers(
            session,
            min_weight=min_weight,
            created_by=created_by,
        )
    elif action == "add_root":
        root = payload.get("workspace_root") or {}
        taxonomy_slug = str(root.get("taxonomy_slug", "")).strip()
        node_uuid = str(root.get("node_uuid", "")).strip()
        if taxonomy_slug and node_uuid:
            node = TaxonomyNode.objects.select_related("taxonomy").filter(
                uuid=node_uuid, taxonomy__slug=taxonomy_slug,
            ).first()
            if node:
                state = dict(session.state or default_workspace_state())
                roots = list(state.get("workspace_roots") or [])
                entry = {
                    "taxonomy_slug": taxonomy_slug,
                    "node_uuid": str(node.uuid),
                    "label": node.label,
                }
                if entry not in roots:
                    roots.append(entry)
                state["workspace_roots"] = roots
                session.state = state
                session.save(update_fields=["state", "updated_at"])
    else:
        raise ValueError(f"Acción workspace desconocida: {action}")
    return session


def bookmark_session(session: AiramSession) -> AiramSession:
    session.is_bookmarked = True
    session.bookmarked_at = timezone.now()
    session.save(update_fields=["is_bookmarked", "bookmarked_at", "updated_at"])
    return session


def get_session_for_request(request: HttpRequest, session_uuid: str) -> AiramSession | None:
    try:
        session = AiramSession.objects.select_related(
            "taxonomy", "root_node", "last_node",
        ).prefetch_related("concept_weights").get(uuid=session_uuid)
    except AiramSession.DoesNotExist:
        return None
    if not _can_access(session, request):
        return None
    return session


def parse_json_body(request: HttpRequest) -> dict:
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}
