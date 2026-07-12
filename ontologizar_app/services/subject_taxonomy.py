from __future__ import annotations

from ontologizar_app.models import Subject, SubjectTaxonomy, Taxonomy


def assign_subject_taxonomy(
    subject: Subject | str,
    taxonomy: Taxonomy | str,
    *,
    role: str = "class",
    taxonomy_group: str = "",
    is_primary: bool = False,
    position: int = 0,
) -> SubjectTaxonomy:
    if isinstance(subject, str):
        subject = Subject.objects.get(slug=subject)
    if isinstance(taxonomy, str):
        taxonomy = Taxonomy.objects.get(slug=taxonomy)

    assignment, _ = SubjectTaxonomy.objects.update_or_create(
        subject=subject,
        taxonomy=taxonomy,
        role=role,
        defaults={
            "taxonomy_group": taxonomy_group,
            "is_primary": is_primary,
            "position": position,
        },
    )
    return assignment
