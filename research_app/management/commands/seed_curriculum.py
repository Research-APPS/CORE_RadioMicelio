from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone

from ontologizar_app.models import (
    Concept, ConceptDefinition, ConceptProperty, ConceptRelation,
    Dictionary, Subject, SubjectMaterial, Taxonomy, TaxonomyNode,
)
from ontologizar_app.services.wikipedia import fetch_wikipedia_summary
from logs_app.models import EventLog, ProjectPlatformLink
from research_app.models import (
    LearningMarker, ProyectoInvestigacion, ProjectCurriculumDeclaration,
    ScientificActivity, ScientificResult,
)

OLDS = ["DIDONE", "DIZO", "VACIADO", "SONARE"]

# Ontología híbrida #ontoHongo — navegable desde AIRAM y la biblioteca
ONTOHONGO_TREE = [
    ("¿Qué es un hongo?", []),
    ("Anatomía fúngica", [
        "Hifa",
        "Micelio",
        ("Conidióforo", ["Conidio", "Espora"]),
        "Basidio",
        "Ascocarpo",
        "Cuerpo fructífero",
    ]),
    ("Ciclo vital", ["Germinación", "Crecimiento", "Fructificación"]),
    ("Ecología", ["Saprófito", "Micorrízico", "Parásito", "Bosque"]),
    ("Taxonomía", ["Ascomycota", "Basidiomycota", "Mucoromycota"]),
    ("Hongos ibéricos", []),
    ("Aplicaciones", ["Alimentación", "Medicina", "Biotecnología", "Dispersión"]),
]

ONTOHONGO_DEFINITIONS = {
    "¿Qué es un hongo?": "Organismo eucariota que se alimenta por absorción; muchos forman hifas y esporas.",
    "Hifa": "Filamento microscópico que crece y ramifica; unidad básica del cuerpo fúngico.",
    "Micelio": "Red de hifas que forma el cuerpo vegetativo del hongo.",
    "Conidióforo": "Estructura aérea que porta conidios en la reproducción asexual.",
    "Conidio": "Espora asexual producida en el ápice del conidióforo.",
    "Espora": "Célula reproductiva que permite dispersar y colonizar nuevos sustratos.",
    "Dispersión": "Mecanismos — viento, agua, animales — que alejan las esporas del individuo madre.",
    "Basidio": "Célula reproductiva típica de basidiomicetos donde se forman basidiosporas.",
    "Bosque": "Ecosistema forestal donde proliferan hongos saprófitos y micorrízicos.",
}

# Ontología híbrida #ontoEmo — inspirada en MFOEM/Emotion Ontology y ONYX (anotación)
ONTOEMO_TREE = [
    ("Emoción", [
        ("Tipos básicos", ["Alegría", "Tristeza", "Miedo", "Ira", "Asco", "Sorpresa"]),
        ("Estados de ánimo", ["Melancolía", "Euforia", "Calma", "Ansiedad"]),
        ("Sentimientos", ["Nostalgia", "Empatía", "Vergüenza"]),
    ]),
    ("Dimensiones (EmotionML / ONYX)", ["Valencia", "Activación", "Intensidad", "Dominancia"]),
    ("Contexto expresivo", [
        "Causa / estímulo",
        "Personaje afectado",
        "Expresión corporal",
        "Escena narrativa",
    ]),
]

ONTOEMO_DEFINITIONS = {
    "Emoción": "Experiencia subjetiva breve ante un estímulo significativo; distinta del estado de ánimo y del sentimiento.",
    "Alegría": "Emoción de valencia positiva asociada a recompensa y apertura social.",
    "Tristeza": "Emoción de valencia negativa ligada a pérdida o fracaso.",
    "Melancolía": "Estado de ánimo de valencia negativa baja, con activación reducida y componente reflexivo.",
    "Valencia": (
        "Dimensión que sitúa la experiencia afectiva entre agradable y desagradable "
        "(valencia hedónica en psicología y neurociencia)."
    ),
    "Activación": "Dimensión de energía o calma del estado afectivo.",
    "Intensidad": "Grado de fuerza con que se vive una emoción (útil para anotar escenas con ONYX).",
    "Escena narrativa": "Unidad de análisis: un poema, una escena radiofónica o un fragmento con emoción detectable.",
}

