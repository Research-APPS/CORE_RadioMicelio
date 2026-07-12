from __future__ import annotations

from dataclasses import dataclass, field

from airam_app.services.temario import node_breadcrumb
from ontologizar_app.models import Concept, Dictionary, Subject, SubjectTaxonomy, Taxonomy, TaxonomyNode


ROLE_LABELS = {
    "class": "Taxonomías de clases",
    "property": "Taxonomías de propiedades",
    "thematic": "Taxonomías temáticas",
}

GROUP_LABELS = {
    "estructural": "Estructural",
    "arquetipico": "Arquetípico",
    "tematico": "Temático",
    "simbolico": "Simbólico",
}


def taxonomy_group_label(slug: str) -> str:
    if not slug:
        return ""
    return GROUP_LABELS.get(slug, slug.replace("-", " ").replace("_", " ").title())


@dataclass
class TaxonomyAssignmentRow:
    taxonomy: Taxonomy
    role: str
    taxonomy_group: str
    taxonomy_group_label: str
    is_primary: bool
    concept_count: int


@dataclass
class DictionaryRow:
    dictionary: Dictionary
    concept_count: int


@dataclass
class CompletenessInfo:
    dictionary_count: int
    class_taxonomy_count: int
    property_taxonomy_count: int
    thematic_taxonomy_count: int
    total_concepts: int
    classified_concepts: int
    unclassified_count: int
    warnings: list[str] = field(default_factory=list)


@dataclass
class SubjectCurriculumProfile:
    subject: Subject
    dictionaries: list[DictionaryRow]
    taxonomies_by_role: dict[str, list[TaxonomyAssignmentRow]]
    unclassified_concepts: list[Concept]
    completeness: CompletenessInfo


@dataclass
class ConceptClassification:
    taxonomy: Taxonomy
    breadcrumb: list[str]
    taxonomy_group: str
    taxonomy_group_label: str


def _class_taxonomies_for_subject(subject: Subject) -> list[Taxonomy]:
    return [
        a.taxonomy
        for a in SubjectTaxonomy.objects.filter(
            subject=subject, role="class", taxonomy__is_active=True,
        ).select_related("taxonomy").order_by("position", "taxonomy__name")
    ]


def subject_curriculum_profile(subject: Subject) -> SubjectCurriculumProfile:
    dictionaries = [
        DictionaryRow(dictionary=d, concept_count=d.concepts.count())
        for d in subject.dictionaries.filter(is_active=True).order_by("name")
    ]

    taxonomies_by_role: dict[str, list[TaxonomyAssignmentRow]] = {
        "class": [], "property": [], "thematic": [],
    }
    assignments = SubjectTaxonomy.objects.filter(
        subject=subject, taxonomy__is_active=True,
    ).select_related("taxonomy").order_by("role", "position", "taxonomy__name")

    for assignment in assignments:
        tax = assignment.taxonomy
        concept_count = TaxonomyNode.objects.filter(
            taxonomy=tax, concept__dictionary__subject=subject,
        ).count()
        row = TaxonomyAssignmentRow(
            taxonomy=tax,
            role=assignment.role,
            taxonomy_group=assignment.taxonomy_group,
            taxonomy_group_label=taxonomy_group_label(assignment.taxonomy_group),
            is_primary=assignment.is_primary,
            concept_count=concept_count,
        )
        taxonomies_by_role.setdefault(assignment.role, []).append(row)

    class_taxonomies = _class_taxonomies_for_subject(subject)
    class_tax_ids = [t.id for t in class_taxonomies]

    all_concepts = list(
        Concept.objects.filter(dictionary__subject=subject, dictionary__is_active=True)
        .select_related("dictionary")
        .order_by("dictionary__name", "label")
    )

    if class_tax_ids:
        classified_ids = set(
            TaxonomyNode.objects.filter(
                taxonomy_id__in=class_tax_ids,
                concept__isnull=False,
                concept__dictionary__subject=subject,
            ).values_list("concept_id", flat=True)
        )
    else:
        classified_ids = set()

    unclassified = [c for c in all_concepts if c.id not in classified_ids]

    warnings: list[str] = []
    if not dictionaries:
        warnings.append("Sin diccionarios activos.")
    if not taxonomies_by_role["class"]:
        warnings.append("Sin taxonomías de clases vinculadas.")
    if unclassified:
        warnings.append(f"{len(unclassified)} concepto(s) sin clasificar en taxonomías de clases.")

    completeness = CompletenessInfo(
        dictionary_count=len(dictionaries),
        class_taxonomy_count=len(taxonomies_by_role["class"]),
        property_taxonomy_count=len(taxonomies_by_role["property"]),
        thematic_taxonomy_count=len(taxonomies_by_role["thematic"]),
        total_concepts=len(all_concepts),
        classified_concepts=len(classified_ids),
        unclassified_count=len(unclassified),
        warnings=warnings,
    )

    return SubjectCurriculumProfile(
        subject=subject,
        dictionaries=dictionaries,
        taxonomies_by_role=taxonomies_by_role,
        unclassified_concepts=unclassified,
        completeness=completeness,
    )


def concept_classifications(concept: Concept) -> list[ConceptClassification]:
    nodes = TaxonomyNode.objects.filter(concept=concept).select_related("taxonomy")
    tax_ids = [n.taxonomy_id for n in nodes]
    group_by_tax = {
        a.taxonomy_id: a.taxonomy_group
        for a in SubjectTaxonomy.objects.filter(
            subject=concept.dictionary.subject,
            taxonomy_id__in=tax_ids,
        )
    }
    results: list[ConceptClassification] = []
    for node in nodes:
        group = group_by_tax.get(node.taxonomy_id, "")
        results.append(ConceptClassification(
            taxonomy=node.taxonomy,
            breadcrumb=node_breadcrumb(node),
            taxonomy_group=group,
            taxonomy_group_label=taxonomy_group_label(group),
        ))
    results.sort(key=lambda r: (r.taxonomy.name, " → ".join(r.breadcrumb)))
    return results
