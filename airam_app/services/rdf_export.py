from __future__ import annotations

import json
from dataclasses import dataclass, field

from django.conf import settings

from airam_app.models import AiramSession
from airam_app.services.temario import node_breadcrumb, subtree_nodes
from ontologizar_app.models import Concept, Taxonomy, TaxonomyNode
from ontologizar_app.services.concept_indicators import _is_ontology_property


@dataclass
class TopicRdf:
    concept_uuid: str
    label: str
    node_uuid: str
    breadcrumb: list[str]
    definition: str
    examples: list[str]
    properties: list[dict[str, str]]
    relations_out: list[dict[str, str]]
    relations_in: list[dict[str, str]]
    position: int


@dataclass
class ClassRdf:
    node_uuid: str
    label: str
    position: int
    topics: list[TopicRdf] = field(default_factory=list)


@dataclass
class TemarioRdfDocument:
    title: str
    taxonomy_slug: str
    taxonomy_name: str
    granularity: str
    session_uuid: str | None
    classes: list[ClassRdf]
    play_order: list[str]


def _site_base() -> str:
    return (getattr(settings, "SITE_URL", "") or "").rstrip("/")


def _ns() -> str:
    return getattr(settings, "CORE_JSONLD_NAMESPACE", "https://core.radiomicelio/ns/")


def _concept_topic(concept: Concept, node: TaxonomyNode, position: int) -> TopicRdf:
    dict_id = concept.dictionary_id
    definition = ""
    examples: list[str] = []
    for d in concept.definitions.filter(is_active=True):
        text = d.text.strip()
        if not text:
            continue
        if d.kind == "definition" and not definition:
            definition = text
        elif d.kind == "example":
            examples.append(text)

    properties = [
        {"key": p.key, "value": p.value.strip()}
        for p in concept.properties.all()
        if _is_ontology_property(p.key) and p.value.strip()
    ]

    relations_out = [
        {
            "target_uuid": str(r.target.uuid),
            "target_label": r.target.label,
            "type": r.relation_type,
        }
        for r in concept.outgoing_relations.all()
        if r.target.dictionary_id == dict_id
    ]
    relations_in = [
        {
            "source_uuid": str(r.source.uuid),
            "source_label": r.source.label,
            "type": r.relation_type,
        }
        for r in concept.incoming_relations.all()
        if r.source.dictionary_id == dict_id
    ]

    return TopicRdf(
        concept_uuid=str(concept.uuid),
        label=concept.label,
        node_uuid=str(node.uuid),
        breadcrumb=node_breadcrumb(node),
        definition=definition,
        examples=examples,
        properties=properties,
        relations_out=relations_out,
        relations_in=relations_in,
        position=position,
    )


def _class_roots(session_or_taxonomy, combined_uuids: list[str]) -> list[TaxonomyNode]:
    taxonomy = session_or_taxonomy if isinstance(session_or_taxonomy, Taxonomy) else session_or_taxonomy.taxonomy
    nodes_by_uuid = {
        str(n.uuid): n
        for n in TaxonomyNode.objects.filter(taxonomy=taxonomy, uuid__in=combined_uuids).select_related("concept")
    }
    return [nodes_by_uuid[u] for u in combined_uuids if u in nodes_by_uuid]


def build_temario_document(
    *,
    taxonomy: Taxonomy,
    combined_uuids: list[str],
    title: str,
    granularity: str = "normal",
    session_uuid: str | None = None,
) -> TemarioRdfDocument:
    roots = _class_roots(taxonomy, combined_uuids)
    play_order: list[str] = []
    classes: list[ClassRdf] = []
    global_position = 1

    for class_pos, root in enumerate(roots, start=1):
        class_topics: list[TopicRdf] = []
        for node in subtree_nodes(root):
            if not node.concept_id:
                continue
            topic = _concept_topic(node.concept, node, global_position)
            class_topics.append(topic)
            play_order.append(topic.concept_uuid)
            global_position += 1
        classes.append(ClassRdf(
            node_uuid=str(root.uuid),
            label=root.label,
            position=class_pos,
            topics=class_topics,
        ))

    return TemarioRdfDocument(
        title=title,
        taxonomy_slug=taxonomy.slug,
        taxonomy_name=taxonomy.name,
        granularity=granularity,
        session_uuid=session_uuid,
        classes=classes,
        play_order=play_order,
    )


