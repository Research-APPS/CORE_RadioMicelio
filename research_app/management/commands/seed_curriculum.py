from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone

from knowledge_app.models import (
    Concept, ConceptDefinition, ConceptProperty, ConceptRelation,
    Dictionary, Subject, SubjectMaterial, Taxonomy, TaxonomyNode,
)
from logs_app.models import EventLog, ProjectPlatformLink
from research_app.models import (
    LearningMarker, ProyectoInvestigacion, ProjectCurriculumDeclaration,
    ScientificActivity, ScientificResult,
)

OLDS = ["DIDONE", "DIZO", "VACIADO", "SONARE"]


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


class Command(BaseCommand):
    help = "Seed currículo escolar + biblioteca semántica transversal"

    def handle(self, *args, **options):
        call_command("ensure_cms_user")
        base = "http://127.0.0.1:8003"

        ProyectoInvestigacion.objects.filter(acron__in=OLDS).delete()

        musica, _ = Subject.objects.get_or_create(slug="musica", defaults={"name": "Música"})
        ciencias, _ = Subject.objects.get_or_create(slug="ciencias-naturales", defaults={"name": "Ciencias Naturales"})
        historia, _ = Subject.objects.get_or_create(slug="historia", defaults={"name": "Historia"})
        geo, _ = Subject.objects.get_or_create(slug="geografia", defaults={"name": "Geografía"})
        lengua, _ = Subject.objects.get_or_create(slug="lengua", defaults={"name": "Lengua y Literatura"})

        SubjectMaterial.objects.get_or_create(subject=ciencias, slug="unidad-hongos", defaults={"title": "Unidad 3: Los hongos", "summary": "Libro digital"})
        SubjectMaterial.objects.get_or_create(subject=lengua, slug="poesia-emociones", defaults={"title": "La poesía y las emociones", "summary": "Material CMS"})

        dict_emociones, _ = Dictionary.objects.get_or_create(subject=musica, slug="emociones", defaults={"name": "Emociones en la música"})
        dict_hongos, _ = Dictionary.objects.get_or_create(subject=ciencias, slug="hongos", defaults={"name": "Hongos"})
        dict_patrimonio, _ = Dictionary.objects.get_or_create(subject=historia, slug="patrimonio-local", defaults={"name": "Patrimonio local"})
        dict_mapa, _ = Dictionary.objects.get_or_create(subject=geo, slug="mapa-local", defaults={"name": "Mapa del entorno"})
        dict_palabras, _ = Dictionary.objects.get_or_create(subject=lengua, slug="vocabulario-poetico", defaults={"name": "Vocabulario poético"})

        # Taxonomías transversales
        tax_emociones, _ = Taxonomy.objects.get_or_create(slug="emociones", defaults={"name": "Taxonomía de emociones", "description": "Transversal: Música, Literatura, Teatro"})
        tax_fungi, _ = Taxonomy.objects.get_or_create(slug="fungi", defaults={"name": "Taxonomía Fungi"})
        tax_ecologia, _ = Taxonomy.objects.get_or_create(slug="ecologia", defaults={"name": "Taxonomía Ecología"})
        tax_patrimonio, _ = Taxonomy.objects.get_or_create(slug="tradiciones", defaults={"name": "Tradiciones"})
        tax_lugares, _ = Taxonomy.objects.get_or_create(slug="lugares", defaults={"name": "Lugares del municipio"})
        tax_metaforas, _ = Taxonomy.objects.get_or_create(slug="metaforas", defaults={"name": "Metáforas"})

        TaxonomyNode.objects.filter(taxonomy__in=[tax_emociones, tax_fungi, tax_ecologia]).delete()

        alegria = concept_in_dict(dict_emociones, "Alegría")
        tristeza = concept_in_dict(dict_emociones, "Tristeza")
        emocion_lengua = concept_in_dict(dict_palabras, "Emoción")
        micelio = concept_in_dict(dict_hongos, "Micelio")
        espora = concept_in_dict(dict_hongos, "Espora")
        bosque = concept_in_dict(dict_hongos, "Bosque")
        fiesta = concept_in_dict(dict_patrimonio, "Fiesta del pueblo")
        plaza = concept_in_dict(dict_mapa, "Plaza mayor")
        rio = concept_in_dict(dict_mapa, "Río")
        metafora = concept_in_dict(dict_palabras, "Metáfora")

        # Enlaces transversales emociones
        for label, c in [("Alegría", alegria), ("Tristeza", tristeza), ("Emoción", emocion_lengua)]:
            TaxonomyNode.objects.get_or_create(taxonomy=tax_emociones, label=label, defaults={"concept": c})

        # Micelio en varias taxonomías
        TaxonomyNode.objects.get_or_create(taxonomy=tax_fungi, label="Micelio", defaults={"concept": micelio})
        TaxonomyNode.objects.get_or_create(taxonomy=tax_fungi, label="Espora", defaults={"concept": espora})
        TaxonomyNode.objects.get_or_create(taxonomy=tax_ecologia, label="Micelio", defaults={"concept": micelio})
        TaxonomyNode.objects.get_or_create(taxonomy=tax_ecologia, label="Bosque", defaults={"concept": bosque})
        TaxonomyNode.objects.get_or_create(taxonomy=tax_patrimonio, label="Fiesta del pueblo", defaults={"concept": fiesta})
        TaxonomyNode.objects.get_or_create(taxonomy=tax_lugares, label="Plaza mayor", defaults={"concept": plaza})
        TaxonomyNode.objects.get_or_create(taxonomy=tax_lugares, label="Río", defaults={"concept": rio})
        TaxonomyNode.objects.get_or_create(taxonomy=tax_metaforas, label="Metáfora", defaults={"concept": metafora})

        ConceptDefinition.objects.get_or_create(concept=micelio, kind="definition", defaults={"text": "Red de filamentos que forma el cuerpo vegetativo de un hongo.", "is_active": True})
        ConceptProperty.objects.get_or_create(concept=micelio, key="dominio", defaults={"value": "biología"})
        ConceptRelation.objects.get_or_create(source=micelio, target=bosque, relation_type="partOf")
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
            (p2, micelio, "used"), (p2, espora, "interesting"), (p2, bosque, "cited"),
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
