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

    @property
    def activities(self):
        return ScientificActivity.objects.filter(notebook_links__project=self)


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
        unique_together = [("project", "concept_uuid")]

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

    @classmethod
    def upsert_for_concept(cls, project, concept, *, status="selected", note="", created_by="", base_url=""):
        draft = cls.from_concept(
            project, concept, status=status, note=note, created_by=created_by, base_url=base_url,
        )
        marker, _ = cls.objects.update_or_create(
            project=project,
            concept_uuid=concept.uuid,
            defaults={
                "subject_slug": draft.subject_slug,
                "dictionary_slug": draft.dictionary_slug,
                "taxonomy_slug": draft.taxonomy_slug,
                "concept_label": draft.concept_label,
                "jsonld_url": draft.jsonld_url,
                "status": draft.status,
                "note": draft.note,
                "created_by": draft.created_by,
            },
        )
        return marker


class ScientificActivity(models.Model):
    STATUS_CHOICES = [
        ("planned", "Planificada"),
        ("active", "Activa"),
        ("completed", "Completada"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    capability_slug = models.CharField(max_length=32, blank=True)
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def get_notebooks(self):
        return ProyectoInvestigacion.objects.filter(
            activity_links__activity=self,
        ).order_by("titulo")

    def get_notebook_uuids(self) -> list[str]:
        return [str(u) for u in self.notebook_links.values_list("project__uuid", flat=True)]

    def set_notebooks(self, projects: list[ProyectoInvestigacion]) -> bool:
        if not projects:
            return False
        seen = set()
        cleaned = []
        for project in projects:
            if project.uuid not in seen:
                cleaned.append(project)
                seen.add(project.uuid)
        self.notebook_links.all().delete()
        ActivityNotebook.objects.bulk_create([
            ActivityNotebook(activity=self, project=project) for project in cleaned
        ])
        return True

    def get_capability_slugs(self) -> list[str]:
        slugs = list(self.capability_links.values_list("capability_slug", flat=True))
        if slugs:
            return slugs
        return [self.capability_slug] if self.capability_slug else []

    def get_capability_labels(self) -> list[str]:
        from research_app.capability_registry import get_competency

        labels = []
        for slug in self.get_capability_slugs():
            cap = get_competency(slug)
            labels.append(cap["label"] if cap else slug)
        return labels

    def set_capabilities(self, slugs: list[str]) -> bool:
        from research_app.capability_registry import VALID_CAPABILITY_SLUGS

        cleaned = []
        seen = set()
        for slug in slugs:
            if slug in VALID_CAPABILITY_SLUGS and slug not in seen:
                cleaned.append(slug)
                seen.add(slug)
        if not cleaned:
            return False
        removed = set(self.get_capability_slugs()) - set(cleaned)
        if removed:
            self.results.filter(capability_slug__in=removed).delete()
        self.capability_links.all().delete()
        ActivityCapability.objects.bulk_create([
            ActivityCapability(activity=self, capability_slug=slug) for slug in cleaned
        ])
        self.capability_slug = cleaned[0]
        self.save(update_fields=["capability_slug"])
        return True


class ActivityNotebook(models.Model):
    activity = models.ForeignKey(
        ScientificActivity, on_delete=models.CASCADE, related_name="notebook_links",
    )
    project = models.ForeignKey(
        ProyectoInvestigacion, on_delete=models.CASCADE, related_name="activity_links",
    )

    class Meta:
        unique_together = [("activity", "project")]
        ordering = ["project__titulo"]

    def __str__(self):
        return f"{self.activity.title} ↔ {self.project.acron or self.project.titulo}"


class ActivityCapability(models.Model):
    activity = models.ForeignKey(
        ScientificActivity, on_delete=models.CASCADE, related_name="capability_links",
    )
    capability_slug = models.CharField(max_length=32, db_index=True)

    class Meta:
        unique_together = [("activity", "capability_slug")]
        ordering = ["capability_slug"]

    def __str__(self):
        return f"{self.activity.title} → {self.capability_slug}"


class ScientificResult(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    activity = models.ForeignKey(ScientificActivity, on_delete=models.CASCADE, related_name="results")
    capability_slug = models.CharField(max_length=32, db_index=True)
    result_type = models.CharField(max_length=32)
    title = models.CharField(max_length=300)
    publish_url = models.URLField(blank=True)
    artifact_url = models.URLField(blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["capability_slug", "title"]

    def __str__(self):
        return self.title
