"""
Seed #ontoNarrativa — asignatura Narrativa en /biblioteca.

Crea Subject, Dictionary (ontonarrativa) y cuatro taxonomías agrupadas por
taxonomy_group: estructural, arquetípico, temático y simbólico. Idempotente.

Uso:
  python manage.py seed_narrativa_ontologia
"""

from django.core.management.base import BaseCommand

from ontologizar_app.models import (
    Concept, ConceptDefinition, ConceptProperty, ConceptRelation,
    Dictionary, Subject, SubjectMaterial, Taxonomy, TaxonomyNode,
)
from ontologizar_app.services.wikipedia import fetch_wikipedia_summary
from ontologizar_app.services.subject_taxonomy import assign_subject_taxonomy

# Taxonomía estructural: tipos de entidad + funciones dramáticas
ESTRUCTURAL_TREE = [
    ("Tipos de entidad", [
        "Obra", "Personaje", "Evento", "Lugar", "Objeto", "Grupo", "Autor",
    ]),
    ("Funciones narrativas", [
        "Conflicto", "Transformación", "Reconocimiento",
    ]),
]

# Taxonomía arquetípica: figuras recurrentes (no listas cerradas de arquetipos)
ARQUETIPICO_TREE = [
    ("Figuras narrativas", [
        "Héroe idealista", "Mentor", "Antagonista", "Trickster",
        "Doncella", "Guardián", "Sombra",
    ]),
]

# Taxonomía temática: motivos narrativos
TEMATICO_TREE = [
    ("Motivos", [
        "Revelación", "Traición", "Encierro", "Exilio",
        "Duelo", "Boda", "Asesinato", "Descubrimiento",
    ]),
]

# Taxonomía simbólica: tipo meta + ejemplos universales
SIMBOLICO_TREE = [
    ("Símbolos", [
        "Símbolo", "Camino", "Agua", "Fuego",
    ]),
]

TAXONOMY_SPECS = [
    {
        "slug": "narrativa",
        "name": "Narrativa — estructural (#ontoNarrativa)",
        "description": "Tipos de entidad y funciones narrativas universales.",
        "tree": ESTRUCTURAL_TREE,
        "taxonomy_group": "estructural",
        "is_primary": True,
        "position": 0,
    },
    {
        "slug": "narrativa-arquetipico",
        "name": "Narrativa — figuras (#ontoNarrativa)",
        "description": "Figuras narrativas recurrentes entre obras y medios.",
        "tree": ARQUETIPICO_TREE,
        "taxonomy_group": "arquetipico",
        "is_primary": False,
        "position": 1,
    },
    {
        "slug": "narrativa-tematico",
        "name": "Narrativa — motivos (#ontoNarrativa)",
        "description": "Motivos narrativos reutilizables.",
        "tree": TEMATICO_TREE,
        "taxonomy_group": "tematico",
        "is_primary": False,
        "position": 2,
    },
    {
        "slug": "narrativa-simbolico",
        "name": "Narrativa — símbolos (#ontoNarrativa)",
        "description": "Símbolos y elementos simbólicos universales.",
        "tree": SIMBOLICO_TREE,
        "taxonomy_group": "simbolico",
        "is_primary": False,
        "position": 3,
    },
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
    "Conflicto": "Función narrativa: tensión o oposición que impulsa la trama.",
    "Transformación": "Función narrativa: cambio significativo en personaje, situación o significado.",
    "Reconocimiento": "Función narrativa: identificación o descubrimiento de identidad.",
    "Héroe idealista": "Figura narrativa: agente que persigue un ideal a pesar del coste personal.",
    "Mentor": "Figura narrativa: guía o maestro que orienta al protagonista.",
    "Antagonista": "Figura narrativa: fuerza opuesta que obstaculiza el objetivo central.",
    "Trickster": "Figura narrativa: agente ambiguo que altera reglas o expectativas.",
    "Doncella": "Figura narrativa: personaje asociado a pureza, deseo o rescate.",
    "Guardián": "Figura narrativa: protector de umbral, secreto o territorio.",
    "Sombra": "Figura narrativa: aspecto reprimido o amenaza vinculada al protagonista.",
    "Revelación": "Motivo narrativo: descubrimiento que altera el conocimiento diegético.",
    "Traición": "Motivo narrativo: quiebre de lealtad o confianza.",
    "Encierro": "Motivo narrativo: privación de libertad o confinamiento.",
    "Exilio": "Motivo narrativo: expulsión o alejamiento del lugar de origen.",
    "Duelo": "Motivo narrativo: enfrentamiento formal entre antagonistas.",
    "Boda": "Motivo narrativo: unión matrimonial o ritual equivalente.",
    "Asesinato": "Motivo narrativo: muerte causada intencionalmente.",
    "Descubrimiento": "Motivo narrativo: hallazgo que impulsa la trama.",
    "Símbolo": "Elemento narrativo que remite a un significado más amplio que su literalidad.",
    "Camino": "Símbolo narrativo: travesía, destino o proceso de transformación.",
    "Agua": "Símbolo narrativo: purificación, vida, muerte o paso entre mundos.",
    "Fuego": "Símbolo narrativo: pasión, destrucción, renovación o revelación.",
}

