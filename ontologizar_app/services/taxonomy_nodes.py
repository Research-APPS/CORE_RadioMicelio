from __future__ import annotations

from django.db import transaction

from ontologizar_app.models import Concept, Dictionary, Taxonomy, TaxonomyNode


def dictionary_for_taxonomy(taxonomy: Taxonomy) -> Dictionary | None:
    """Diccionario ontológico asociado a la taxonomía (inferido de nodos existentes)."""
    node = (
        TaxonomyNode.objects.filter(taxonomy=taxonomy, concept__isnull=False)
        .select_related("concept__dictionary")
        .first()
    )
    return node.concept.dictionary if node else None


@transaction.atomic
def add_taxonomy_node(
    taxonomy: Taxonomy,
    label: str,
    *,
    parent: TaxonomyNode | None = None,
    dictionary: Dictionary | None = None,
) -> TaxonomyNode:
    label = label.strip()
    if not label:
        raise ValueError("El nombre de la clase no puede estar vacío.")
    if parent and parent.taxonomy_id != taxonomy.pk:
        raise ValueError("El nodo padre no pertenece a esta taxonomía.")

    dictionary = dictionary or dictionary_for_taxonomy(taxonomy)
    if dictionary is None:
        raise ValueError(
            "No hay diccionario asociado a esta taxonomía. "
            "Importa la taxonomía desde el CMS o añade un nodo con concepto primero."
        )

    concept, _ = Concept.objects.get_or_create(dictionary=dictionary, label=label)
    return TaxonomyNode.objects.create(
        taxonomy=taxonomy,
        label=label,
        concept=concept,
        parent=parent,
    )
