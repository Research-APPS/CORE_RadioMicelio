from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone


class AiramSession(models.Model):
    KIND_CHOICES = [
        ("temario", "Temario"),
        ("workspace", "Marco de trabajo"),
    ]
    GRANULARITY_CHOICES = [
        ("breve", "Breve"),
        ("normal", "Normal"),
        ("profundo", "Profundo"),
        ("temario", "Temario"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    session_kind = models.CharField(max_length=20, choices=KIND_CHOICES, default="temario")
    title = models.CharField(max_length=300)
    taxonomy = models.ForeignKey(
        "ontologizar_app.Taxonomy",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="airam_sessions",
    )
    root_node = models.ForeignKey(
        "ontologizar_app.TaxonomyNode",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="airam_sessions_root",
    )
    last_node = models.ForeignKey(
        "ontologizar_app.TaxonomyNode",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    project_uuid = models.UUIDField(null=True, blank=True, db_index=True)
    granularity = models.CharField(max_length=20, choices=GRANULARITY_CHOICES, default="normal")
    state = models.JSONField(default=dict, blank=True)
    owner_username = models.CharField(max_length=150, blank=True)
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    is_bookmarked = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    bookmarked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

    @property
    def is_workspace(self) -> bool:
        return self.session_kind == "workspace"


class AiramConceptWeight(models.Model):
    session = models.ForeignKey(
        AiramSession, on_delete=models.CASCADE, related_name="concept_weights",
    )
    concept_uuid = models.UUIDField(db_index=True)
    concept_label = models.CharField(max_length=200, blank=True)
    subject_slug = models.CharField(max_length=80, blank=True)
    dictionary_slug = models.CharField(max_length=80, blank=True)
    taxonomy_slug = models.CharField(max_length=80, blank=True)
    weight = models.PositiveIntegerField(default=0)
    visit_count = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-weight", "-updated_at"]
        unique_together = [("session", "concept_uuid")]

    def __str__(self):
        return f"{self.concept_label or self.concept_uuid} ({self.weight})"
