from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from ontologizar_app.models import Concept, Taxonomy
from ontologizar_app.services.jsonld import concept_to_jsonld, taxonomy_to_jsonld


def concept_jsonld(request, uuid):
    concept = get_object_or_404(Concept, uuid=uuid)
    return JsonResponse(concept_to_jsonld(concept))


def taxonomy_jsonld(request, slug):
    taxonomy = get_object_or_404(Taxonomy, slug=slug, is_active=True)
    return JsonResponse(taxonomy_to_jsonld(taxonomy))
