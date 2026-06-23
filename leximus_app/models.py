import uuid
from django.db import models
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey


class Taxonomy(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    slug = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "taxonomies"

    def __str__(self):
        return self.name


class TaxonomyNode(MPTTModel):
    taxonomy = models.ForeignKey(Taxonomy, on_delete=models.CASCADE, related_name="nodes")
    label = models.CharField(max_length=200)
    parent = TreeForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")

    class MPTTMeta:
        order_insertion_by = ["label"]

    def __str__(self):
        return self.label


class ProjectTaxonomyLink(models.Model):
    research_project_uuid = models.UUIDField(db_index=True)
    taxonomy = models.ForeignKey(Taxonomy, on_delete=models.CASCADE, related_name="project_links")
    is_primary = models.BooleanField(default=True)
    activated_by_username = models.CharField(max_length=150, blank=True)
    activated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["research_project_uuid", "taxonomy"],
                name="leximus_unique_project_taxonomy",
            ),
        ]

    def __str__(self):
        return f"{self.research_project_uuid} → {self.taxonomy.slug}"