def document_from_session(session: AiramSession) -> TemarioRdfDocument:
    combined = list((session.state or {}).get("combined_node_uuids") or [])
    if not combined:
        combined = [str(session.root_node.uuid)]
    return build_temario_document(
        taxonomy=session.taxonomy,
        combined_uuids=combined,
        title=session.title,
        granularity=session.granularity,
        session_uuid=str(session.uuid),
    )


def document_from_node_uuids(
    taxonomy_slug: str,
    node_uuids: list[str],
    *,
    granularity: str = "normal",
    title: str | None = None,
) -> TemarioRdfDocument:
    taxonomy = Taxonomy.objects.get(slug=taxonomy_slug, is_active=True)
    roots = _class_roots(taxonomy, node_uuids)
    if not roots:
        raise ValueError("No se encontraron clases válidas para exportar.")
    if not title:
        labels = [r.label for r in roots[:3]]
        title = " + ".join(labels)
        if len(roots) > 3:
            title += f" (+{len(roots) - 3})"
        title += f" — {taxonomy.name}"
    return build_temario_document(
        taxonomy=taxonomy,
        combined_uuids=node_uuids,
        title=title,
        granularity=granularity,
    )


def _topic_jsonld(topic: TopicRdf, base: str) -> dict:
    uri = f"{base}/biblioteca/temas/{topic.concept_uuid}/"
    data: dict = {
        "@id": uri,
        "@type": ["skos:Concept", "schema:DefinedTerm", "airam:Topic"],
        "skos:prefLabel": topic.label,
        "schema:name": topic.label,
        "airam:nodeUuid": topic.node_uuid,
        "airam:position": topic.position,
        "airam:breadcrumb": topic.breadcrumb,
    }
    if topic.definition:
        data["skos:definition"] = topic.definition
        data["schema:description"] = topic.definition
    if topic.examples:
        data["schema:example"] = topic.examples
    if topic.properties:
        data["airam:ontologyProperty"] = [
            {"@type": "schema:PropertyValue", "schema:name": p["key"], "schema:value": p["value"]}
            for p in topic.properties
        ]
    relations = []
    for rel in topic.relations_out:
        relations.append({
            "@type": "airam:Relation",
            "airam:relationType": rel["type"],
            "schema:target": {
                "@id": f"{base}/biblioteca/temas/{rel['target_uuid']}/",
                "schema:name": rel["target_label"],
            },
        })
    for rel in topic.relations_in:
        relations.append({
            "@type": "airam:Relation",
            "airam:relationType": rel["type"],
            "schema:source": {
                "@id": f"{base}/biblioteca/temas/{rel['source_uuid']}/",
                "schema:name": rel["source_label"],
            },
        })
    if relations:
        data["airam:relation"] = relations
    return data


def document_to_jsonld(doc: TemarioRdfDocument) -> dict:
    base = _site_base()
    ns = _ns()
    session_id = (
        f"{base}/airam/sessions/{doc.session_uuid}/"
        if doc.session_uuid
        else f"{ns}temario/{doc.taxonomy_slug}/{hash(tuple(doc.play_order)) & 0xFFFFFFFF:x}"
    )

    graph: list[dict] = []
    class_refs = []

    for cls in doc.classes:
        class_id = f"{base}/airam/classes/{cls.node_uuid}/"
        topic_refs = [f"{base}/biblioteca/temas/{t.concept_uuid}/" for t in cls.topics]
        class_node = {
            "@id": class_id,
            "@type": ["airam:TemarioClass", "schema:Chapter"],
            "schema:position": cls.position,
            "schema:name": cls.label,
            "airam:rootNodeUuid": cls.node_uuid,
            "airam:hasTopic": topic_refs,
        }
        graph.append(class_node)
        class_refs.append({"@id": class_id})
        for topic in cls.topics:
            graph.append(_topic_jsonld(topic, base))

    session_node = {
        "@id": session_id,
        "@type": ["airam:TemarioSession", "schema:LearningResource"],
        "schema:name": doc.title,
        "airam:granularity": doc.granularity,
        "airam:taxonomy": {
            "@id": f"{base}/biblioteca/taxonomias/{doc.taxonomy_slug}/",
            "schema:name": doc.taxonomy_name,
        },
        "airam:combinedClass": class_refs,
        "airam:playOrder": [f"{base}/biblioteca/temas/{uuid}/" for uuid in doc.play_order],
        "airam:topicCount": len(doc.play_order),
        "airam:generator": "AIRAM/CORE Radio Micelio",
    }

    return {
        "@context": {
            "@vocab": f"{ns}airam#",
            "schema": "https://schema.org/",
            "skos": "http://www.w3.org/2004/02/skos/core#",
            "airam": f"{ns}airam#",
            "name": "schema:name",
            "description": "schema:description",
            "position": "schema:position",
        },
        "@graph": [session_node, *graph],
    }


