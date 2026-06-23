from django.shortcuts import get_object_or_404, render

from knowledge_app.models import Concept, Dictionary, Subject, Taxonomy, TaxonomyNode
from knowledge_app.services.jsonld import topic_page_jsonld
from knowledge_app.services.topic_body import render_topic_body
from research_app.models import LearningMarker, ScientificResult


def biblioteca_index(request):
    return render(request, "cms/public/index.html", {
        "subjects": Subject.objects.filter(is_active=True),
        "taxonomies": Taxonomy.objects.filter(is_active=True).order_by("name")[:6],
    })


def subject_detail(request, slug):
    subject = get_object_or_404(Subject, slug=slug, is_active=True)
    return render(request, "cms/public/subject.html", {
        "subject": subject,
        "materials": subject.materials.all(),
        "dictionaries": subject.dictionaries.filter(is_active=True),
    })


def dictionary_detail(request, subject_slug, dict_slug):
    dictionary = get_object_or_404(Dictionary, subject__slug=subject_slug, slug=dict_slug, is_active=True)
    return render(request, "cms/public/dictionary.html", {
        "dictionary": dictionary,
        "concepts": dictionary.concepts.all(),
    })


def taxonomy_list(request):
    return render(request, "cms/public/taxonomy_list.html", {
        "taxonomies": Taxonomy.objects.filter(is_active=True).order_by("name"),
    })


def taxonomy_detail(request, slug):
    taxonomy = get_object_or_404(Taxonomy, slug=slug, is_active=True)
    roots = TaxonomyNode.objects.filter(taxonomy=taxonomy, parent=None)
    return render(request, "cms/public/taxonomy.html", {"taxonomy": taxonomy, "roots": roots})


def topic_detail(request, uuid):
    concept = get_object_or_404(Concept, uuid=uuid)
    markers = LearningMarker.objects.filter(concept_uuid=concept.uuid).select_related("project")
    return render(request, "cms/public/topic.html", {
        "concept": concept,
        "body_html": render_topic_body(concept),
        "taxonomies": concept.taxonomies(),
        "markers": markers,
        "jsonld": topic_page_jsonld(concept, request),
    })
