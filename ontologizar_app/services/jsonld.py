import json
from django.utils import timezone

from ontologizar_app.models import Concept, Taxonomy, TaxonomyNode
from ontologizar_app.services.citations import (
    citations_is_based_on,
    citations_to_jsonld,
    concept_citations,
)

CORE_ORGANIZATION = {
    "@type": "Organization",
    "name": "CORE Radio Micelio",
}


def _concept_date_modified(concept: Concept) -> str:
    timestamps = [
        d.created_at for d in concept.definitions.filter(is_active=True) if d.created_at
    ]
    if timestamps:
        return max(timestamps).date().isoformat()
    return timezone.now().date().isoformat()


def concept_to_jsonld(concept: Concept) -> dict:
    props = [
        {"@type": "PropertyValue", "name": p.key, "value": p.value}
        for p in concept.properties.all()
    ]
    definition = concept.definitions.filter(is_active=True, kind="definition").first()
    citations = concept_citations(concept)
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
        "author": CORE_ORGANIZATION,
        "publisher": CORE_ORGANIZATION,
        "dateModified": _concept_date_modified(concept),
    }
    if definition:
        data["description"] = definition.text
    if props:
        data["additionalProperty"] = props
    if citations:
        data["citation"] = citations_to_jsonld(citations)
        is_based_on = citations_is_based_on(citations)
        if is_based_on:
            data["isBasedOn"] = is_based_on
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
