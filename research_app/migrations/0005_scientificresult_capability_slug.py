from django.db import migrations, models


def assign_result_capabilities(apps, schema_editor):
    ScientificResult = apps.get_model("research_app", "ScientificResult")
    ActivityCapability = apps.get_model("research_app", "ActivityCapability")
    for result in ScientificResult.objects.select_related("activity"):
        activity = result.activity
        if result.result_type == "geojson":
            preferred = "geodata"
        elif result.result_type == "jsonld":
            preferred = "ontology"
        elif result.result_type == "report":
            preferred = "analysis"
        else:
            preferred = activity.capability_slug
        slugs = list(
            ActivityCapability.objects.filter(activity=activity).values_list("capability_slug", flat=True)
        )
        if not slugs and activity.capability_slug:
            slugs = [activity.capability_slug]
        if preferred in slugs:
            result.capability_slug = preferred
        elif slugs:
            result.capability_slug = slugs[0]
        else:
            result.capability_slug = "ontology"
        result.save(update_fields=["capability_slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("research_app", "0004_activitycapability"),
    ]

    operations = [
        migrations.AddField(
            model_name="scientificresult",
            name="capability_slug",
            field=models.CharField(db_index=True, default="ontology", max_length=32),
            preserve_default=False,
        ),
        migrations.RunPython(assign_result_capabilities, migrations.RunPython.noop),
    ]
