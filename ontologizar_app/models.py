from __future__ import annotations
import uuid
from django.db import models
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey

from airam_app.services.semantic_relations import RELATION_TYPES

# Etiquetas legibles para el <select> del CMS — RELATION_TYPES (en
# airam_app/services/semantic_relations.py) sigue siendo la única fuente de
# verdad de qué tipos existen; esto solo decide cómo se muestran.
_RELATION_LABELS = {
    "related": "Relacionado",
    "broader": "Más amplio",
    "narrower": "Más estrecho",
    "part_of": "Parte de",
    "has_part": "Tiene como parte a",
    "produces": "Produce",
    "enables": "Permite",
    "participates_in": "Participa en",
    "works_via": "Funciona mediante",
    "evolves_from": "Evoluciona de",
    "evolves_to": "Evoluciona hacia",
    "historically_after": "Viene después de",
    "historically_before": "Viene antes de",
    "appears_in": "Aparece en",
    "invented_by": "Inventado por",
    "used_in": "Se usa en",
    "transmits_to": "Transmite a",
    "may_fail_as": "Puede fallar como",
    "requires_maintenance": "Requiere mantenimiento",
    "may_lead_to": "Puede llevar a",
    "monta_a": "Monta a",
    "escudero_de": "Escudero de",
    "ama_a": "Ama a",
    "ocurre_en": "Ocurre en",
    "advierte_a": "Advierte a",
    "ataca_a": "Ataca a",
    # #ontoNarrativa — relaciones documentales universales
    "contiene": "Contiene",
    "padre_de": "Padre de",
    "hijo_de": "Hijo de",
    "enemigo_de": "Enemigo de",
    "amigo_de": "Amigo de",
    "sirve_a": "Sirve a",
    "traiciona_a": "Traiciona a",
    "posee": "Posee",
    "viaja_a": "Viaja a",
    "criado_por": "Criado por",
    "enamorado_de": "Enamorado de",
    # Procedencia y marcos interpretativos
    "defined_in": "Definido en",
    "interpreted_as": "Interpretado como",
    "develops": "Desarrolla",
    "reinterprets": "Reinterpreta",
    "criticizes": "Critica",
    "distinct_from": "Distinto de",
}


class Subject(models.Model):
    """Asignatura — metáfora escolar dentro de la biblioteca."""
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    slug = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    source_url = models.URLField(blank=True, help_text="Fuente externa (p. ej. Wikipedia)")
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
    body = models.TextField(blank=True, help_text="Texto wiki del material")
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


class SubjectTaxonomy(models.Model):
    """Vincula una asignatura con las taxonomías que utiliza (por rol y grupo taxonómico)."""

    ROLE_CHOICES = [
        ("class", "Taxonomía de clases"),
        ("property", "Taxonomía de propiedades"),
        ("thematic", "Taxonomía temática"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="taxonomy_assignments",
    )
    taxonomy = models.ForeignKey(
        "Taxonomy", on_delete=models.CASCADE, related_name="subject_assignments",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="class")
    taxonomy_group = models.CharField(
        max_length=80, blank=True,
        help_text="Grupo taxonómico: agrupación editorial de árboles.",
    )
    is_primary = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "taxonomy__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["subject", "taxonomy", "role"],
                name="unique_subject_taxonomy_role",
            ),
        ]

    def __str__(self):
        group = f" [{self.taxonomy_group}]" if self.taxonomy_group else ""
        return f"{self.subject.slug} — {self.taxonomy.slug} ({self.role}){group}"


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
    KIND_CHOICES = [
        ("definition", "Definición"),
        ("definition_primary", "Definición (fuente primaria)"),
        ("definition_institutional", "Definición (fuente institucional)"),
        ("definition_scholarly", "Definición (estudio académico)"),
        ("example", "Ejemplo"),
        ("note", "Nota"),
        ("reference", "Referencia"),
    ]
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name="definitions")
    text = models.TextField()
    kind = models.CharField(max_length=32, choices=KIND_CHOICES, default="definition")
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
    # snake_case canónico — ver airam_app/services/semantic_relations.py (RELATION_TYPES es la
    # única fuente de verdad). "partOf" (legacy camelCase) ya no es una opción nueva válida;
    # se sigue aceptando en datos existentes y se normaliza a "part_of" vía normalize_relation_type().
    RELATION_CHOICES = [(t, _RELATION_LABELS[t]) for t in RELATION_TYPES]
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    source = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name="outgoing_relations")
    target = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name="incoming_relations")
    relation_type = models.CharField(max_length=32, choices=RELATION_CHOICES, default="related")

    class Meta:
        unique_together = [("source", "target", "relation_type")]


class AttributedRelation(models.Model):
    """Metadatos de procedencia para una ConceptRelation (hecho documental o interpretación)."""

    AUTHORITY_LAYER_CHOICES = [
        ("factual", "Documental"),
        ("interpretive", "Interpretativa"),
    ]
    CONFIDENCE_CHOICES = [
        ("documented", "Documentada"),
        ("inferred", "Inferida"),
        ("speculative", "Especulativa"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    relation = models.OneToOneField(
        ConceptRelation, on_delete=models.CASCADE, related_name="attribution",
    )
    authority_layer = models.CharField(
        max_length=20, choices=AUTHORITY_LAYER_CHOICES, default="factual",
    )
    framework = models.CharField(
        max_length=80, blank=True,
        help_text="Slug de perspectiva interpretativa (ej. lectura_politica); vacío en hechos documentales.",
    )
    asserted_by = models.CharField(max_length=300, blank=True)
    asserted_by_concept = models.ForeignKey(
        Concept, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="attributions_as_author",
    )
    source_work = models.CharField(max_length=500, blank=True)
    locator = models.CharField(max_length=200, blank=True)
    confidence = models.CharField(
        max_length=20, choices=CONFIDENCE_CHOICES, default="documented",
    )
    scope = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ["-relation_id"]

    def __str__(self):
        return f"{self.relation} ({self.authority_layer})"


# --- Fase 1.5b (diseño, no implementado) ---
# OntologyProperty: lema reutilizable de propiedad (ej. "color", "frecuencia_hz") con
# SubjectTaxonomy role="property" vinculando taxonomías de propiedades a asignaturas.
# ConceptPropertyAssertion: N:M concepto↔OntologyProperty con valor tipado, distinto de
# ConceptProperty (clave libre por concepto). Permite árboles de propiedades y clasificación
# paralela a las taxonomías de clases.
