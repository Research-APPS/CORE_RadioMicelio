from __future__ import annotations

from dataclasses import dataclass

from ontologizar_app.models import AttributedRelation, Concept, ConceptRelation


INTERPRETIVE_RELATION_TYPES = frozenset({
    "interpreted_as", "defined_in", "develops", "reinterprets", "criticizes",
})

FACTUAL_RELATION_TYPES = frozenset({
    "contiene", "padre_de", "hijo_de", "enemigo_de", "amigo_de", "sirve_a",
    "traiciona_a", "participa_en", "ocurre_en", "posee", "viaja_a",
    "criado_por", "enamorado_de", "ama_a", "appears_in",
})


@dataclass(frozen=True)
class AttributedRelationView:
    relation: ConceptRelation
    attribution: AttributedRelation
    source_label: str
    target_label: str
    relation_type: str


def create_attributed_relation(
    source: Concept,
    target: Concept,
    relation_type: str,
    *,
    authority_layer: str = "factual",
    framework: str = "",
    asserted_by: str = "",
    asserted_by_concept: Concept | None = None,
    source_work: str = "",
    locator: str = "",
    confidence: str = "documented",
    scope: str = "",
) -> AttributedRelation:
    relation, _ = ConceptRelation.objects.get_or_create(
        source=source, target=target, relation_type=relation_type,
    )
    attrs, _ = AttributedRelation.objects.update_or_create(
        relation=relation,
        defaults={
            "authority_layer": authority_layer,
            "framework": framework,
            "asserted_by": asserted_by,
            "asserted_by_concept": asserted_by_concept,
            "source_work": source_work,
            "locator": locator,
            "confidence": confidence,
            "scope": scope,
        },
    )
    return attrs


def concept_interpretations(concept: Concept) -> list[AttributedRelationView]:
    """Interpretaciones documentadas donde `concept` es source o target."""
    views: list[AttributedRelationView] = []
    qs = (
        AttributedRelation.objects.filter(
            authority_layer="interpretive",
            relation__source=concept,
        ) | AttributedRelation.objects.filter(
            authority_layer="interpretive",
            relation__target=concept,
        )
    ).select_related(
        "relation", "relation__source", "relation__target",
    ).distinct()

    for attr in qs:
        rel = attr.relation
        views.append(AttributedRelationView(
            relation=rel,
            attribution=attr,
            source_label=rel.source.label,
            target_label=rel.target.label,
            relation_type=rel.relation_type,
        ))
    return views


def interpretation_is_complete(attribution: AttributedRelation) -> bool:
    if attribution.authority_layer != "interpretive":
        return True
    return bool(
        attribution.source_work.strip()
        and (attribution.asserted_by.strip() or attribution.asserted_by_concept_id)
    )
