from django.test import TestCase

from knowledge_app.models import Concept, Dictionary, Subject, Taxonomy, TaxonomyNode
from logs_app.models import ProjectPlatformLink
from research_app.models import LearningMarker, ProyectoInvestigacion, ProjectCurriculumDeclaration
from research_app.project_hub import get_project_digital_profile


class ProjectHubTests(TestCase):
    databases = {"default", "research_db", "knowledge_db"}

    def test_digital_profile_includes_markers_and_declarations(self):
        subj = Subject.objects.create(slug="musica", name="Música")
        dic = Dictionary.objects.create(subject=subj, slug="dic", name="Dic")
        tax = Taxonomy.objects.create(slug="tax", name="Tax")
        concept = Concept.objects.create(dictionary=dic, label="Ira")
        TaxonomyNode.objects.create(taxonomy=tax, label="Ira", concept=concept)
        proyecto = ProyectoInvestigacion.objects.create(titulo="Test", acron="T1")
        ProjectPlatformLink.objects.create(research_project_uuid=proyecto.uuid, platform_slug="aula-virtual")
        ProjectCurriculumDeclaration.objects.create(project=proyecto, capability_slug="ontology")
        LearningMarker.from_concept(proyecto, concept, status="used").save()
        profile = get_project_digital_profile(proyecto.uuid)
        self.assertIsNotNone(profile)
        self.assertEqual(len(profile.markers), 1)
        self.assertIn("ontology", profile.curriculum["declared_capabilities"])
