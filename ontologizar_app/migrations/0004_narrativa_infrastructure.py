# Generated manually for #ontoNarrativa infrastructure

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ontologizar_app", "0003_alter_conceptrelation_relation_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="conceptdefinition",
            name="kind",
            field=models.CharField(
                choices=[
                    ("definition", "Definición"),
                    ("definition_primary", "Definición (fuente primaria)"),
                    ("definition_institutional", "Definición (fuente institucional)"),
                    ("definition_scholarly", "Definición (estudio académico)"),
                    ("example", "Ejemplo"),
                    ("note", "Nota"),
                    ("reference", "Referencia"),
                ],
                default="definition",
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="conceptrelation",
            name="relation_type",
            field=models.CharField(
                choices=[
                    ("related", "Relacionado"),
                    ("broader", "Más amplio"),
                    ("narrower", "Más estrecho"),
                    ("part_of", "Parte de"),
                    ("has_part", "Tiene como parte a"),
                    ("produces", "Produce"),
                    ("enables", "Permite"),
                    ("participates_in", "Participa en"),
                    ("works_via", "Funciona mediante"),
                    ("evolves_from", "Evoluciona de"),
                    ("evolves_to", "Evoluciona hacia"),
                    ("historically_after", "Viene después de"),
                    ("historically_before", "Viene antes de"),
                    ("appears_in", "Aparece en"),
                    ("invented_by", "Inventado por"),
                    ("used_in", "Se usa en"),
                    ("transmits_to", "Transmite a"),
                    ("may_fail_as", "Puede fallar como"),
                    ("requires_maintenance", "Requiere mantenimiento"),
                    ("may_lead_to", "Puede llevar a"),
                    ("monta_a", "Monta a"),
                    ("escudero_de", "Escudero de"),
                    ("ama_a", "Ama a"),
                    ("ocurre_en", "Ocurre en"),
                    ("advierte_a", "Advierte a"),
                    ("ataca_a", "Ataca a"),
                    ("contiene", "Contiene"),
                    ("padre_de", "Padre de"),
                    ("hijo_de", "Hijo de"),
                    ("enemigo_de", "Enemigo de"),
                    ("amigo_de", "Amigo de"),
                    ("sirve_a", "Sirve a"),
                    ("traiciona_a", "Traiciona a"),
                    ("posee", "Posee"),
                    ("viaja_a", "Viaja a"),
                    ("criado_por", "Criado por"),
                    ("enamorado_de", "Enamorado de"),
                    ("defined_in", "Definido en"),
                    ("interpreted_as", "Interpretado como"),
                    ("develops", "Desarrolla"),
                    ("reinterprets", "Reinterpreta"),
                    ("criticizes", "Critica"),
                    ("distinct_from", "Distinto de"),
                ],
                default="related",
                max_length=32,
            ),
        ),
        migrations.CreateModel(
            name="AttributedRelation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, unique=True,
                    ),
                ),
                (
                    "authority_layer",
                    models.CharField(
                        choices=[
                            ("factual", "Documental"),
                            ("interpretive", "Interpretativa"),
                        ],
                        default="factual",
                        max_length=20,
                    ),
                ),
                ("framework", models.CharField(blank=True, help_text="Slug de perspectiva interpretativa (ej. lectura_politica); vacío en hechos documentales.", max_length=80)),
                ("asserted_by", models.CharField(blank=True, max_length=300)),
                ("source_work", models.CharField(blank=True, max_length=500)),
                ("locator", models.CharField(blank=True, max_length=200)),
                (
                    "confidence",
                    models.CharField(
                        choices=[
                            ("documented", "Documentada"),
                            ("inferred", "Inferida"),
                            ("speculative", "Especulativa"),
                        ],
                        default="documented",
                        max_length=20,
                    ),
                ),
                ("scope", models.CharField(blank=True, max_length=80)),
                (
                    "asserted_by_concept",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="attributions_as_author",
                        to="ontologizar_app.concept",
                    ),
                ),
                (
                    "relation",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attribution",
                        to="ontologizar_app.conceptrelation",
                    ),
                ),
            ],
            options={
                "ordering": ["-relation_id"],
            },
        ),
    ]
