"""
Seed #ontoNarrativa — asignatura Narrativa en /biblioteca.

Crea Subject, Dictionary (ontonarrativa), Taxonomy y vocabulario meta
(tipos de entidad, funciones narrativas). Idempotente.

Uso:
  python manage.py seed_narrativa_ontologia
"""

from django.core.management.base import BaseCommand

from ontologizar_app.models import (
    Concept, ConceptDefinition, ConceptProperty, ConceptRelation,
    Dictionary, Subject, SubjectMaterial, Taxonomy, TaxonomyNode,
)
from ontologizar_app.services.wikipedia import fetch_wikipedia_summary

ONTO_NARRATIVA_TREE = [
    ("Tipos de entidad", [
        "Obra", "Personaje", "Evento", "Lugar", "Objeto", "Grupo", "Autor",
    ]),
    ("Funciones narrativas", [
        "Revelación", "Traición", "Encierro", "Reconocimiento", "Exilio",
        "Duelo", "Boda", "Asesinato", "Descubrimiento",
    ]),
]

ONTO_NARRATIVA_DEFINITIONS = {
    "Obra": (
        "Unidad narrativa completa: novela, obra teatral, película, saga, "
        "campaña de videojuego, ciclo mitológico u otro relato estructurado. "
        "El medio (novela, teatro, cine…) se documenta como propiedad, no como tipo aparte."
    ),
    "Personaje": "Agente ficticio o histórico que participa en una narrativa.",
    "Evento": "Acontecimiento narrativo: batalla, encierro, boda, revelación, misión…",
    "Lugar": "Espacio diegético donde ocurren eventos o habitan personajes.",
    "Objeto": "Artefacto relevante para la trama o el simbolismo narrativo.",
    "Grupo": "Colectivo de personajes: ejército, familia, cofradía, banda…",
    "Autor": "Creador documentado de una obra (escritor, guionista, director…).",
    "Revelación": "Función narrativa: descubrimiento que altera el conocimiento diegético.",
    "Traición": "Función narrativa: quiebre de lealtad o confianza.",
    "Encierro": "Función narrativa: privación de libertad o confinamiento.",
    "Reconocimiento": "Función narrativa: identificación o descubrimiento de identidad.",
    "Exilio": "Función narrativa: expulsión o alejamiento del lugar de origen.",
    "Duelo": "Función narrativa: enfrentamiento formal entre antagonistas.",
    "Boda": "Función narrativa: unión matrimonial o ritual equivalente.",
    "Asesinato": "Función narrativa: muerte causada intencionalmente.",
    "Descubrimiento": "Función narrativa: hallazgo que impulsa la trama.",
}

ENTITY_TYPES = {
    "Obra", "Personaje", "Evento", "Lugar", "Objeto", "Grupo", "Autor",
}

FUNCTION_TYPES = {
    "Revelación", "Traición", "Encierro", "Reconocimiento", "Exilio",
    "Duelo", "Boda", "Asesinato", "Descubrimiento",
}

ONTO_NARRATIVA_PROPERTIES = {
    "Obra": [
        ("concept_type", "narrative_entity"),
        ("preferred_label_en", "Work"),
    ],
    "Personaje": [
        ("concept_type", "narrative_entity"),
        ("preferred_label_en", "Character"),
    ],
    "Evento": [
        ("concept_type", "narrative_entity"),
        ("preferred_label_en", "Event"),
    ],
    "Lugar": [
        ("concept_type", "narrative_entity"),
        ("preferred_label_en", "Place"),
    ],
    "Objeto": [
        ("concept_type", "narrative_entity"),
        ("preferred_label_en", "Object"),
    ],
    "Grupo": [
        ("concept_type", "narrative_entity"),
        ("preferred_label_en", "Group"),
    ],
    "Autor": [
        ("concept_type", "narrative_entity"),
        ("preferred_label_en", "Author"),
    ],
}

ONTO_NARRATIVA_RELATIONS = [
    ("Obra", "Personaje", "contiene"),
    ("Obra", "Evento", "contiene"),
    ("Obra", "Lugar", "contiene"),
    ("Personaje", "Evento", "participa_en"),
    ("Evento", "Lugar", "ocurre_en"),
    ("Autor", "Obra", "related"),
]

SUBJECT_WIKIPEDIA = "Narrativa"


def _concept_in_dict(dictionary, label):
    return Concept.objects.get_or_create(dictionary=dictionary, label=label)[0]


