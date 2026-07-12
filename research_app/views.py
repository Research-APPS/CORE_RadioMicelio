from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify

from ontologizar_app.models import Concept
from research_app.capability_registry import (
    capabilities_grouped_by_family,
    get_competency,
    homepage_capability_groups,
    is_digital_capability,
)
from research_app.models import ProyectoInvestigacion, ScientificActivity, ScientificResult
from research_app.project_hub import get_project_digital_profile
from research_app.project_ontology import build_digital_profile_jsonld, build_project_ontology_graph

RESULT_TYPE_CHOICES = [
    ("jsonld", "JSON-LD"),
    ("report", "Informe"),
    ("geojson", "GeoJSON"),
    ("pdf", "PDF"),
    ("web", "Página web"),
    ("dataset", "Dataset"),
    ("other", "Otro"),
]


def _activity_context(activity=None, proyectos=None):
    selected = set(activity.get_capability_slugs()) if activity else set()
    selected_notebooks = set(activity.get_notebook_uuids()) if activity else set()
    groups = homepage_capability_groups()
    capability_families = capabilities_grouped_by_family("digital")
    results_by_slug = {}
    if activity:
        for result in activity.results.all():
            results_by_slug.setdefault(result.capability_slug, []).append(result)
    for caps in groups.values():
        for cap in caps:
            cap["selected"] = cap["slug"] in selected
    for family in capability_families:
        for cap in family["actions"]:
            cap["selected"] = cap["slug"] in selected
            cap["results"] = results_by_slug.get(cap["slug"], [])
    notebook_options = proyectos or ProyectoInvestigacion.objects.filter(activo=True).order_by("titulo")
    for project in notebook_options:
        project.notebook_selected = str(project.uuid) in selected_notebooks
    return {
        "capability_groups": groups,
        "capability_families": capability_families,
        "selected_capability_slugs": selected,
        "notebook_options": notebook_options,
        "status_choices": ScientificActivity.STATUS_CHOICES,
        "result_type_choices": RESULT_TYPE_CHOICES,
    }


def _save_activity_capabilities(activity, request):
    slugs = request.POST.getlist("capability_slugs")
    if not activity.set_capabilities(slugs):
        messages.error(request, "Selecciona al menos una funcionalidad o competencia.")
        return False
    return True


def _save_activity_notebooks(activity, request):
    uuids = request.POST.getlist("notebook_uuids")
    projects = list(ProyectoInvestigacion.objects.filter(uuid__in=uuids, activo=True))
    if not activity.set_notebooks(projects):
        messages.error(request, "Selecciona al menos un cuaderno.")
        return False
    return True


def proyecto_list(request):
    proyectos = ProyectoInvestigacion.objects.filter(activo=True, publico=True)
    return render(request, "research/proyecto_list.html", {"proyectos": proyectos})


def activity_list(request):
    activities = (
        ScientificActivity.objects.prefetch_related(
            "results", "capability_links", "notebook_links__project",
        )
        .order_by("title")
    )
    for act in activities:
        act.capability_labels_display = act.get_capability_labels()
        act.notebooks_display = list(act.get_notebooks())
    ctx = _activity_context()
    ctx.update({"activities": activities})
    return render(request, "research/activity_list.html", ctx)


@login_required
def activity_create(request):
    proyectos = ProyectoInvestigacion.objects.filter(activo=True).order_by("titulo")
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        if not title:
            messages.error(request, "El título es obligatorio.")
        else:
            base_slug = slugify(title)[:70] or "actividad"
            slug = base_slug
            n = 1
            while ScientificActivity.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{n}"
                n += 1
            activity = ScientificActivity.objects.create(
                title=title,
                slug=slug,
                capability_slug="",
                description=request.POST.get("description", "").strip(),
                status=request.POST.get("status", "active"),
            )
            ok = _save_activity_notebooks(activity, request) and _save_activity_capabilities(activity, request)
            if ok:
                messages.success(request, f"Investigación «{activity.title}» creada.")
                return redirect("research:activity_edit", uuid=activity.uuid)
    ctx = _activity_context(proyectos=proyectos)
    ctx.update({"activity": None})
    return render(request, "research/activity_edit.html", ctx)


