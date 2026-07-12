from django.db import migrations, models


def dedupe_learning_markers(apps, schema_editor):
    LearningMarker = apps.get_model("research_app", "LearningMarker")
    seen = set()
    to_delete = []
    for marker in LearningMarker.objects.order_by("-created_at", "-id"):
        key = (marker.project_id, str(marker.concept_uuid))
        if key in seen:
            to_delete.append(marker.pk)
        else:
            seen.add(key)
    if to_delete:
        LearningMarker.objects.filter(pk__in=to_delete).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("research_app", "0002_scientificactivity_and_more"),
    ]

    operations = [
        migrations.RunPython(dedupe_learning_markers, migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name="learningmarker",
            unique_together={("project", "concept_uuid")},
        ),
    ]
