from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone


class AiramSession(models.Model):
    GRANULARITY_CHOICES = [
        ("breve", "Breve"),
        ("normal", "Normal"),
        ("profundo", "Profundo"),
        ("temario", "Temario"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    title = models.CharField(max_length=300)
    taxonomy = models.ForeignKey(
        "ontologizar_app.Taxonomy", on_delete=models.CASCADE, related_name="airam_sessions",
    )
    root_node = models.ForeignKey(
        "ontologizar_app.TaxonomyNode", on_delete=models.CASCADE, related_name="airam_sessions_root",
    )
    last_node = models.ForeignKey(
        "ontologizar_app.TaxonomyNode",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
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