def _ttl_literal(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def document_to_turtle(doc: TemarioRdfDocument) -> str:
    base = _site_base()
    ns = _ns()
    lines = [
        f"@prefix schema: <https://schema.org/> .",
        f"@prefix skos: <http://www.w3.org/2004/02/skos/core#> .",
        f"@prefix airam: <{ns}airam#> .",
        "",
    ]

    if doc.session_uuid:
        session_uri = f"<{base}/airam/sessions/{doc.session_uuid}/>"
    else:
        session_uri = f"<{ns}temario/{doc.taxonomy_slug}>"

    lines.append(f"{session_uri} a airam:TemarioSession, schema:LearningResource ;")
    lines.append(f"  schema:name {_ttl_literal(doc.title)} ;")
    lines.append(f"  airam:granularity {_ttl_literal(doc.granularity)} ;")
    lines.append(f"  airam:topicCount {len(doc.play_order)} ;")
    lines.append(f'  airam:taxonomy <{base}/biblioteca/taxonomias/{doc.taxonomy_slug}/> ;')
    lines.append(f'  airam:generator "AIRAM/CORE Radio Micelio" ;')

    class_uris = []
    for cls in doc.classes:
        class_uri = f"<{base}/airam/classes/{cls.node_uuid}/>"
        class_uris.append(class_uri)
        lines.append("")
        lines.append(f"{class_uri} a airam:TemarioClass, schema:Chapter ;")
        lines.append(f"  schema:position {cls.position} ;")
        lines.append(f"  schema:name {_ttl_literal(cls.label)} ;")
        lines.append(f"  airam:rootNodeUuid {_ttl_literal(cls.node_uuid)} .")

        for topic in cls.topics:
            topic_uri = f"<{base}/biblioteca/temas/{topic.concept_uuid}/>"
            lines.append("")
            lines.append(f"{topic_uri} a skos:Concept, schema:DefinedTerm, airam:Topic ;")
            lines.append(f"  skos:prefLabel {_ttl_literal(topic.label)} ;")
            lines.append(f"  airam:position {topic.position} ;")
            lines.append(f"  airam:nodeUuid {_ttl_literal(topic.node_uuid)} ;")
            if topic.definition:
                lines.append(f"  skos:definition {_ttl_literal(topic.definition)} ;")
            lines.append(f"  airam:breadcrumb {_ttl_literal(' › '.join(topic.breadcrumb))} .")
            for prop in topic.properties:
                lines.append(
                    f"{topic_uri} airam:ontologyProperty "
                    f"[ schema:name {_ttl_literal(prop['key'])} ; schema:value {_ttl_literal(prop['value'])} ] ."
                )
            for rel in topic.relations_out:
                lines.append(
                    f"{topic_uri} airam:relation "
                    f"[ airam:relationType {_ttl_literal(rel['type'])} ; "
                    f"schema:target <{base}/biblioteca/temas/{rel['target_uuid']}/> ] ."
                )

    lines.append("")
    lines.append(f"{session_uri} airam:combinedClass {', '.join(class_uris)} .")
    play = ", ".join(f"<{base}/biblioteca/temas/{u}/>" for u in doc.play_order)
    if play:
        lines.append(f"{session_uri} airam:playOrder ( {play} ) .")
    lines.append("")
    return "\n".join(lines)


def session_to_jsonld(session: AiramSession) -> dict:
    return document_to_jsonld(document_from_session(session))


def session_to_turtle(session: AiramSession) -> str:
    return document_to_turtle(document_from_session(session))
