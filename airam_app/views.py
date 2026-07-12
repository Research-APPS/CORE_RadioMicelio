from __future__ import annotations

import json

from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods

from airam_app.graph import build_graph
from airam_app.models import AiramSession
from airam_app.services.sessions import (
    bookmark_session,
    create_session,
    create_workspace,
    get_or_create_workspace,
    get_session_for_request,
    parse_json_body,
    patch_session,
    session_to_dict,
)
from airam_app.services.rdf_export import (
    document_from_node_uuids,
    document_from_session,
    document_to_jsonld,
    document_to_turtle,
    session_to_jsonld,
    session_to_turtle,
)
from ontologizar_app.models import TaxonomyNode


def graph_json(request):
    return JsonResponse(build_graph())


@require_http_methods(["POST"])
def session_create(request):
    data = parse_json_body(request)
    taxonomy_slug = data.get("taxonomy_slug", "").strip()
    node_uuid = data.get("node_uuid", "").strip()
    node_uuids = data.get("node_uuids")
    granularity = data.get("granularity", "normal").strip()

    if not taxonomy_slug:
        return JsonResponse({"error": "taxonomy_slug es obligatorio"}, status=400)

    uuids: list[str] = []
    if isinstance(node_uuids, list):
        uuids = [str(u).strip() for u in node_uuids if str(u).strip()]
    if not uuids and node_uuid:
        uuids = [node_uuid]
    if not uuids:
        return JsonResponse({"error": "node_uuid o node_uuids son obligatorios"}, status=400)

    for uuid in uuids:
        try:
            TaxonomyNode.objects.get(uuid=uuid, taxonomy__slug=taxonomy_slug)
        except TaxonomyNode.DoesNotExist:
            return JsonResponse({"error": f"Nodo no encontrado: {uuid}"}, status=404)

    try:
        session = create_session(
            request,
            taxonomy_slug=taxonomy_slug,
            node_uuids=uuids,
            granularity=granularity,
        )
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(session_to_dict(session), status=201)


@require_http_methods(["GET", "POST"])
def workspace_current(request):
    if request.method == "GET":
        from airam_app.services.sessions import _session_key
        sk = _session_key(request)
        session = AiramSession.objects.filter(
            session_kind="workspace", session_key=sk, is_bookmarked=False,
        ).order_by("-updated_at").prefetch_related("concept_weights").first()
        if not session:
            return JsonResponse({"workspace": None})
        return JsonResponse({"workspace": session_to_dict(session)})

    data = parse_json_body(request)
    force_new = bool(data.get("force_new"))
    if force_new:
        session = create_workspace(request, project_uuid=str(data.get("project_uuid", "")).strip())
    else:
        session = get_or_create_workspace(request)
    return JsonResponse(session_to_dict(session), status=201)


@require_http_methods(["GET"])
def workspace_projects(request):
    from research_app.models import ProyectoInvestigacion
    rows = ProyectoInvestigacion.objects.filter(activo=True, publico=True).order_by("titulo")[:30]
    return JsonResponse({
        "projects": [
            {"uuid": str(p.uuid), "title": p.acron or p.titulo}
            for p in rows
        ],
    })


@require_http_methods(["GET", "PATCH"])
def workspace_detail(request, uuid):
    session = get_session_for_request(request, str(uuid))
    if not session or not session.is_workspace:
        return JsonResponse({"error": "Workspace no encontrado"}, status=404)
    if request.method == "GET":
        return JsonResponse(session_to_dict(session))
    payload = parse_json_body(request)
    if not payload.get("action"):
        return JsonResponse({"error": "action es obligatorio"}, status=400)
    try:
        session = patch_session(session, payload)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(session_to_dict(session))


@require_http_methods(["GET", "PATCH"])
def session_detail(request, uuid):
    session = get_session_for_request(request, str(uuid))
    if not session or session.is_workspace:
        return JsonResponse({"error": "Sesión no encontrada"}, status=404)
    if request.method == "GET":
        return JsonResponse(session_to_dict(session))
    payload = parse_json_body(request)
    if not payload.get("action"):
        return JsonResponse({"error": "action es obligatorio"}, status=400)
    session = patch_session(session, payload)
    return JsonResponse(session_to_dict(session))


@require_http_methods(["POST"])
def session_bookmark(request, uuid):
    session = get_session_for_request(request, str(uuid))
    if not session:
        return JsonResponse({"error": "Sesión no encontrada"}, status=404)
    session = bookmark_session(session)
    return JsonResponse(session_to_dict(session))


def _rdf_response(payload: str, *, filename: str, content_type: str) -> HttpResponse:
    response = HttpResponse(payload, content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@require_http_methods(["GET"])
def session_rdf(request, uuid):
    session = get_session_for_request(request, str(uuid))
    if not session:
        return JsonResponse({"error": "Sesión no encontrada"}, status=404)

    fmt = request.GET.get("format", "jsonld").strip().lower()
    if session.is_workspace or not session.taxonomy_id:
        return JsonResponse({"error": "RDF no disponible para workspace"}, status=400)
    slug = session.taxonomy.slug
    if fmt == "turtle":
        body = session_to_turtle(session)
        return _rdf_response(body, filename=f"temario-{slug}-{uuid}.ttl", content_type="text/turtle; charset=utf-8")
    if fmt == "json":
        body = json.dumps(session_to_jsonld(session), ensure_ascii=False, indent=2)
        return _rdf_response(
            body,
            filename=f"temario-{slug}-{uuid}.jsonld",
            content_type="application/ld+json; charset=utf-8",
        )
    return JsonResponse(session_to_jsonld(session), json_dumps_params={"ensure_ascii": False})


@require_http_methods(["POST"])
def temario_rdf_export(request):
    """Exporta RDF de un temario preparado (cola o lista de clases) sin sesión activa."""
    data = parse_json_body(request)
    session_uuid = data.get("session_uuid", "").strip()
    fmt = str(data.get("format", "jsonld")).strip().lower()

    try:
        if session_uuid:
            session = get_session_for_request(request, session_uuid)
            if not session:
                return JsonResponse({"error": "Sesión no encontrada"}, status=404)
            doc = document_from_session(session)
            slug = session.taxonomy.slug
            file_id = str(session.uuid)
        else:
            taxonomy_slug = data.get("taxonomy_slug", "").strip()
            node_uuids = data.get("node_uuids")
            if not taxonomy_slug or not isinstance(node_uuids, list) or not node_uuids:
                return JsonResponse(
                    {"error": "taxonomy_slug y node_uuids son obligatorios (o session_uuid)"},
                    status=400,
                )
            uuids = [str(u).strip() for u in node_uuids if str(u).strip()]
            doc = document_from_node_uuids(
                taxonomy_slug,
                uuids,
                granularity=str(data.get("granularity", "normal")),
                title=str(data.get("title", "")).strip() or None,
            )
            slug = taxonomy_slug
            file_id = "preview"
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except TaxonomyNode.DoesNotExist:
        return JsonResponse({"error": "Nodo no encontrado"}, status=404)

    if fmt == "turtle":
        body = document_to_turtle(doc)
        return _rdf_response(body, filename=f"temario-{slug}-{file_id}.ttl", content_type="text/turtle; charset=utf-8")
    payload = document_to_jsonld(doc)
    if fmt == "json":
        body = json.dumps(payload, ensure_ascii=False, indent=2)
        return _rdf_response(
            body,
            filename=f"temario-{slug}-{file_id}.jsonld",
            content_type="application/ld+json; charset=utf-8",
        )
    return JsonResponse(payload, json_dumps_params={"ensure_ascii": False})