ONTOEMO_RELATIONS = [
    ("Alegría", "Valencia", "related"),
    ("Tristeza", "Valencia", "related"),
    ("Melancolía", "Tristeza", "narrower"),
    ("Melancolía", "Nostalgia", "related"),
    ("Intensidad", "Activación", "related"),
    ("Escena narrativa", "Causa / estímulo", "related"),
]

# Ontología #ontoNeuro — vocabulario inspirado en NeuroLex / NIFSTD
ONTONEURO_TREE = [
    ("Sistema nervioso", [
        "Neurona",
        "Sinapsis",
        ("Regiones cerebrales", ["Amígdala", "Hipocampo", "Corteza prefrontal"]),
        ("Sistemas", ["Sistema límbico", "Tronco encefálico"]),
        ("Neurotransmisores", ["Dopamina", "Serotonina", "Noradrenalina"]),
    ]),
    ("Correlatos de la emoción", [
        "Procesamiento afectivo",
        "Memoria emocional",
        "Respuesta al estrés",
    ]),
]

ONTOQUIM_TREE = [
    ("Química", [
        ("Estructura atómica", [
            "Electrones de valencia",
            ("Valencia química", ["Regla del octeto", "Estado de oxidación"]),
            "Enlace químico",
        ]),
    ]),
]

ONTOQUIM_DEFINITIONS = {
    "Química": "Ciencia que estudia la materia, su composición, estructura y transformaciones.",
    "Estructura atómica": "Organización de protones, neutrones y electrones en el átomo.",
    "Electrones de valencia": "Electrones del último nivel energético; determinan la capacidad de enlace.",
    "Valencia química": (
        "Capacidad de un átomo para formar enlaces químicos con otros átomos. "
        "Históricamente se asoció al número de enlaces que podía establecer; "
        "en la formulación moderna se relaciona con la configuración electrónica "
        "y con el estado de oxidación en compuestos."
    ),
    "Regla del octeto": "Tendencia de los átomos ligeros a completar ocho electrones de valencia en enlaces.",
    "Estado de oxidación": "Carga formal que tendría un átomo si todos sus enlaces fueran iónicos.",
    "Enlace químico": "Interacción que mantiene unidos a los átomos en una molécula o red cristalina.",
}

ONTOQUIM_NOTE_VALENCIA = (
    "La regla del octeto explica muchos compuestos de H, O, N y C, pero admite excepciones "
    "(p. ej. compuestos de boro o fósforo hipervalente). "
    "Distinguir valencia clásica del estado de oxidación evita confusiones en nomenclatura."
)

ONTOQUIM_REFERENCES_VALENCIA = [
    "IUPAC Gold Book — valence | https://goldbook.iupac.org/terms/view/V06588 | referencia_terminologica | IUPAC | terminological_reference",
    "IUPAC Gold Book — oxidation number | https://goldbook.iupac.org/terms/view/O04365 | referencia_terminologica | IUPAC | terminological_reference",
    "NIST Chemistry WebBook | https://webbook.nist.gov/chemistry/ | dataset | NIST | dataset",
]

ONTOQUIM_RELATIONS = [
    ("Valencia química", "Electrones de valencia", "related"),
    ("Valencia química", "Regla del octeto", "related"),
    ("Valencia química", "Estado de oxidación", "related"),
    ("Valencia química", "Enlace químico", "related"),
    ("Regla del octeto", "Valencia química", "narrower"),
    ("Estado de oxidación", "Valencia química", "narrower"),
]

ONTONEURO_DEFINITIONS = {
    "Neurona": "Célula nerviosa que transmite señales eléctricas y químicas.",
    "Sinapsis": "Conexión entre neuronas donde se libera un neurotransmisor.",
    "Sistema límbico": "Conjunto de estructuras implicadas en emoción, motivación y memoria.",
    "Amígdala": "Región clave en la detección de amenazas y emociones intensas.",
    "Dopamina": "Neurotransmisor asociado a recompensa, motivación y placer.",
    "Procesamiento afectivo": "Circuitos que integran estímulo, valoración y respuesta emocional.",
}


SUBJECT_WIKIPEDIA = {
    "ciencias-naturales": "Ciencias_naturales",
    "micologia": "Micología",
    "musica": "Música",
    "historia": "Historia",
    "geografia": "Geografía",
    "lengua": "Literatura",
    "emociones": "Emoción",
    "neurociencia": "Neurociencia",
    "quimica": "Química",
}


