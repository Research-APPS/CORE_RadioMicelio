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


SUBJECT_WIKIPEDIA = {
    "ciencias-naturales": "Ciencias_naturales",
    "micologia": "Micología",
    "musica": "Música",
    "historia": "Historia",
    "geografia": "Geografía",
    "lengua": "Literatura",
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


def seed_ontohongo(taxonomy, dictionary):
    TaxonomyNode.objects.filter(taxonomy=taxonomy).delete()
    link_taxonomy(taxonomy, dictionary, ONTOHONGO_TREE)
    concepts = {c.label: c for c in Concept.objects.filter(dictionary=dictionary)}
    for label, text in ONTOHONGO_DEFINITIONS.items():
        if label in concepts:
            ConceptDefinition.objects.get_or_create(
                concept=concepts[label], kind="definition",
                defaults={"text": text, "is_active": True},
            )
    def rel(a, b, kind="related"):
        if a in concepts and b in concepts:
            ConceptRelation.objects.get_or_create(source=concepts[a], target=concepts[b], relation_type=kind)

    rel("Hifa", "Micelio", "partOf")
    rel("Conidióforo", "Conidio", "narrower")
    rel("Conidióforo", "Espora", "related")
    rel("Conidio", "Espora", "narrower")
    rel("Espora", "Dispersión", "related")
    rel("Dispersión", "Bosque", "related")
    rel("Micelio", "Bosque", "partOf")
    return concepts


class Command(BaseCommand):
    help = "Seed currículo escolar + biblioteca semántica transversal"

    def handle(self, *args, **options):
        call_command("ensure_cms_user")
        base = "http://127.0.0.1:8003"

        ProyectoInvestigacion.objects.filter(acron__in=OLDS).delete()

        musica, _ = Subject.objects.get_or_create(slug="musica", defaults={"name": "Música"})
        ciencias, _ = Subject.objects.get_or_create(slug="ciencias-naturales", defaults={"name": "Ciencias Naturales"})
        micologia, _ = Subject.objects.get_or_create(slug="micologia", defaults={"name": "Micología"})
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
                    "[[Hifa|hifas]], [[Micelio|micelios]] y [[Espora|esporas]], y se relacionan con ecosistemas "
                    "como el [[Bosque]].\n\n"
                    "En la biblioteca del centro puedes seguir con la asignatura [[asignatura:micologia|Micología]] "
                    "y la taxonomía transversal [[taxonomia:hongos|Hongos (#ontoHongo)]], donde cada concepto "
                    "tiene ficha semántica y relaciones navegables."
                ),
            },
        )
        SubjectMaterial.objects.get_or_create(subject=lengua, slug="poesia-emociones", defaults={"title": "La poesía y las emociones", "summary": "Material CMS"})

        for subj in (musica, ciencias, micologia, historia, geo, lengua):
            if seed_subject_wiki(subj):
                self.stdout.write(f"  Wikipedia → {subj.slug}")

        dict_emociones, _ = Dictionary.objects.get_or_create(subject=musica, slug="emociones", defaults={"name": "Emociones en la música"})
        dict_micologia, _ = Dictionary.objects.get_or_create(subject=micologia, slug="ontohongo", defaults={"name": "Vocabulario micológico"})
        dict_patrimonio, _ = Dictionary.objects.get_or_create(subject=historia, slug="patrimonio-local", defaults={"name": "Patrimonio local"})
        dict_mapa, _ = Dictionary.objects.get_or_create(subject=geo, slug="mapa-local", defaults={"name": "Mapa del entorno"})
        dict_palabras, _ = Dictionary.objects.get_or_create(subject=lengua, slug="vocabulario-poetico", defaults={"name": "Vocabulario poético"})

        # Taxonomías transversales
        tax_emociones, _ = Taxonomy.objects.get_or_create(slug="emociones", defaults={"name": "Taxonomía de emociones", "description": "Transversal: Música, Literatura, Teatro"})
        tax_hongos, _ = Taxonomy.objects.get_or_create(
            slug="hongos",
            defaults={
                "name": "Hongos (#ontoHongo)",
                "description": "Ontología híbrida navegable: anatomía, ciclo vital, ecología, taxonomía y aplicaciones.",
            },
        )
        tax_ecologia, _ = Taxonomy.objects.get_or_create(slug="ecologia", defaults={"name": "Taxonomía Ecología"})
        tax_patrimonio, _ = Taxonomy.objects.get_or_create(slug="tradiciones", defaults={"name": "Tradiciones"})
        tax_lugares, _ = Taxonomy.objects.get_or_create(slug="lugares", defaults={"name": "Lugares del municipio"})
        tax_metaforas, _ = Taxonomy.objects.get_or_create(slug="metaforas", defaults={"name": "Metáforas"})

        TaxonomyNode.objects.filter(taxonomy__in=[tax_emociones, tax_ecologia]).delete()

        onto = seed_ontohongo(tax_hongos, dict_micologia)
        micelio = onto["Micelio"]
        espora = onto["Espora"]
        bosque = onto["Bosque"]
        conidioforo = onto["Conidióforo"]

        alegria = concept_in_dict(dict_emociones, "Alegría")
        tristeza = concept_in_dict(dict_emociones, "Tristeza")
        emocion_lengua = concept_in_dict(dict_palabras, "Emoción")
        fiesta = concept_in_dict(dict_patrimonio, "Fiesta del pueblo")
        plaza = concept_in_dict(dict_mapa, "Plaza mayor")
        rio = concept_in_dict(dict_mapa, "Río")
        metafora = concept_in_dict(dict_palabras, "Metáfora")

        # Enlaces transversales emociones
        for label, c in [("Alegría", alegria), ("Tristeza", tristeza), ("Emoción", emocion_lengua)]:
            TaxonomyNode.objects.get_or_create(taxonomy=tax_emociones, label=label, defaults={"concept": c})

        TaxonomyNode.objects.get_or_create(taxonomy=tax_ecologia, label="Micelio", defaults={"concept": micelio})
        TaxonomyNode.objects.get_or_create(taxonomy=tax_ecologia, label="Bosque", defaults={"concept": bosque})
        TaxonomyNode.objects.get_or_create(taxonomy=tax_patrimonio, label="Fiesta del pueblo", defaults={"concept": fiesta})
        TaxonomyNode.objects.get_or_create(taxonomy=tax_lugares, label="Plaza mayor", defaults={"concept": plaza})
        TaxonomyNode.objects.get_or_create(taxonomy=tax_lugares, label="Río", defaults={"concept": rio})
        TaxonomyNode.objects.get_or_create(taxonomy=tax_metaforas, label="Metáfora", defaults={"concept": metafora})

        ConceptProperty.objects.get_or_create(concept=micelio, key="dominio", defaults={"value": "micología"})
        ConceptProperty.objects.get_or_create(concept=conidioforo, key="hashtag", defaults={"value": "#ontoHongo"})
        ConceptRelation.objects.get_or_create(source=alegria, target=emocion_lengua, relation_type="related")
        ConceptRelation.objects.get_or_create(source=micelio, target=alegria, relation_type="related")

        p1, _ = ProyectoInvestigacion.objects.get_or_create(acron="PFC-1", defaults={"titulo": "Emociones en un poema", "descripcion": "Cruza Lengua y Música"})
        p2, _ = ProyectoInvestigacion.objects.get_or_create(acron="PFC-2", defaults={"titulo": "El bosque y sus sonidos", "descripcion": "Ciencias y Música"})
        p3, _ = ProyectoInvestigacion.objects.get_or_create(acron="PFC-3", defaults={"titulo": "Mi pueblo en el mapa", "descripcion": "Geografía e Historia"})

        for proj, caps in [(p1, ["ontology", "publish"]), (p2, ["ontology", "logs"]), (p3, ["geodata", "publish"])]:
            for c in caps:
                ProjectCurriculumDeclaration.objects.get_or_create(project=proj, capability_slug=c)

        for proj, concept_obj, status in [
            (p1, alegria, "used"), (p1, metafora, "cited"), (p1, tristeza, "selected"),
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
