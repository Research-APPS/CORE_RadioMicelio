from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from leximus_app.models import Taxonomy, TaxonomyNode
from leximus_app.services.jsonld import taxonomy_to_jsonld


def taxonomy_detail(request, slug):
    taxonomy = get_object_or_404(Taxonomy, slug=slug, is_active=True)
    nodes = TaxonomyNode.objects.filter(taxonomy=taxonomy).order_by("tree_id", "lft")
    return render(request, "leximus/taxonomy_detail.html", {"taxonomy": taxonomy, "nodes": nodes})


def taxonomy_api(request, slug):
    taxonomy = get_object_or_404(Taxonomy, slug=slug, is_active=True)
    return JsonResponse({
        "slug": taxonomy.slug,
        "name": taxonomy.name,
        "description": taxonomy.description,
        "node_count": taxonomy.nodes.count(),
    })


def taxonomy_jsonld(request, slug):
    taxonomy = get_object_or_404(Taxonomy, slug=slug, is_active=True)
    return JsonResponse(taxonomy_to_jsonld(taxonomy))