def seed_subject_wiki(subject: Subject) -> bool:
    title = SUBJECT_WIKIPEDIA.get(subject.slug)
    if not title:
        return False
    data = fetch_wikipedia_summary(title)
    if not data:
        return False
    subject.description = data["extract"]
    subject.source_url = data["page_url"]
    subject.save(update_fields=["description", "source_url"])
    return True


def concept_in_dict(dictionary, label):
    return Concept.objects.get_or_create(dictionary=dictionary, label=label)[0]


def link_taxonomy(taxonomy, dictionary, tree, parent=None):
    """tree: list of (label, children) or simple label strings"""
    for item in tree:
        if isinstance(item, tuple):
            label, children = item
        else:
            label, children = item, []
        c = concept_in_dict(dictionary, label)
        node = TaxonomyNode.objects.create(taxonomy=taxonomy, label=label, concept=c, parent=parent)
        if children:
            link_taxonomy(taxonomy, dictionary, children, parent=node)


def seed_ontology(taxonomy, dictionary, tree, definitions=None, relations=None):
    TaxonomyNode.objects.filter(taxonomy=taxonomy).delete()
    link_taxonomy(taxonomy, dictionary, tree)
    concepts = {c.label: c for c in Concept.objects.filter(dictionary=dictionary)}
    for label, text in (definitions or {}).items():
        if label in concepts:
            ConceptDefinition.objects.get_or_create(
                concept=concepts[label], kind="definition",
                defaults={"text": text, "is_active": True},
            )

    def rel(a, b, kind="related"):
        if a in concepts and b in concepts:
            ConceptRelation.objects.get_or_create(source=concepts[a], target=concepts[b], relation_type=kind)

    for item in relations or []:
        rel(*item)
    return concepts


def seed_ontoquim(taxonomy, dictionary):
    concepts = seed_ontology(
        taxonomy, dictionary, ONTOQUIM_TREE, ONTOQUIM_DEFINITIONS, ONTOQUIM_RELATIONS,
    )
    valencia = concepts.get("Valencia química")
    if valencia:
        ConceptDefinition.objects.get_or_create(
            concept=valencia, kind="note",
            defaults={"text": ONTOQUIM_NOTE_VALENCIA, "is_active": True},
        )
        ConceptDefinition.objects.filter(concept=valencia, kind="reference").delete()
        for ref_line in ONTOQUIM_REFERENCES_VALENCIA:
            ConceptDefinition.objects.create(
                concept=valencia, kind="reference", text=ref_line, is_active=True,
            )
        ConceptProperty.objects.get_or_create(
            concept=valencia, key="doi",
            defaults={"value": "10.1351/goldbook.V06588"},
        )
        ConceptProperty.objects.get_or_create(
            concept=valencia, key="source_url",
            defaults={"value": "https://goldbook.iupac.org/terms/view/V06588"},
        )
        ConceptProperty.objects.get_or_create(
            concept=valencia, key="provider",
            defaults={"value": "IUPAC"},
        )
    return concepts


def seed_ontohongo(taxonomy, dictionary):
    return seed_ontology(
        taxonomy, dictionary, ONTOHONGO_TREE, ONTOHONGO_DEFINITIONS,
        [
            ("Hifa", "Micelio", "partOf"),
            ("Conidióforo", "Conidio", "narrower"),
            ("Conidióforo", "Espora", "related"),
            ("Conidio", "Espora", "narrower"),
            ("Espora", "Dispersión", "related"),
            ("Dispersión", "Bosque", "related"),
            ("Micelio", "Bosque", "partOf"),
        ],
    )


