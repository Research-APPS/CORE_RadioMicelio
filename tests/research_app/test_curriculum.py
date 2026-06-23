from django.test import TestCase

from knowledge_app.models import Concept, Dictionary, Subject, Taxonomy, TaxonomyNode
from research_app.models import LearningMarker, ProyectoInvestigacion, ProjectCurriculumDeclaration
from research_app.project_hub import get_project_digital_profile


class CurriculumTests(TestCase):
    databases = {"default", "research_db", "knowledge_db"}

    def test_marker_and_expediente(self):
        subj = Subject.objects.create(slug="musica", name="Música")
        dic = Dictionary.objects.create(subject=subj, slug="test-dic", name="Test")
        tax = Taxonomy.objects.create(slug="test-tax", name="Tax")
        concept = Concept.objects.create(dictionary=dic, label="Ira")
        TaxonomyNode.objects.create(taxonomy=tax, label="Ira", concept=concept)
        proj = ProyectoInvestigacion.objects.create(titulo="Test", acron="T1")
        ProjectCurriculumDeclaration.objects.create(project=proj, capability_slug="ontology")
        LearningMarker.from_concept(proj, concept, status="used").save()
        profile = get_project_digital_profile(proj.uuid)
        self.assertEqual(len(profile.markers), 1)
        self.assertEqual(profile.markers[0]["concept_label"], "Ira")
