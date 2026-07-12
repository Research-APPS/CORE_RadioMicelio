from django.db import migrations, models
import django.db.models.deletion


def copy_legacy_capabilities(apps, schema_editor):
    ScientificActivity = apps.get_model("research_app", "ScientificActivity")
    ActivityCapability = apps.get_model("research_app", "ActivityCapability")
    for activity in ScientificActivity.objects.exclude(capability_slug=""):
        ActivityCapability.objects.get_or_create(
            activity=activity,
            capability_slug=activity.capability_slug,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("research_app", "0003_learningmarker_unique_per_concept"),
    ]

    operations = [
        migrations.CreateModel(
            name="ActivityCapability",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("capability_slug", models.CharField(db_index=True, max_length=32)),
                (
                    "activity",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="capability_links",
                        to="research_app.scientificactivity",
                    ),
                ),
            ],
            options={
                "ordering": ["capability_slug"],
                "unique_together": {("activity", "capability_slug")},
            },
        ),
        migrations.RunPython(copy_legacy_capabilities, migrations.RunPython.noop),
    ]
