"""
Conecta el corpus del Quijote (#ontoNarrativa piloto).

Añade instancias documentales mínimas al diccionario quijote, alinea
concept_type con el meta-vocabulario ontonarrativa y crea una interpretación
de demostración con AttributedRelation.

Requiere: seed_quijote_ontologia, seed_narrativa_ontologia

Uso:
  python manage.py align_quijote_narrativa
"""

from django.core.management.base import BaseCommand

from ontologizar_app.models import Concept, ConceptProperty, Dictionary, Subject
from ontologizar_app.services.attributed_relations import create_attributed_relation


QUIJOTE_OBRA = "Don Quijote de la Mancha"
PERSONAJES = [
    ("Don Quijote", "Personaje"),
    ("Sancho Panza", "Personaje"),
    ("Dulcinea del Toboso", "Personaje"),
]

TAXONOMY_BUCKET_TYPES = {
    "Personajes": "Personaje",
    "Lugares": "Lugar",
    "Objetos": "Objeto",
    "Eventos": "Evento",
    "Temas": "narrative_function",
}


def _set_prop(concept, key, value):
    ConceptProperty.objects.update_or_create(
        concept=concept, key=key, defaults={"value": value, "value_type": "text"},
    )


class Command(BaseCommand):
    help = "Alinea el diccionario quijote con #ontoNarrativa (corpus piloto)"

    def handle(self, *args, **options):
        try:
            meta = Dictionary.objects.get(subject__slug="narrativa", slug="ontonarrativa")
        except Dictionary.DoesNotExist:
            self.stderr.write("Ejecuta primero: python manage.py seed_narrativa_ontologia")
            return

        lengua = Subject.objects.filter(slug="lengua").first()
        if not lengua:
            self.stderr.write("Ejecuta primero: python manage.py seed_quijote_ontologia")
            return

        quijote_dict = Dictionary.objects.filter(subject=lengua, slug="quijote").first()
        if not quijote_dict:
            self.stderr.write("Ejecuta primero: python manage.py seed_quijote_ontologia")
            return

        meta_types = {c.label: c for c in meta.concepts.all()}

        obra, _ = Concept.objects.get_or_create(
            dictionary=quijote_dict, label=QUIJOTE_OBRA,
        )
        _set_prop(obra, "concept_type", "work")
        _set_prop(obra, "medium", "novela")
        _set_prop(obra, "authority_layer", "factual")

        for label, ctype in PERSONAJES:
            concept, created = Concept.objects.get_or_create(
                dictionary=quijote_dict, label=label,
            )
            _set_prop(concept, "concept_type", ctype)
            _set_prop(concept, "authority_layer", "factual")
            create_attributed_relation(
                obra, concept, "contiene",
                authority_layer="factual",
                source_work="El ingenioso hidalgo Don Quijote de la Mancha",
                locator="corpus completo",
                scope="narrative_analysis",
            )

        don_q = Concept.objects.filter(dictionary=quijote_dict, label="Don Quijote").first()
        sancho = Concept.objects.filter(dictionary=quijote_dict, label="Sancho Panza").first()
        if don_q and sancho:
            create_attributed_relation(
                sancho, don_q, "escudero_de",
                authority_layer="factual",
                source_work="El ingenioso hidalgo Don Quijote de la Mancha",
                locator="relación documental canónica",
            )

        reconocimiento = meta_types.get("Reconocimiento")
        if don_q and reconocimiento:
            create_attributed_relation(
                don_q, reconocimiento, "interpreted_as",
                authority_layer="interpretive",
                framework="critica_literaria",
                asserted_by="Material demo CORE Radio Micelio",
                source_work="Introducción a la novela (interpretación de demostración)",
                locator="nota editorial",
                confidence="documented",
                scope="narrative_analysis",
            )

        tagged = sum(1 for c in quijote_dict.concepts.all() if c.properties.filter(key="concept_type").exists())
        self.stdout.write(self.style.SUCCESS(
            f"Corpus quijote alineado: obra '{QUIJOTE_OBRA}', "
            f"{len(PERSONAJES)} personajes, {tagged} conceptos con concept_type."
        ))