def _link_taxonomy(taxonomy, dictionary, tree, parent=None):
    for item in tree:
        if isinstance(item, tuple):
            label, children = item
        else:
            label, children = item, []
        is_group = label in ("Tipos de entidad", "Funciones narrativas")
        concept = None if is_group else _concept_in_dict(dictionary, label)
        node, _ = TaxonomyNode.objects.get_or_create(
            taxonomy=taxonomy, label=label, parent=parent,
            defaults={"concept": concept},
        )
        if not is_group and node.concept_id != (concept.id if concept else None):
            node.concept = concept
            node.save(update_fields=["concept"])
        if children:
            _link_taxonomy(taxonomy, dictionary, children, parent=node)


def _set_properties(concept, pairs):
    for key, value in pairs:
        ConceptProperty.objects.update_or_create(
            concept=concept, key=key, defaults={"value": value, "value_type": "text"},
        )


def _set_function_type(concept):
    ConceptProperty.objects.update_or_create(
        concept=concept, key="concept_type",
        defaults={"value": "narrative_function", "value_type": "text"},
    )


class Command(BaseCommand):
    help = "Crea asignatura Narrativa (#ontoNarrativa) en /biblioteca"

    def handle(self, *args, **options):
        subject, created_subj = Subject.objects.get_or_create(
            slug="narrativa", defaults={"name": "Narrativa"},
        )
        if created_subj:
            data = fetch_wikipedia_summary(SUBJECT_WIKIPEDIA)
            if data:
                subject.description = data["extract"]
                subject.source_url = data["page_url"]
                subject.save(update_fields=["description", "source_url"])

        SubjectMaterial.objects.update_or_create(
            subject=subject, slug="intro-narrativa",
            defaults={
                "title": "Introducción a la narrativa",
                "summary": "Asignatura #ontoNarrativa",
                "body": (
                    "Vocabulario universal para documentar narrativas en cualquier medio: "
                    "novela, teatro, mitología, cine, cómic, videojuego o relato oral. "
                    "Los corpus concretos (obras, personajes, eventos) viven en diccionarios "
                    "por obra; aquí solo están los tipos y funciones reutilizables."
                ),
            },
        )

        dictionary, created_dict = Dictionary.objects.get_or_create(
            subject=subject, slug="ontonarrativa",
            defaults={
                "name": "Vocabulario narrativo",
                "description": "Base #ontoNarrativa — meta-vocabulario de entidades y funciones",
            },
        )

        taxonomy, created_tax = Taxonomy.objects.get_or_create(
            slug="narrativa",
            defaults={
                "name": "Narrativa (#ontoNarrativa)",
                "description": "Tipos de entidad y funciones narrativas universales.",
            },
        )

        TaxonomyNode.objects.filter(taxonomy=taxonomy).delete()
        _link_taxonomy(taxonomy, dictionary, ONTO_NARRATIVA_TREE)

        concepts = {}
        for label in ENTITY_TYPES | FUNCTION_TYPES:
            concepts[label] = _concept_in_dict(dictionary, label)

        for label, text in ONTO_NARRATIVA_DEFINITIONS.items():
            ConceptDefinition.objects.update_or_create(
                concept=concepts[label], kind="definition",
                defaults={"text": text, "is_active": True},
            )

        for label, pairs in ONTO_NARRATIVA_PROPERTIES.items():
            _set_properties(concepts[label], pairs)

        for label in FUNCTION_TYPES:
            _set_function_type(concepts[label])
            ConceptProperty.objects.update_or_create(
                concept=concepts[label], key="preferred_label_en",
                defaults={"value": label, "value_type": "text"},
            )

        ConceptDefinition.objects.update_or_create(
            concept=concepts["Obra"], kind="note",
            defaults={
                "text": (
                    "Propiedad `medium`: novela | teatro | cine | mitologia | comic | "
                    "videojuego | relato_oral — se aplica a instancias de Obra en corpus concretos."
                ),
                "is_active": True,
            },
        )

        for src, tgt, rel in ONTO_NARRATIVA_RELATIONS:
            ConceptRelation.objects.get_or_create(
                source=concepts[src], target=concepts[tgt], relation_type=rel,
            )

        self.stdout.write(self.style.SUCCESS(
            f"Subject 'narrativa' (nuevo={created_subj}), "
            f"Dictionary 'ontonarrativa' (nuevo={created_dict}), "
            f"Taxonomy 'narrativa' (nuevo={created_tax}), "
            f"{len(concepts)} conceptos meta."
        ))
