# Generated manually for Phase 2b AIRAM Workspace

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("airam_app", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="airamsession",
            name="project_uuid",
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="airamsession",
            name="session_kind",
            field=models.CharField(
                choices=[("temario", "Temario"), ("workspace", "Marco de trabajo")],
                default="temario",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="airamsession",
            name="root_node",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="airam_sessions_root",
                to="ontologizar_app.taxonomynode",
            ),
        ),
        migrations.AlterField(
            model_name="airamsession",
            name="taxonomy",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="airam_sessions",
                to="ontologizar_app.taxonomy",
            ),
        ),
        migrations.CreateModel(
            name="AiramConceptWeight",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("concept_uuid", models.UUIDField(db_index=True)),
                ("concept_label", models.CharField(blank=True, max_length=200)),
                ("subject_slug", models.CharField(blank=True, max_length=80)),
                ("dictionary_slug", models.CharField(blank=True, max_length=80)),
                ("taxonomy_slug", models.CharField(blank=True, max_length=80)),
                ("weight", models.PositiveIntegerField(default=0)),
                ("visit_count", models.PositiveIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="concept_weights",
                        to="airam_app.airamsession",
                    ),
                ),
            ],
            options={
                "ordering": ["-weight", "-updated_at"],
                "unique_together": {("session", "concept_uuid")},
            },
        ),
    ]
