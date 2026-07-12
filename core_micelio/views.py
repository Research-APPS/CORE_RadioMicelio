from django.conf import settings
from django.shortcuts import render
from django.urls import reverse

from ontologizar_app.models import Concept, Dictionary, Subject, Taxonomy, TaxonomyNode
from ontologizar_app.services.attributed_relations import concept_interpretations
from logs_app.platforms import list_platforms
from research_app.capability_registry import (
    ARCHETYPE_FIGURE_LABELS,
    capabilities_by_category,
    capabilities_grouped_by_family,
    get_public_capability_by_slug,
    homepage_capability_groups,
    is_capability_module_enabled,
)
from research_app.models import ProyectoInvestigacion


def _enabled(internal_slug: str) -> bool:
    return is_capability_module_enabled(internal_slug)


def _capability_entry(cap: dict) -> dict:
    from django.urls import reverse

    return {
        **cap,
        "enabled": cap["mvp_active"] and _enabled(cap["slug"]),
        "url": reverse("capability_detail", kwargs={"public_slug": cap["public_slug"]}),
        "coming_soon": not cap["mvp_active"],
        "definition": cap.get("definition", ""),
    }


def _homepage_capability_families() -> list[dict]:
    families = capabilities_grouped_by_family("digital")
    specs_by_slug = {c["slug"]: c for c in capabilities_by_category("digital")}
    for family in families:
        family["actions"] = [
            _capability_entry(specs_by_slug[action["slug"]])
            for action in family["actions"]
        ]
    return families


def _narrativa_meta_dictionary():
    return Dictionary.objects.filter(
        subject__slug="narrativa", slug="ontonarrativa", is_active=True,
    ).select_related("subject").first()


def _quijote_dictionary():
    return Dictionary.objects.filter(
        subject__slug="lengua", slug="quijote", is_active=True,
    ).select_related("subject").first()


