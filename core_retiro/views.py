from django.conf import settings
from django.shortcuts import render

from knowledge_app.models import Concept, Dictionary, Subject, Taxonomy
from logs_app.platforms import list_platforms
from research_app.capability_registry import PUBLIC_CAPABILITIES, get_public_capability_by_slug
from research_app.models import ProyectoInvestigacion


def _enabled(internal_slug: str) -> bool:
    mapping = {
        "logs": "logs",
        "ontology": "knowledge",
        "dataset": "knowledge",
        "geodata": "knowledge",
        "publish": "research",
        "analysis": "research",
        "visualize": "research",
        "preserve": "research",
    }
    mod = mapping.get(internal_slug)
    if not mod:
        return False
    return mod in getattr(settings, "CORE_ENABLED_MODULES", [])


def home(request):
    capabilities = []
    for cap in PUBLIC_CAPABILITIES:
        active = cap["mvp_active"] and _enabled(cap["slug"])
        capabilities.append({
            **cap,
            "enabled": active,
            "url": f"/capacidades/{cap['public_slug']}/",
            "coming_soon": not cap["mvp_active"],
        })
    return render(request, "core/home.html", {
        "institute": getattr(settings, "CORE_INSTITUTE_NAME", "CORE Radio Micelio"),
        "capabilities": capabilities,
        "project_count": ProyectoInvestigacion.objects.filter(activo=True, publico=True).count(),
    })


def capability_detail(request, public_slug):
    cap = get_public_capability_by_slug(public_slug)
    if not cap:
        return render(request, "core/not_found.html", status=404)

    slug = cap["slug"]
    implemented = cap["mvp_active"] and _enabled(slug)
    ctx = {
        "capability": cap,
        "implemented": implemented,
        "implementation": None,
        "results": [],
        "platforms": [],
        "subjects": [],
    }

    if slug == "logs" and implemented:
        ctx["implementation"] = {"name": "logs", "label": "Sistema de medición", "status": "Activo"}
        ctx["platforms"] = list_platforms()
    elif slug == "ontology" and implemented:
        ctx["implementation"] = {"name": "knowledge", "label": "Biblioteca semántica", "status": "Activo"}
        for tax in Taxonomy.objects.filter(is_active=True).order_by("name"):
            ctx["results"].append({
                "title": tax.name, "slug": tax.slug,
                "url": f"/capacidades/ontologizar/taxonomias/{tax.slug}/",
                "jsonld_url": f"/knowledge/api/taxonomies/{tax.slug}/jsonld/",
            })
    elif slug == "catalogar" and implemented:
        ctx["implementation"] = {"name": "knowledge", "label": "Biblioteca semántica", "status": "Activo"}
        for dic in Dictionary.objects.filter(is_active=True).select_related("subject").order_by("subject__name", "name"):
            ctx["results"].append({
                "title": dic.name,
                "meta": dic.subject.name,
                "url": f"/capacidades/catalogar/",
            })
    elif slug == "geolocalizar" and implemented:
        ctx["subjects"] = Subject.objects.filter(slug="geografia", is_active=True)
        ctx["implementation"] = {"name": "knowledge", "label": "Biblioteca semántica", "status": "Activo"}
    elif slug == "publicar" and implemented:
        ctx["implementation"] = {"name": "core", "label": "CORE API", "status": "Activo"}
        for tax in Taxonomy.objects.filter(is_active=True):
            ctx["results"].append({
                "title": tax.name, "kind": "Ontología",
                "url": f"/knowledge/api/taxonomies/{tax.slug}/jsonld/",
            })

    return render(request, "core/capability_detail.html", ctx)


def ontology_taxonomy(request, slug):
    cap = get_public_capability_by_slug("ontologizar")
    taxonomy = Taxonomy.objects.filter(slug=slug, is_active=True).first()
    if not cap or not taxonomy:
        return render(request, "core/not_found.html", status=404)
    concepts = TaxonomyNode.objects.filter(taxonomy=taxonomy).order_by("tree_id", "lft")
    return render(request, "core/ontology_taxonomy.html", {
        "capability": cap, "taxonomy": taxonomy, "nodes": concepts,
        "implementation": {"name": "knowledge", "label": "Biblioteca semántica"},
    })


def results_index(request):
    results = []
    if "knowledge" in getattr(settings, "CORE_ENABLED_MODULES", []):
        for tax in Taxonomy.objects.filter(is_active=True).order_by("name"):
            results.append({
                "title": tax.name, "capability": "Ontologizar", "type": "Taxonomía",
                "url": f"/capacidades/ontologizar/taxonomias/{tax.slug}/",
                "publish_url": f"/knowledge/api/taxonomies/{tax.slug}/jsonld/",
            })
    if "logs" in getattr(settings, "CORE_ENABLED_MODULES", []):
        for p in list_platforms():
            results.append({
                "title": p.label, "capability": "Medir", "type": "Informe de uso",
                "url": f"/logs/{p.slug}/", "publish_url": f"/logs/api/platforms/{p.slug}/segments/",
            })
    return render(request, "core/results.html", {"results": results})