class Command(BaseCommand):
    help = "Seed currículo escolar + biblioteca semántica transversal"

    def handle(self, *args, **options):
        call_command("ensure_cms_user")
        base = "http://127.0.0.1:8003"

        ProyectoInvestigacion.objects.filter(acron__in=OLDS).delete()
        ConceptRelation.objects.all().delete()

        musica, _ = Subject.objects.get_or_create(slug="musica", defaults={"name": "Música"})
        ciencias, _ = Subject.objects.get_or_create(slug="ciencias-naturales", defaults={"name": "Ciencias Naturales"})
        micologia, _ = Subject.objects.get_or_create(slug="micologia", defaults={"name": "Micología"})
        emociones_subj, _ = Subject.objects.get_or_create(slug="emociones", defaults={"name": "Emociones"})
        neurociencia, _ = Subject.objects.get_or_create(slug="neurociencia", defaults={"name": "Neurociencia"})
        quimica, _ = Subject.objects.get_or_create(slug="quimica", defaults={"name": "Química"})
        historia, _ = Subject.objects.get_or_create(slug="historia", defaults={"name": "Historia"})
        geo, _ = Subject.objects.get_or_create(slug="geografia", defaults={"name": "Geografía"})
        lengua, _ = Subject.objects.get_or_create(slug="lengua", defaults={"name": "Lengua y Literatura"})

        SubjectMaterial.objects.update_or_create(
            subject=micologia, slug="intro-micologia",
            defaults={
                "title": "Introducción a la micología",
                "summary": "Asignatura #ontoHongo",
                "body": (
                    "La micología estudia los hongos: organismos eucariotas que descomponen materia orgánica, "
                    "forman micelios y liberan esporas. En CORE Radio Micelio esta asignatura es el laboratorio "
                    "para navegar la ontología híbrida #ontoHongo con AIRAM."
                ),
            },
        )
        SubjectMaterial.objects.update_or_create(
            subject=ciencias, slug="unidad-hongos",
            defaults={
                "title": "Unidad 3: Los hongos",
                "summary": "Los hongos en el currículo de Ciencias Naturales",
                "body": (
                    "Los hongos no son plantas ni animales: pertenecen al reino Fungi. Observan estructuras como "
                    "hifas, micelios y esporas, y su papel en ecosistemas forestales."
                ),
            },
        )
        SubjectMaterial.objects.update_or_create(
            subject=emociones_subj, slug="intro-emociones",
            defaults={
                "title": "Introducción a las emociones",
                "summary": "Asignatura #ontoEmo",
                "body": (
                    "Ontología para clasificar emociones con categorías inspiradas en MFOEM/Emotion Ontology "
                    "y dimensiones tipo EmotionML/ONYX. "
                    "Las relaciones entre conceptos se limitan a esta ontología hasta validación científica."
                ),
            },
        )
        SubjectMaterial.objects.update_or_create(
            subject=neurociencia, slug="intro-neuro",
            defaults={
                "title": "Sistema nervioso y emoción",
                "summary": "Asignatura #ontoNeuro",
                "body": (
                    "Vocabulario inspirado en NeuroLex/NIFSTD: neuronas, regiones cerebrales, neurotransmisores "
                    "y circuitos afectivos. Ontología independiente: sin enlaces automáticos a otras asignaturas "
                    "hasta que exista base científica explícita."
                ),
            },
        )
        SubjectMaterial.objects.update_or_create(
            subject=quimica, slug="intro-quimica",
            defaults={
                "title": "Introducción a la química",
                "summary": "Asignatura #ontoQuim",
                "body": (
                    "La química estudia la materia y sus transformaciones. "
                    "En CORE Radio Micelio esta asignatura introduce el vocabulario #ontoQuim "
                    "con procedencia científica formal (IUPAC, NIST) y definiciones editoriales propias."
                ),
            },
        )
        SubjectMaterial.objects.get_or_create(subject=lengua, slug="poesia-emociones", defaults={
            "title": "La poesía y las emociones",
            "summary": "Material CMS",
            "body": (
                "Las escenas poéticas pueden describir emociones con vocabulario preciso: "
                "valencia, intensidad, melancolía, nostalgia, etc."
            ),
        })

        for subj in (musica, ciencias, micologia, emociones_subj, neurociencia, quimica, historia, geo, lengua):
            if seed_subject_wiki(subj):
                self.stdout.write(f"  Wikipedia → {subj.slug}")

        dict_emociones, _ = Dictionary.objects.get_or_create(
            subject=emociones_subj, slug="ontoemo",
            defaults={"name": "Vocabulario emocional", "description": "Base #ontoEmo (MFOEM / ONYX)"},
        )
        dict_neuro, _ = Dictionary.objects.get_or_create(
            subject=neurociencia, slug="ontoneuro",
            defaults={"name": "Sistema nervioso", "description": "Base #ontoNeuro (NeuroLex)"},
        )
        dict_micologia, _ = Dictionary.objects.get_or_create(subject=micologia, slug="ontohongo", defaults={"name": "Vocabulario micológico"})
        dict_quimica, _ = Dictionary.objects.get_or_create(
            subject=quimica, slug="ontoquim",
            defaults={"name": "Vocabulario químico", "description": "Base #ontoQuim (IUPAC)"},
        )
        dict_patrimonio, _ = Dictionary.objects.get_or_create(subject=historia, slug="patrimonio-local", defaults={"name": "Patrimonio local"})
        dict_mapa, _ = Dictionary.objects.get_or_create(subject=geo, slug="mapa-local", defaults={"name": "Mapa del entorno"})
        dict_palabras, _ = Dictionary.objects.get_or_create(subject=lengua, slug="vocabulario-poetico", defaults={"name": "Vocabulario poético"})

        # Taxonomías por asignatura (sin cruces entre dominios)
        tax_emociones, _ = Taxonomy.objects.get_or_create(
            slug="emociones",
            defaults={
                "name": "Emociones (#ontoEmo)",
                "description": "Ontología afectiva. Inspirada en MFOEM y ONYX.",
            },
        )
        tax_neuro, _ = Taxonomy.objects.get_or_create(
            slug="neurociencia",
            defaults={
                "name": "Neurociencia (#ontoNeuro)",
                "description": "Sistema nervioso y correlatos afectivos. Inspirada en NeuroLex/NIFSTD.",
            },
        )
        tax_hongos, _ = Taxonomy.objects.get_or_create(
            slug="hongos",
            defaults={
                "name": "Hongos (#ontoHongo)",
                "description": "Ontología híbrida navegable: anatomía, ciclo vital, ecología, taxonomía y aplicaciones.",
            },
        )
        tax_quimica, _ = Taxonomy.objects.get_or_create(
            slug="quimica",
            defaults={
                "name": "Química (#ontoQuim)",
                "description": "Vocabulario químico con referencias IUPAC y datos NIST.",
            },
        )
        tax_ecologia, _ = Taxonomy.objects.get_or_create(slug="ecologia", defaults={"name": "Ecología"})
        tax_patrimonio, _ = Taxonomy.objects.get_or_create(slug="tradiciones", defaults={"name": "Tradiciones"})
        tax_lugares, _ = Taxonomy.objects.get_or_create(slug="lugares", defaults={"name": "Lugares del municipio"})
        tax_metaforas, _ = Taxonomy.objects.get_or_create(slug="metaforas", defaults={"name": "Metáforas"})

        Taxonomy.objects.filter(slug="emociones").update(
            name="Emociones (#ontoEmo)",
            description="Ontología afectiva. Inspirada en MFOEM y ONYX.",
        )

        TaxonomyNode.objects.filter(taxonomy__in=[tax_ecologia, tax_patrimonio, tax_lugares, tax_metaforas]).delete()

        onto_hongos = seed_ontohongo(tax_hongos, dict_micologia)
        onto_emo = seed_ontology(tax_emociones, dict_emociones, ONTOEMO_TREE, ONTOEMO_DEFINITIONS, ONTOEMO_RELATIONS)
        seed_ontology(tax_neuro, dict_neuro, ONTONEURO_TREE, ONTONEURO_DEFINITIONS)
        onto_quim = seed_ontoquim(tax_quimica, dict_quimica)

        valencia_emo = onto_emo.get("Valencia")
        valencia_quim = onto_quim.get("Valencia química")
        if valencia_emo:
            homonym_note = (
                "Ver también [[asignatura:quimica|Química]]: "
                "[[Valencia química]]."
            )
            ConceptDefinition.objects.filter(concept=valencia_emo, kind="note").delete()
            ConceptDefinition.objects.create(
                concept=valencia_emo, kind="note", text=homonym_note, is_active=True,
            )

        micelio = onto_hongos["Micelio"]
        espora = onto_hongos["Espora"]
        bosque = onto_hongos["Bosque"]
        conidioforo = onto_hongos["Conidióforo"]
        alegria = onto_emo["Alegría"]
        tristeza = onto_emo["Tristeza"]
        melancolia = onto_emo["Melancolía"]
        metafora = concept_in_dict(dict_palabras, "Metáfora")
        fiesta = concept_in_dict(dict_patrimonio, "Fiesta del pueblo")
        plaza = concept_in_dict(dict_mapa, "Plaza mayor")
        rio = concept_in_dict(dict_mapa, "Río")

        ConceptProperty.objects.get_or_create(concept=micelio, key="dominio", defaults={"value": "micología"})
        ConceptProperty.objects.get_or_create(concept=conidioforo, key="hashtag", defaults={"value": "#ontoHongo"})
        ConceptProperty.objects.get_or_create(concept=alegria, key="hashtag", defaults={"value": "#ontoEmo"})
        ConceptProperty.objects.get_or_create(
            concept=micelio, key="orcid",
            defaults={"value": "0000-0002-1825-0097"},
        )
        ConceptProperty.objects.get_or_create(
            concept=micelio, key="source_url",
            defaults={"value": "https://www.mycobank.org/"},
        )
        ConceptProperty.objects.get_or_create(
            concept=micelio, key="institution",
            defaults={"value": "Real Jardín Botánico (CSIC)"},
        )
        ConceptDefinition.objects.get_or_create(
            concept=espora, kind="example",
            defaults={"text": "Esporas liberadas por *Trametes versicolor* en un tronco caído.", "is_active": True},
        )
        basidio = onto_hongos.get("Basidio")
        if basidio:
            ConceptProperty.objects.get_or_create(
                concept=basidio, key="sameAs",
                defaults={"value": "http://purl.obolibrary.org/obo/FUNGUS_0000001"},
            )

        p1, _ = ProyectoInvestigacion.objects.get_or_create(acron="PFC-1", defaults={"titulo": "Emociones en un poema", "descripcion": "Cruza Lengua y Música"})
        p2, _ = ProyectoInvestigacion.objects.get_or_create(acron="PFC-2", defaults={"titulo": "El bosque y sus sonidos", "descripcion": "Ciencias y Música"})
        p3, _ = ProyectoInvestigacion.objects.get_or_create(acron="PFC-3", defaults={"titulo": "Mi pueblo en el mapa", "descripcion": "Geografía e Historia"})

        for proj, caps in [(p1, ["ontology", "publish"]), (p2, ["ontology", "logs"]), (p3, ["geodata", "publish"])]:
            for c in caps:
                ProjectCurriculumDeclaration.objects.get_or_create(project=proj, capability_slug=c)

        for proj, concept_obj, status in [
            (p1, alegria, "used"), (p1, metafora, "cited"), (p1, tristeza, "selected"), (p1, melancolia, "interesting"),
            (p2, micelio, "used"), (p2, conidioforo, "interesting"), (p2, espora, "interesting"), (p2, bosque, "cited"),
            (p3, plaza, "used"), (p3, fiesta, "cited"), (p3, rio, "selected"),
        ]:
            LearningMarker.from_concept(proj, concept_obj, status=status, created_by="seed", base_url=base).save()

        act1, _ = ScientificActivity.objects.get_or_create(project=p1, slug="analizar-poema", defaults={"title": "Analizar emociones en un poema", "capability_slug": "ontology"})
        ScientificResult.objects.get_or_create(activity=act1, title="informe-emociones-poema.pdf", defaults={"result_type": "report", "published_at": timezone.now()})
        act2, _ = ScientificActivity.objects.get_or_create(project=p2, slug="observar-hongos", defaults={"title": "Observación de hongos", "capability_slug": "ontology"})
        ScientificResult.objects.get_or_create(activity=act2, title="ficha-hongos.jsonld", defaults={"result_type": "jsonld", "publish_url": f"{base}/biblioteca/temas/{micelio.uuid}/", "published_at": timezone.now()})
        act3, _ = ScientificActivity.objects.get_or_create(project=p3, slug="mapa-pueblo", defaults={"title": "Mapa del pueblo", "capability_slug": "geodata"})
        ScientificResult.objects.get_or_create(activity=act3, title="mapa-pueblo.geojson", defaults={"result_type": "geojson", "published_at": timezone.now()})

        self.stdout.write(self.style.SUCCESS(
            f"Seed OK — conceptos: {Concept.objects.count()}, taxonomías: {Taxonomy.objects.count()}, marcadores: {LearningMarker.objects.count()}"
        ))
