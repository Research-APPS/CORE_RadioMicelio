import json
from django.conf import settings

from ontologizar_app.models import Concept, Taxonomy, TaxonomyNode


def concept_to_jsonld(concept: Concept) -> dict:
    props = [
        {"@type": "PropertyValue", "name": p.key, "value": p.value}
        for p in concept.properties.all()
    ]
    definition = concept.definitions.filter(is_active=True, kind="definition").first()
    data = {
        "@context": "https://schema.org/",
        "@type": "DefinedTerm",
        "@id": str(concept.uuid),
        "name": concept.label,
        "inDefinedTermSet": concept.dictionary.name,
        "isPartOf": {
            "@type": "DefinedTermSet",
            "name": concept.dictionary.subject.name,
        },
    }
    if definition:
        data["description"] = definition.text
    if props:
        data["additionalProperty"] = props
    classifications = [t.name for t in concept.taxonomies()]
    if classifications:
        data["classification"] = classifications
    return data


def taxonomy_to_jsonld(taxonomy: Taxonomy) -> dict:
    nodes = taxonomy.nodes.filter(concept__isnull=False).select_related("concept")
    return {
        "@context": "https://www.w3.org/2004/02/skos/core",
        "@type": "ConceptScheme",
        "@id": str(taxonomy.uuid),
        "prefLabel": taxonomy.name,
        "definition": taxonomy.description,
        "hasTopConcept": [
            {"@id": str(n.concept.uuid), "prefLabel": n.concept.label}
            for n in nodes.filter(level=0)
        ],
    }


def topic_page_jsonld(concept: Concept, request) -> str:
    data = concept_to_jsonld(concept)
    data["@type"] = ["DefinedTerm", "Article"]
    data["url"] = request.build_absolute_uri(f"/biblioteca/temas/{concept.uuid}/")
  # breadcrumb
    crumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Biblioteca", "item": request.build_absolute_uri("/biblioteca/")},
            {"@type": "ListItem", "position": 2, "name": concept.dictionary.subject.name},
            {"@type": "ListItem", "position": 3, "name": concept.label},
        ],
    }
    return json.dumps([data, crumbs], ensure_ascii=False)
