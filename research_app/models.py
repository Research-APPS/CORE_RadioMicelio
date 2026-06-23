from __future__ import annotations
import uuid
from django.db import models
from django.urls import reverse
from django.utils import timezone


class ProyectoInvestigacion(models.Model):
    """Cuaderno de investigación (ResearchProject) — recorrido transversal por asignaturas."""

    ESTADO_CHOICES = [
        ("activa", "Activa"),
        ("pausada", "Pausada"),
        ("completada", "Completada"),
        ("cancelada", "Cancelada"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    acron = models.CharField(max_length=32, blank=True, db_index=True)
    titulo = models.CharField(max_length=300)
    descripcion = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="activa")
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    publico = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["titulo"]
        verbose_name = "Cuaderno de investigación"
        verbose_name_plural = "Cuadernos de investigación"

    def __str__(self):
        return self.acron or self.titulo

    def get_absolute_url(self):
        return reverse("research:proyecto_detail", kwargs={"uuid": self.uuid})


ResearchProject = ProyectoInvestigacion  # alias conceptual


class ProjectCurriculumDeclaration(models.Model):
    project = models.ForeignKey(ProyectoInvestigacion, on_delete=models.CASCADE, related_name="declarations")
    capability_slug = models.CharField(max_length=32, db_index=True)
    declared_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = [("project", "capability_slug")]

    def __str__(self):
        return f"{self.project.acron} → {self.capability_slug}"


class LearningMarker(models.Model):
    """Marcador — cita un concepto de la biblioteca sin copiar la taxonomía."""

    STATUS_CHOICES = [
        ("interesting", "Interesante"),
        ("selected", "Seleccionado"),
        ("used", "Usado"),
        ("cited", "Citado"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    project = models.ForeignKey(ProyectoInvestigacion, on_delete=models.CASCADE, related_name="markers")
    concept_uuid = models.UUIDField(db_index=True)
    subject_slug = models.CharField(max_length=80)
    dictionary_slug = models.CharField(max_length=80)
    taxonomy_slug = models.CharField(max_length=80)
    concept_label = models.CharField(max_length=200)
    jsonld_url = models.URLField(blank=True)
    note = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="selected")
    created_by = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.project.acron} → {self.concept_label}"

    @classmethod
    def from_concept(cls, project, concept, *, status="selected", note="", created_by="", base_url=""):
        jsonld = f"{base_url.rstrip('/')}{concept.jsonld_path()}" if base_url else concept.jsonld_path()
        return cls(
            project=project,
            concept_uuid=concept.uuid,
            subject_slug=concept.subject.slug,
            dictionary_slug=concept.dictionary.slug,
            taxonomy_slug=concept.primary_taxonomy_slug(),
            concept_label=concept.label,
            jsonld_url=jsonld,
            status=status,
            note=note,
            created_by=created_by,
        )


class ScientificActivity(models.Model):
    STATUS_CHOICES = [
        ("planned", "Planificada"),
        ("active", "Activa"),
        ("completed", "Completada"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    project = models.ForeignKey(ProyectoInvestigacion, on_delete=models.CASCADE, related_name="activities")
    capability_slug = models.CharField(max_length=32)
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=80)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    class Meta:
        unique_together = [("project", "slug")]
        ordering = ["title"]

    def __str__(self):
        return self.title


class ScientificResult(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    activity = models.ForeignKey(ScientificActivity, on_delete=models.CASCADE, related_name="results")
    result_type = models.CharField(max_length=32)
    title = models.CharField(max_length=300)
    publish_url = models.URLField(blank=True)
    artifact_url = models.URLField(blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title
