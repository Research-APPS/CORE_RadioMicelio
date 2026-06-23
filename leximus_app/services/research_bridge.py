from __future__ import annotations
from uuid import UUID

from core_retiro.core_urls import module_url
from leximus_app.models import ProjectTaxonomyLink, Taxonomy
from research_app.capability_registry import ProjectCapabilityDescriptor


def get_taxonomies_for_project(project_uuid: UUID):
    return Taxonomy.objects.filter(
        project_links__research_project_uuid=project_uuid,
        is_active=True,
    ).distinct().order_by("name")


def get_primary_taxonomy_for_project(project_uuid: UUID) -> Taxonomy | None:
    link = (
        ProjectTaxonomyLink.objects.filter(
            research_project_uuid=project_uuid,
            is_primary=True,
            taxonomy__is_active=True,
        )
        .select_related("taxonomy")
        .first()
    )
    return link.taxonomy if link else None


def activate_leximus_for_project(
    project_uuid: UUID,
    taxonomy_slug: str,
    username: str = "",
    *,
    is_primary: bool = True,
):
    taxonomy = Taxonomy.objects.get(slug=taxonomy_slug, is_active=True)
    if is_primary:
        ProjectTaxonomyLink.objects.filter(
            research_project_uuid=project_uuid,
            is_primary=True,
        ).update(is_primary=False)
    link, created = ProjectTaxonomyLink.objects.get_or_create(
        research_project_uuid=project_uuid,
        taxonomy=taxonomy,
        defaults={"is_primary": is_primary, "activated_by_username": username},
    )
    if not created and is_primary:
        link.is_primary = True
        link.save(update_fields=["is_primary"])
    return link


def get_ontology_descriptor(project_uuid: UUID) -> ProjectCapabilityDescriptor | None:
    taxonomy = get_primary_taxonomy_for_project(project_uuid)
    if not taxonomy:
        return ProjectCapabilityDescriptor(
            capability_slug="ontology",
            implementation_slug="leximus",
            source_module="leximus_app",
            active=False,
            label="Ontologizar",
            summary={"message": "Ontologizar no activado para este proyecto"},
        )
    node_count = taxonomy.nodes.count()
    jsonld_url = module_url("leximus", f"api/taxonomies/{taxonomy.slug}/jsonld/")
    manage_url = module_url("leximus", f"taxonomies/{taxonomy.slug}/")
    return ProjectCapabilityDescriptor(
        capability_slug="ontology",
        implementation_slug="leximus",
        source_module="leximus_app",
        active=True,
        label="Ontologizar",
        manage_url=manage_url,
        api_url=module_url("leximus", f"api/taxonomies/{taxonomy.slug}/"),
        jsonld_url=jsonld_url,
        summary={
            "taxonomy_slug": taxonomy.slug,
            "taxonomy_name": taxonomy.name,
            "node_count": node_count,
        },
    )
