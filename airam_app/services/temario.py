from __future__ import annotations

import re

from ontologizar_app.models import Concept, TaxonomyNode
from ontologizar_app.services.concept_indicators import _is_ontology_property

GRANULARITIES = frozenset({"breve", "normal", "profundo", "temario"})
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def first_sentence(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    parts = _SENTENCE_END.split(text, maxsplit=1)
    return parts[0]


def subtree_nodes(root: TaxonomyNode) -> list[TaxonomyNode]:
    return list(
        root.get_descendants(include_self=True)
        .select_related("concept")
        .prefetch_related(
            "concept__definitions",
            "concept__properties",
            "concept__outgoing_relations__target",
            "concept__incoming_relations__source",
        )
        .order_by("lft")
    )


def node_breadcrumb(node: TaxonomyNode) -> list[str]:
    return [a.label for a in node.get_ancestors(include_self=True)]


def _local_relations(concept: Concept) -> list[str]:
    dict_id = concept.dictionary_id
    lines = []
    for rel in concept.outgoing_relations.all():
        if rel.target.dictionary_id == dict_id:
            lines.append(f"→ {rel.target.label} ({rel.relation_type})")
    for rel in concept.incoming_relations.all():
        if rel.source.dictionary_id == dict_id:
            lines.append(f"← {rel.source.label} ({rel.relation_type})")
    return lines


def _ontology_properties(concept: Concept) -> list[str]:
    return [
        f"{p.key}: {p.value}"
        for p in concept.properties.all()
        if _is_ontology_property(p.key) and p.value.strip()
    ]


def _active_definition(concept: Concept) -> str:
    d = concept.definitions.filter(is_active=True, kind="definition").first()
    return d.text.strip() if d and d.text else ""


def narrate_concept(concept: Concept, granularity: str, *, heading: str | None = None) -> dict:
    label = heading or concept.label
    paragraphs: list[str] = []
    concepts = [{"uuid": str(concept.uuid), "label": concept.label}]
    def_text = _active_definition(concept)

    if granularity == "breve":
        if def_text:
            paragraphs.append(f"{label}: {first_sentence(def_text)}")
        else:
            paragraphs.append(label)
    elif granularity == "normal":
        paragraphs.append(label)
        if def_text:
            paragraphs.append(def_text)
    elif granularity == "profundo":
        paragraphs.append(label)
        if def_text:
            paragraphs.append(def_text)
        props = _ontology_properties(concept)
        if props:
            paragraphs.append("Propiedades: " + "; ".join(props))
        rels = _local_relations(concept)
        if rels:
            paragraphs.append("Relaciones: " + "; ".join(rels))
    elif granularity == "temario":
        paragraphs.append(label)
        if def_text:
            paragraphs.append(def_text)
        props = _ontology_properties(concept)
        if props:
            paragraphs.append("Propiedades: " + "; ".join(props))
        rels = _local_relations(concept)
        if rels:
            paragraphs.append("Relaciones: " + "; ".join(rels))

    return {"paragraphs": paragraphs, "concepts": concepts}


def narrate_node(node: TaxonomyNode, granularity: str) -> dict:
    if granularity not in GRANULARITIES:
        granularity = "normal"

    if node.concept_id:
        result = narrate_concept(node.concept, granularity, heading=node.label)
    else:
        result = {"paragraphs": [node.label], "concepts": []}

    if granularity == "temario":
        children = list(node.get_children())
        if children:
            child_labels = ", ".join(c.label for c in children)
            result["paragraphs"].append(f"Incluye: {child_labels}.")
        crumb = " › ".join(node_breadcrumb(node))
        if crumb:
            result["paragraphs"].insert(0, f"Ruta: {crumb}.")

    result["breadcrumb"] = node_breadcrumb(node)
    result["node_uuid"] = str(node.uuid)
    result["node_label"] = node.label
    return result


def next_node_in_subtree(root: TaxonomyNode, current: TaxonomyNode) -> TaxonomyNode | None:
    nodes = subtree_nodes(root)
    ids = [n.pk for n in nodes]
    if current.pk not in ids:
        return nodes[0] if nodes else None
    idx = ids.index(current.pk)
    if idx + 1 < len(nodes):
        return nodes[idx + 1]
    return None


def combined_subtree_nodes(
    taxonomy_id: int,
    node_uuids: list[str],
) -> list[TaxonomyNode]:
    """Recorre varias clases en orden, aplanando subárboles sin duplicar nodos."""
    if not node_uuids:
        return []

    nodes_by_uuid = {
        str(n.uuid): n
        for n in TaxonomyNode.objects.filter(
            taxonomy_id=taxonomy_id,
            uuid__in=node_uuids,
        ).select_related("concept")
    }

    seen: set[int] = set()
    result: list[TaxonomyNode] = []
    for uuid in node_uuids:
        root = nodes_by_uuid.get(str(uuid))
        if not root:
            continue
        for node in subtree_nodes(root):
            if node.pk not in seen:
                seen.add(node.pk)
                result.append(node)
    return result


def session_nodes(session) -> list[TaxonomyNode]:
    """Nodos del temario activo (una clase o varias combinadas)."""
    state = session.state or {}
    combined = state.get("combined_node_uuids")
    if combined:
        return combined_subtree_nodes(session.taxonomy_id, combined)
    return subtree_nodes(session.root_node)


def next_node_in_session(session, current: TaxonomyNode) -> TaxonomyNode | None:
    nodes = session_nodes(session)
    if not nodes:
        return None
    ids = [n.pk for n in nodes]
    if current.pk not in ids:
        return nodes[0]
    idx = ids.index(current.pk)
    if idx + 1 < len(nodes):
        return nodes[idx + 1]
    return None


def segment_start_labels(session) -> dict[str, str]:
    """Mapa nodo_uuid → etiqueta de clase al empezar cada segmento del temario combinado."""
    state = session.state or {}
    combined = state.get("combined_node_uuids") or []
    if len(combined) <= 1:
        return {}

    labels: dict[str, str] = {}
    for uuid in combined:
        root = TaxonomyNode.objects.filter(
            uuid=uuid, taxonomy_id=session.taxonomy_id,
        ).first()
        if not root:
            continue
        segment = subtree_nodes(root)
        if segment:
            labels[str(segment[0].uuid)] = root.label
    return labels

