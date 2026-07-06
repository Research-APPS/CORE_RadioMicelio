from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from uuid import UUID

from ontologizar_app.models import Concept, Taxonomy, TaxonomyNode
from ontologizar_app.services.concept_indicators import _is_ontology_property


LEVEL_LABELS = ("vacío", "esbozo", "básico", "desarrollado", "completo")


@dataclass(frozen=True)
class KnowledgeDepth:
    level: int
    label: str
    text_chars: int
    relations_count: int
    properties_count: int

    @property
    def title(self) -> str:
        return (
            f"Nivel {self.level}/4 ({self.label}): "
            f"{self.text_chars} caracteres de texto, "
            f"{self.relations_count} relaciones, "
            f"{self.properties_count} propiedades ontológicas"
        )


def _concept_metrics(concept: Concept) -> tuple[int, int, int]:
    text_chars = sum(
        len(d.text.strip())
        for d in concept.definitions.all()
        if d.is_active and d.text.strip()
    )
    relations_count = concept.outgoing_relations.count() + concept.incoming_relations.count()
    properties_count = sum(
        1 for p in concept.properties.all()
        if _is_ontology_property(p.key) and p.value.strip()
    )
    return text_chars, relations_count, properties_count


def score_from_metrics(text_chars: int, relations_count: int, properties_count: int) -> int:
    score = 0
    if text_chars >= 20:
        score += 1
    if text_chars >= 120:
        score += 1
    if text_chars >= 400:
        score += 1
    score += min(2, relations_count)
    score += min(2, properties_count)
    return min(4, score)


def depth_from_metrics(text_chars: int, relations_count: int, properties_count: int) -> KnowledgeDepth:
    level = score_from_metrics(text_chars, relations_count, properties_count)
    return KnowledgeDepth(
        level=level,
        label=LEVEL_LABELS[level],
        text_chars=text_chars,
        relations_count=relations_count,
        properties_count=properties_count,
    )


def build_taxonomy_knowledge_map(taxonomy: Taxonomy) -> dict[UUID, KnowledgeDepth]:
    """Profundidad de conocimiento dentro de cada nodo (subárbol agregado)."""
    nodes = list(
        TaxonomyNode.objects.filter(taxonomy=taxonomy)
        .select_related("concept")
        .order_by("tree_id", "lft")
    )
    if not nodes:
        return {}

    concept_ids = {n.concept_id for n in nodes if n.concept_id}
    concepts = {
        c.pk: c
        for c in Concept.objects.filter(pk__in=concept_ids).prefetch_related(
            "definitions", "properties", "outgoing_relations", "incoming_relations",
        )
    }
    metrics_by_concept = {
        pk: _concept_metrics(concept) for pk, concept in concepts.items()
    }

    children_by_parent: dict[int | None, list[TaxonomyNode]] = defaultdict(list)
    for node in nodes:
        children_by_parent[node.parent_id].append(node)

    result: dict[UUID, KnowledgeDepth] = {}

    def aggregate(node: TaxonomyNode) -> tuple[int, int, int]:
        text_chars, relations_count, properties_count = 0, 0, 0
        if node.concept_id:
            c, r, p = metrics_by_concept.get(node.concept_id, (0, 0, 0))
            text_chars += c
            relations_count += r
            properties_count += p
        for child in children_by_parent.get(node.id, []):
            cc, cr, cp = aggregate(child)
            text_chars += cc
            relations_count += cr
            properties_count += cp
        result[node.uuid] = depth_from_metrics(text_chars, relations_count, properties_count)
        return text_chars, relations_count, properties_count

    for root in children_by_parent.get(None, []):
        aggregate(root)
    return result


def build_taxonomy_tree_roots(taxonomy: Taxonomy) -> list[TaxonomyNode]:
    """Carga el árbol en memoria con profundidad de conocimiento y hijos anidados."""
    knowledge_map = build_taxonomy_knowledge_map(taxonomy)
    nodes = list(
        TaxonomyNode.objects.filter(taxonomy=taxonomy)
        .select_related("concept")
        .order_by("tree_id", "lft")
    )
    children_by_parent: dict[int | None, list[TaxonomyNode]] = defaultdict(list)
    for node in nodes:
        node.knowledge_depth = knowledge_map.get(node.uuid)
        children_by_parent[node.parent_id].append(node)
    for node in nodes:
        node.taxonomy_children = children_by_parent.get(node.id, [])
    return children_by_parent.get(None, [])
