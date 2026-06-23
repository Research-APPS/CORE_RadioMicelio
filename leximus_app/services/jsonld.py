from leximus_app.models import Taxonomy, TaxonomyNode


def taxonomy_to_jsonld(taxonomy: Taxonomy) -> dict:
    nodes = TaxonomyNode.objects.filter(taxonomy=taxonomy).order_by("tree_id", "lft")
    concepts = []
    for node in nodes:
        concepts.append({
            "@type": "DefinedTerm",
            "@id": f"#{node.pk}",
            "name": node.label,
            "broader": f"#{node.parent_id}" if node.parent_id else None,
        })
    return {
        "@context": "https://www.w3.org/2004/02/skos/core",
        "@type": "DefinedTermSet",
        "@id": taxonomy.slug,
        "name": taxonomy.name,
        "description": taxonomy.description,
        "hasDefinedTerm": concepts,
    }
