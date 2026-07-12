from __future__ import annotations

from ontologizar_app.models import Concept
from ontologizar_app.services.jsonld import concept_to_jsonld
from ontologizar_app.services.subject_curriculum import concept_classifications


def _relation_assertions(concept: Concept) -> list[dict]:
    assertions = []
    for rel in concept.outgoing_relations.select_related("target__dictionary__subject"):
        assertions.append({
            "@type": "core:RelationAssertion",
            "relationType": rel.relation_type,
            "source": {"@id": f"concept:{concept.uuid}", "name": concept.label},
            "target": {
                "@id": f"concept:{rel.target.uuid}",
                "name": rel.target.label,
                "subject": rel.target.dictionary.subject.name,
            },
        })
    for rel in concept.incoming_relations.select_related("source__dictionary__subject"):
        assertions.append({
            "@type": "core:RelationAssertion",
            "relationType": rel.relation_type,
            "direction": "incoming",
            "source": {
                "@id": f"concept:{rel.source.uuid}",
                "name": rel.source.label,
                "subject": rel.source.dictionary.subject.name,
            },
            "target": {"@id": f"concept:{concept.uuid}", "name": concept.label},
        })
    return assertions


def _taxonomy_assertions(concept: Concept) -> list[dict]:
    items = []
    for clf in concept_classifications(concept):
        items.append({
            "@type": "core:TaxonomyPlacement",
            "taxonomy": clf.taxonomy.name,
            "taxonomySlug": clf.taxonomy.slug,
            "breadcrumb": clf.breadcrumb,
            "taxonomyGroup": clf.taxonomy_group_label or "",
        })
    return items


def concept_graph_jsonld(concept: Concept, *, base_url: str = "") -> dict:
    """Grafo JSON-LD de un concepto: clase, propiedades y relaciones."""
    ns = "https://core.radiomicelio/ns/"
    node = concept_to_jsonld(concept)
    node["@id"] = f"concept:{concept.uuid}"
    node["@type"] = ["DefinedTerm", "core:OntologyClass"]
    node["core:entityKind"] = "class"
    if base_url:
        node["url"] = f"{base_url.rstrip('/')}/biblioteca/temas/{concept.uuid}/"

    props = node.pop("additionalProperty", [])
    property_nodes = []
    for prop in props:
        property_nodes.append({
            "@id": f"property:{concept.uuid}:{prop['name']}",
            "@type": ["PropertyValue", "core:OntologyProperty"],
            "core:entityKind": "property",
            "name": prop["name"],
            "value": prop["value"],
            "core:ofConcept": {"@id": f"concept:{concept.uuid}"},
        })

    relations = _relation_assertions(concept)
    placements = _taxonomy_assertions(concept)

    graph = [node, *property_nodes]
    if relations:
        for i, rel in enumerate(relations):
            rel["@id"] = f"rel:{concept.uuid}:{i}"
            graph.append(rel)
        node["core:relations"] = [{"@id": rel["@id"]} for rel in relations]
    if placements:
        node["core:taxonomyPlacements"] = placements

    return {
        "@context": {
            "@vocab": "https://schema.org/",
            "core": ns,
            "DefinedTerm": "https://schema.org/DefinedTerm",
            "PropertyValue": "https://schema.org/PropertyValue",
            "core:OntologyClass": f"{ns}OntologyClass",
            "core:OntologyProperty": f"{ns}OntologyProperty",
            "core:RelationAssertion": f"{ns}RelationAssertion",
            "core:TaxonomyPlacement": f"{ns}TaxonomyPlacement",
            "core:entityKind": f"{ns}entityKind",
            "core:ofConcept": f"{ns}ofConcept",
            "core:relations": f"{ns}relations",
            "core:relationType": f"{ns}relationType",
            "core:taxonomyPlacements": f"{ns}taxonomyPlacements",
            "core:taxonomyGroup": f"{ns}taxonomyGroup",
        },
        "@graph": graph,
    }