@login_required
def activity_edit(request, uuid):
    proyectos = ProyectoInvestigacion.objects.filter(activo=True).order_by("titulo")
    activity = get_object_or_404(
        ScientificActivity.objects.prefetch_related(
            "results", "capability_links", "notebook_links__project",
        ),
        uuid=uuid,
    )
    if request.method == "POST":
        action = request.POST.get("action", "save_activity")
        if action == "save_activity":
            title = request.POST.get("title", "").strip()
            if not title:
                messages.error(request, "El título es obligatorio.")
            else:
                activity.title = title
                activity.description = request.POST.get("description", "").strip()
                activity.status = request.POST.get("status", activity.status)
                activity.save()
                if _save_activity_notebooks(activity, request) and _save_activity_capabilities(activity, request):
                    messages.success(request, "Investigación actualizada.")
        elif action == "add_result":
            capability_slug = request.POST.get("capability_slug", "").strip()
            title = request.POST.get("result_title", "").strip()
            result_type = request.POST.get("result_type", "").strip()
            if not is_digital_capability(capability_slug):
                messages.error(request, "El resultado debe vincularse a una funcionalidad.")
            elif capability_slug not in activity.get_capability_slugs():
                messages.error(request, "Marca y guarda la funcionalidad antes de añadir resultados.")
            elif not title or not result_type:
                messages.error(request, "Título y tipo del resultado son obligatorios.")
            else:
                ScientificResult.objects.create(
                    activity=activity,
                    capability_slug=capability_slug,
                    title=title,
                    result_type=result_type,
                    publish_url=request.POST.get("publish_url", "").strip(),
                    artifact_url=request.POST.get("artifact_url", "").strip(),
                    published_at=timezone.now(),
                )
                messages.success(request, "Resultado añadido.")
        elif action == "delete_result":
            result = activity.results.filter(uuid=request.POST.get("result_uuid")).first()
            if result:
                result.delete()
                messages.success(request, "Resultado eliminado.")
        return redirect("research:activity_edit", uuid=activity.uuid)

    ctx = _activity_context(activity, proyectos=proyectos)
    ctx.update({"activity": activity})
    return render(request, "research/activity_edit.html", ctx)


def proyecto_detail(request, uuid):
    proyecto = get_object_or_404(ProyectoInvestigacion, uuid=uuid, activo=True)
    profile = get_project_digital_profile(uuid)
    if profile:
        for act in profile.curriculum.get("activities", []):
            act["capability_labels"] = act.get("capability_labels") or []
            if not act["capability_labels"] and act.get("capability"):
                cap = get_competency(act["capability"])
                act["capability_labels"] = [cap["label"] if cap else act["capability"]]
    return render(
        request,
        "research/proyecto_detail.html",
        {"proyecto": proyecto, "profile": profile},
    )


def digital_profile_json(request, uuid):
    profile = get_project_digital_profile(uuid)
    if not profile:
        return JsonResponse({"error": "not found"}, status=404)
    if request.GET.get("format") == "jsonld":
        return JsonResponse(build_digital_profile_jsonld(profile), json_dumps_params={"ensure_ascii": False})
    return JsonResponse(profile.to_dict())


def proyecto_ontology(request, uuid):
    proyecto = get_object_or_404(ProyectoInvestigacion, uuid=uuid, activo=True)
    graph = build_project_ontology_graph(uuid)
    return render(
        request,
        "research/proyecto_ontology.html",
        {"proyecto": proyecto, "graph": graph},
    )


def proyecto_ontology_json(request, uuid):
    graph = build_project_ontology_graph(uuid)
    if not graph:
        return JsonResponse({"error": "not found"}, status=404)
    return JsonResponse(graph, json_dumps_params={"ensure_ascii": False})


def marker_jsonld(request, uuid, concept_uuid):
    proyecto = get_object_or_404(ProyectoInvestigacion, uuid=uuid, activo=True)
    concept = get_object_or_404(Concept, uuid=concept_uuid)
    from ontologizar_app.services.concept_graph import concept_graph_jsonld
    base = request.build_absolute_uri("/").rstrip("/")
    payload = concept_graph_jsonld(concept, base_url=base)
    marker = proyecto.markers.filter(concept_uuid=concept.uuid).first()
    if marker:
        payload["@graph"].insert(0, {
            "@id": f"marker:{proyecto.uuid}:{concept.uuid}",
            "@type": "core:LearningMarker",
            "name": marker.concept_label,
            "core:status": marker.status,
            "core:note": marker.note or "",
            "core:cites": {"@id": f"concept:{concept.uuid}"},
        })
    return JsonResponse(payload, json_dumps_params={"ensure_ascii": False})
