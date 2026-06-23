from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ontologizar_app", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="subject",
            name="source_url",
            field=models.URLField(blank=True, help_text="Fuente externa (p. ej. Wikipedia)"),
        ),
        migrations.AddField(
            model_name="subjectmaterial",
            name="body",
            field=models.TextField(blank=True, help_text="Texto wiki del material"),
        ),
    ]
