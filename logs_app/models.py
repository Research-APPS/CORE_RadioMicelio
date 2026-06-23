from django.db import models
from django.utils import timezone


class EventLog(models.Model):
    source_id = models.IntegerField(unique=True, db_index=True)
    email = models.TextField(db_index=True)
    timestamp = models.DateTimeField(db_index=True)
    name = models.TextField(db_index=True)
    application = models.TextField(db_index=True)
    orig_id = models.TextField(blank=True, db_column="origId")

    class Meta:
        db_table = "logs_eventlog"
        indexes = [
            models.Index(fields=["application", "timestamp"]),
            models.Index(fields=["name", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.application} / {self.name} @ {self.timestamp}"


class ProjectPlatformLink(models.Model):
    research_project_uuid = models.UUIDField(db_index=True)
    platform_slug = models.CharField(max_length=32, db_index=True)
    is_primary = models.BooleanField(default=True)
    activated_by_username = models.CharField(max_length=150, blank=True)
    activated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["research_project_uuid", "platform_slug"],
                name="logs_unique_project_platform",
            ),
        ]

    def __str__(self):
        return f"{self.research_project_uuid} → {self.platform_slug}"
