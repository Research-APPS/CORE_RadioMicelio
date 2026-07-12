from django.db import migrations, models
import django.db.models.deletion


def copy_activity_notebooks(apps, schema_editor):
    ScientificActivity = apps.get_model("research_app", "ScientificActivity")
    ActivityNotebook = apps.get_model("research_app", "ActivityNotebook")
    for activity in ScientificActivity.objects.exclude(project_id=None):
        ActivityNotebook.objects.get_or_create(activity=activity, project_id=activity.project_id)


class Migration(migrations.Migration):

    dependencies = [
        ("research_app", "0005_scientificresult_capability_slug"),
    ]

    operations = [
        migrations.CreateModel(
            name="ActivityNotebook",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "activity",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notebook_links",
                        to="research_app.scientificactivity",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="activity_links",
                        to="research_app.proyectoinvestigacion",
                    ),
                ),
            ],
            options={
                "ordering": ["project__titulo"],
                "unique_together": {("activity", "project")},
            },
        ),
        migrations.RunPython(copy_activity_notebooks, migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name="scientificactivity",
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name="scientificactivity",
            name="capability_slug",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AlterField(
            model_name="scientificactivity",
            name="slug",
            field=models.SlugField(max_length=80, unique=True),
        ),
        migrations.RemoveField(
            model_name="scientificactivity",
            name="project",
        ),
    ]
