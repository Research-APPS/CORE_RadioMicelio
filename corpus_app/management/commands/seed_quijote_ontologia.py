"""
Management command: seed_quijote_ontologia

Crea el esqueleto de Subject/Dictionary/Taxonomy/TaxonomyNode para que "El
Quijote" aparezca como un apartado navegable en /biblioteca/, igual que
hongos/emociones/neurociencia — sin ninguna vista ni plantilla nueva (la
navegación pública de cms_app ya es genérica sobre estos modelos).

Idempotente (get_or_create): correr varias veces no duplica nada.

Uso:
  python manage.py seed_quijote_ontologia
"""

from django.core.management.base import BaseCommand

from ontologizar_app.models import Dictionary, Subject, Taxonomy, TaxonomyNode

NODOS_RAIZ = ["Personajes", "Lugares", "Objetos", "Eventos", "Temas"]


class Command(BaseCommand):
    help = "Crea Subject/Dictionary/Taxonomy 'El Quijote' con nodos raíz por tipo de entidad"

    def handle(self, *args, **options):
        subject, created_subject = Subject.objects.get_or_create(
            slug="lengua", defaults={"name": "Lengua y Literatura"}
        )
        dictionary, created_dict = Dictionary.objects.get_or_create(
            subject=subject, slug="quijote", defaults={"name": "El Quijote"}
        )
        taxonomy, created_tax = Taxonomy.objects.get_or_create(
            slug="quijote", defaults={"name": "El Quijote"}
        )

        creados = 0
        for label in NODOS_RAIZ:
            _, created = TaxonomyNode.objects.get_or_create(
                taxonomy=taxonomy, label=label, parent=None, concept=None
            )
            if created:
                creados += 1

        self.stdout.write(self.style.SUCCESS(
            f"Subject 'lengua' (nuevo={created_subject}), "
            f"Dictionary 'quijote' (nuevo={created_dict}), "
            f"Taxonomy 'quijote' (nuevo={created_tax}), "
            f"{creados} nodos raíz nuevos de {len(NODOS_RAIZ)} esperados."
        ))
