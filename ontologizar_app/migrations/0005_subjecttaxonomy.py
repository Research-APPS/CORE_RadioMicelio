import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("ontologizar_app", "0004_narrativa_infrastructure"),
    ]

    operations = [
        migrations.CreateModel(
            name="SubjectTaxonomy",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("class", "Taxonomía de clases"),
                            ("property", "Taxonomía de propiedades"),
                            ("thematic", "Taxonomía temática"),
                        ],
                        default="class",
                        max_length=20,
                    ),
                ),
                (
                    "taxonomy_group",
                    models.CharField(
                        blank=True,
                        help_text="Grupo taxonómico: agrupación editorial de árboles.",
                        max_length=80,
                    ),
                ),
                ("is_primary", models.BooleanField(default=False)),
                ("position", models.PositiveIntegerField(default=0)),
                (
                    "subject",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="taxonomy_assignments",
                        to="ontologizar_app.subject",
                    ),
                ),
                (
                    "taxonomy",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subject_assignments",
                        to="ontologizar_app.taxonomy",
                    ),
                ),
            ],
            options={
                "ordering": ["position", "taxonomy__name"],
            },
        ),
        migrations.AddConstraint(
            model_name="subjecttaxonomy",
            constraint=models.UniqueConstraint(
                fields=("subject", "taxonomy", "role"),
                name="unique_subject_taxonomy_role",
            ),
        ),
    ]