ENTITY_TYPES = {
    "Obra", "Personaje", "Evento", "Lugar", "Objeto", "Grupo", "Autor",
}
STRUCTURAL_FUNCTIONS = {"Conflicto", "Transformación", "Reconocimiento"}
FIGURE_TYPES = {
    "Héroe idealista", "Mentor", "Antagonista", "Trickster",
    "Doncella", "Guardián", "Sombra",
}
MOTIF_TYPES = {
    "Revelación", "Traición", "Encierro", "Exilio",
    "Duelo", "Boda", "Asesinato", "Descubrimiento",
}
SYMBOL_TYPES = {"Símbolo", "Camino", "Agua", "Fuego"}

ALL_LABELS = ENTITY_TYPES | STRUCTURAL_FUNCTIONS | FIGURE_TYPES | MOTIF_TYPES | SYMBOL_TYPES

GROUP_NODE_LABELS = frozenset({
    "Tipos de entidad", "Funciones narrativas", "Figuras narrativas",
    "Motivos", "Símbolos",
})

ONTO_NARRATIVA_PROPERTIES = {
    "Obra": [("concept_type", "narrative_entity"), ("preferred_label_en", "Work")],
    "Personaje": [("concept_type", "narrative_entity"), ("preferred_label_en", "Character")],
    "Evento": [("concept_type", "narrative_entity"), ("preferred_label_en", "Event")],
    "Lugar": [("concept_type", "narrative_entity"), ("preferred_label_en", "Place")],
    "Objeto": [("concept_type", "narrative_entity"), ("preferred_label_en", "Object")],
    "Grupo": [("concept_type", "narrative_entity"), ("preferred_label_en", "Group")],
    "Autor": [("concept_type", "narrative_entity"), ("preferred_label_en", "Author")],
}

ONTO_NARRATIVA_RELATIONS = [
    ("Obra", "Personaje", "contiene"),
    ("Obra", "Evento", "contiene"),
    ("Obra", "Lugar", "contiene"),
    ("Personaje", "Evento", "participa_en"),
    ("Evento", "Lugar", "ocurre_en"),
    ("Autor", "Obra", "related"),
    ("Héroe idealista", "Conflicto", "related"),
    ("Mentor", "Transformación", "related"),
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
        is_group = label in GROUP_NODE_LABELS
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


def _set_concept_type(concept, value):
    ConceptProperty.objects.update_or_create(
        concept=concept, key="concept_type",
        defaults={"value": value, "value_type": "text"},
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
                    "Las taxonomías agrupan tipos de entidad, figuras, motivos y símbolos; "
                    "los corpus concretos (obras, personajes, eventos) viven en diccionarios por obra."
                ),
            },
        )

        dictionary, created_dict = Dictionary.objects.get_or_create(
            subject=subject, slug="ontonarrativa",
            defaults={
                "name": "Vocabulario narrativo",
                "description": "Base #ontoNarrativa — meta-vocabulario de entidades, figuras, motivos y símbolos",
            },
        )

        created_taxonomies = []
        for spec in TAXONOMY_SPECS:
            taxonomy, created_tax = Taxonomy.objects.get_or_create(
                slug=spec["slug"],
                defaults={"name": spec["name"], "description": spec["description"]},
            )
            if not created_tax:
                taxonomy.name = spec["name"]
                taxonomy.description = spec["description"]
                taxonomy.save(update_fields=["name", "description"])
            TaxonomyNode.objects.filter(taxonomy=taxonomy).delete()
            _link_taxonomy(taxonomy, dictionary, spec["tree"])
            assign_subject_taxonomy(
                subject, taxonomy,
                role="class",
                taxonomy_group=spec["taxonomy_group"],
                is_primary=spec["is_primary"],
                position=spec["position"],
            )
            created_taxonomies.append((spec["slug"], created_tax))

        concepts = {label: _concept_in_dict(dictionary, label) for label in ALL_LABELS}

        for label, text in ONTO_NARRATIVA_DEFINITIONS.items():
            ConceptDefinition.objects.update_or_create(
                concept=concepts[label], kind="definition",
                defaults={"text": text, "is_active": True},
            )

        for label, pairs in ONTO_NARRATIVA_PROPERTIES.items():
            _set_properties(concepts[label], pairs)

        for label in STRUCTURAL_FUNCTIONS:
            _set_concept_type(concepts[label], "narrative_function")
            _set_properties(concepts[label], [("preferred_label_en", label)])

        for label in FIGURE_TYPES:
            _set_concept_type(concepts[label], "narrative_figure")
            _set_properties(concepts[label], [("preferred_label_en", label)])

        for label in MOTIF_TYPES:
            _set_concept_type(concepts[label], "narrative_motif")
            _set_properties(concepts[label], [("preferred_label_en", label)])

        for label in SYMBOL_TYPES:
            ctype = "narrative_symbol" if label == "Símbolo" else "narrative_symbol_instance"
            _set_concept_type(concepts[label], ctype)
            _set_properties(concepts[label], [("preferred_label_en", label)])

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

        tax_summary = ", ".join(f"{slug} (nuevo={created})" for slug, created in created_taxonomies)
        self.stdout.write(self.style.SUCCESS(
            f"Subject 'narrativa' (nuevo={created_subj}), "
            f"Dictionary 'ontonarrativa' (nuevo={created_dict}), "
            f"taxonomías: {tax_summary}, "
            f"{len(concepts)} conceptos meta."
        ))
