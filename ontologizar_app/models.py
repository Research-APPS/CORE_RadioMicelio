from __future__ import annotations
import uuid
from django.db import models
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey


class Subject(models.Model):
    """Asignatura — metáfora escolar dentro de la biblioteca."""
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    slug = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SubjectMaterial(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="materials")
    slug = models.SlugField(max_length=80)
    title = models.CharField(max_length=300)
    summary = models.TextField(blank=True)
    cms_url = models.URLField(blank=True)

    class Meta:
        unique_together = [("subject", "slug")]
        ordering = ["title"]

    def __str__(self):
        return self.title


class Dictionary(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="dictionaries")
    slug = models.SlugField(max_length=80)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("subject", "slug")]
        ordering = ["name"]
        verbose_name_plural = "dictionaries"

    def __str__(self):
        return f"{self.subject.slug}/{self.name}"


class Taxonomy(models.Model):
    """Vista de clasificación transversal del centro."""
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    slug = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "taxonomies"

    def __str__(self):
        return self.name


class Concept(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    dictionary = models.ForeignKey(Dictionary, on_delete=models.CASCADE, related_name="concepts")
    label = models.CharField(max_length=200)

    class Meta:
        ordering = ["label"]
        unique_together = [("dictionary", "label")]

    def __str__(self):
        return self.label

    @property
    def subject(self):
        return self.dictionary.subject

    def jsonld_path(self):
        return f"/ontologizar/api/concepts/{self.uuid}/jsonld/"

    def primary_taxonomy_slug(self) -> str:
        node = TaxonomyNode.objects.filter(concept=self).select_related("taxonomy").first()
        return node.taxonomy.slug if node else ""

    def taxonomies(self):
        return Taxonomy.objects.filter(nodes__concept=self).distinct()


class TaxonomyNode(MPTTModel):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    taxonomy = models.ForeignKey(Taxonomy, on_delete=models.CASCADE, related_name="nodes")
    label = models.CharField(max_length=200)
    concept = models.ForeignKey(Concept, on_delete=models.SET_NULL, null=True, blank=True, related_name="taxonomy_nodes")
    parent = TreeForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")

    class MPTTMeta:
        order_insertion_by = ["label"]

    def __str__(self):
        return f"{self.taxonomy.slug}/{self.label}"


class ConceptDefinition(models.Model):
    KIND_CHOICES = [("definition", "Definición"), ("example", "Ejemplo"), ("note", "Nota"), ("reference", "Referencia")]
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name="definitions")
    text = models.TextField()
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default="definition")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]


class ConceptProperty(models.Model):
    VALUE_TYPE_CHOICES = [("text", "Texto"), ("number", "Número"), ("url", "URL"), ("date", "Fecha")]
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name="properties")
    key = models.CharField(max_length=120)
    value = models.TextField()
    value_type = models.CharField(max_length=20, choices=VALUE_TYPE_CHOICES, default="text")

    class Meta:
        ordering = ["key"]
        unique_together = [("concept", "key")]


class ConceptRelation(models.Model):
    RELATION_CHOICES = [("broader", "Más amplio"), ("narrower", "Más estrecho"), ("related", "Relacionado"), ("partOf", "Parte de")]
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    source = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name="outgoing_relations")
    target = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name="incoming_relations")
    relation_type = models.CharField(max_length=20, choices=RELATION_CHOICES, default="related")

    class Meta:
        unique_together = [("source", "target", "relation_type")]
