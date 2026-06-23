from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from research_app.models import ProyectoInvestigacion
from research_app.project_hub import build_digital_profile_jsonld, get_project_digital_profile


def proyecto_list(request):
    proyectos = ProyectoInvestigacion.objects.filter(activo=True, publico=True)
    return render(request, "research/proyecto_list.html", {"proyectos": proyectos})


def proyecto_detail(request, uuid):
    proyecto = get_object_or_404(ProyectoInvestigacion, uuid=uuid, activo=True)
    profile = get_project_digital_profile(uuid)
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
        return JsonResponse(build_digital_profile_jsonld(profile))
    return JsonResponse(profile.to_dict())