def home(request):
    capability_families = _homepage_capability_families()
    interpretive_capabilities = [
        _capability_entry(cap) for cap in capabilities_by_category("interpretive")
    ]
    return render(request, "core/home.html", {
        "institute": getattr(settings, "CORE_INSTITUTE_NAME", "CORE Radio Micelio"),
        "capability_families": capability_families,
        "interpretive_capabilities": interpretive_capabilities,
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
        "figures": [],
        "interpretations": [],
        "biblioteca_links": [],
    }

    if slug == "logs" and implemented:
        ctx["implementation"] = {"name": "logs", "label": "Sistema de medición", "status": "Activo"}
        ctx["platforms"] = list_platforms()
    elif slug == "ontology" and implemented:
        ctx["implementation"] = {"name": "ontologizar", "label": "Biblioteca semántica", "status": "Activo"}
        for tax in Taxonomy.objects.filter(is_active=True).order_by("name"):
            ctx["results"].append({
                "title": tax.name, "slug": tax.slug,
                "url": reverse("ontology_taxonomy", kwargs={"slug": tax.slug}),
                "jsonld_url": f"/ontologizar/api/taxonomies/{tax.slug}/jsonld/",
            })
    elif slug == "dataset" and implemented:
        ctx["implementation"] = {"name": "ontologizar", "label": "Biblioteca semántica", "status": "Activo"}
        for dic in Dictionary.objects.filter(is_active=True).select_related("subject").order_by("subject__name", "name"):
            ctx["results"].append({
                "title": dic.name,
                "meta": dic.subject.name,
                "url": reverse("capability_detail", kwargs={"public_slug": "catalogar"}),
            })
    elif slug == "geodata" and implemented:
        ctx["subjects"] = Subject.objects.filter(slug="geografia", is_active=True)
        ctx["implementation"] = {"name": "ontologizar", "label": "Biblioteca semántica", "status": "Activo"}
    elif slug == "publicar" and implemented:
        ctx["implementation"] = {"name": "core", "label": "CORE API", "status": "Activo"}
        for tax in Taxonomy.objects.filter(is_active=True):
            ctx["results"].append({
                "title": tax.name, "kind": "Ontología",
                "url": f"/ontologizar/api/taxonomies/{tax.slug}/jsonld/",
            })
    elif slug == "narrate" and implemented:
        ctx["implementation"] = {"name": "ontologizar", "label": "Biblioteca semántica", "status": "Activo"}
        meta = _narrativa_meta_dictionary()
        if meta:
            ctx["biblioteca_links"] = [
                {
                    "title": meta.subject.name,
                    "description": "Asignatura y materiales de estudio narrativo",
                    "url": reverse("biblioteca:subject", kwargs={"slug": meta.subject.slug}),
                },
                {
                    "title": meta.name,
                    "description": "Meta-vocabulario #ontoNarrativa",
                    "url": reverse(
                        "biblioteca:dictionary",
                        kwargs={"subject_slug": meta.subject.slug, "dict_slug": meta.slug},
                    ),
                },
            ]
            taxonomies = Taxonomy.objects.filter(
                slug__in=(
                    "narrativa", "narrativa-arquetipico",
                    "narrativa-tematico", "narrativa-simbolico",
                ),
                is_active=True,
            ).order_by("name")
            for tax in taxonomies:
                ctx["biblioteca_links"].append({
                    "title": tax.name,
                    "description": tax.description or "Taxonomía #ontoNarrativa",
                    "url": reverse("biblioteca:taxonomy", kwargs={"slug": tax.slug}),
                })
    elif slug == "archetype" and implemented:
        ctx["implementation"] = {"name": "ontologizar", "label": "Biblioteca semántica", "status": "Activo"}
        meta = _narrativa_meta_dictionary()
        if meta:
            for concept in meta.concepts.filter(label__in=ARCHETYPE_FIGURE_LABELS).order_by("label"):
                ctx["figures"].append({
                    "title": concept.label,
                    "url": reverse("biblioteca:topic", kwargs={"uuid": concept.uuid}),
                })
            tax = Taxonomy.objects.filter(slug="narrativa-arquetipico", is_active=True).first()
            if tax:
                ctx["biblioteca_links"] = [{
                    "title": tax.name,
                    "description": "Explorar figuras narrativas del meta-vocabulario",
                    "url": reverse("biblioteca:taxonomy", kwargs={"slug": tax.slug}),
                }]
    elif slug == "interpret" and implemented:
        ctx["implementation"] = {"name": "ontologizar", "label": "Biblioteca semántica", "status": "Activo"}
        quijote = _quijote_dictionary()
        if quijote:
            ctx["biblioteca_links"] = [{
                "title": quijote.name,
                "description": f"Corpus documental — {quijote.subject.name}",
                "url": reverse(
                    "biblioteca:dictionary",
                    kwargs={"subject_slug": quijote.subject.slug, "dict_slug": quijote.slug},
                ),
            }]
            for concept in quijote.concepts.order_by("label"):
                readings = concept_interpretations(concept)
                if readings:
                    ctx["interpretations"].append({
                        "concept": concept.label,
                        "url": reverse("biblioteca:topic", kwargs={"uuid": concept.uuid}),
                        "readings": [
                            {
                                "target": r.relation.target.label,
                                "framework": r.attribution.framework or "",
                                "relation_type": r.relation.relation_type,
                            }
                            for r in readings
                        ],
                    })
                else:
                    ctx["results"].append({
                        "title": concept.label,
                        "url": reverse("biblioteca:topic", kwargs={"uuid": concept.uuid}),
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
        "implementation": {"name": "ontologizar", "label": "Biblioteca semántica"},
    })


def results_index(request):
    results = []
    if "ontologizar" in getattr(settings, "CORE_ENABLED_MODULES", []):
        for tax in Taxonomy.objects.filter(is_active=True).order_by("name"):
            results.append({
                "title": tax.name, "capability": "Ontologizar", "type": "Taxonomía",
                "url": reverse("ontology_taxonomy", kwargs={"slug": tax.slug}),
                "publish_url": f"/ontologizar/api/taxonomies/{tax.slug}/jsonld/",
            })
    if "logs" in getattr(settings, "CORE_ENABLED_MODULES", []):
        for p in list_platforms():
            results.append({
                "title": p.label, "capability": "Medir", "type": "Informe de uso",
                "url": reverse("logs:platform_dashboard", kwargs={"platform_slug": p.slug}),
                "publish_url": f"/logs/api/platforms/{p.slug}/segments/",
            })
    return render(request, "core/results.html", {"results": results})
