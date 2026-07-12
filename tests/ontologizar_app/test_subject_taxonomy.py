from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from ontologizar_app.models import Concept, Dictionary, Subject, SubjectTaxonomy, Taxonomy, TaxonomyNode
from ontologizar_app.services.subject_curriculum import concept_classifications, subject_curriculum_profile
from ontologizar_app.services.subject_taxonomy import assign_subject_taxonomy


class SubjectTaxonomyModelTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def test_assign_is_idempotent(self):
        subj = Subject.objects.create(slug="test-subj", name="Test")
        tax = Taxonomy.objects.create(slug="test-tax", name="Test Tax")
        assign_subject_taxonomy(subj, tax, role="class", is_primary=True)
        assign_subject_taxonomy(subj, tax, role="class", is_primary=True)
        self.assertEqual(SubjectTaxonomy.objects.filter(subject=subj, taxonomy=tax).count(), 1)


class SubjectCurriculumProfileTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def setUp(self):
        self.subj = Subject.objects.create(slug="neuro-test", name="Neuro Test")
        self.dict = Dictionary.objects.create(subject=self.subj, slug="dict", name="Dict")
        self.tax = Taxonomy.objects.create(slug="neuro-tax", name="Neuro Tax")
        self.c1 = Concept.objects.create(dictionary=self.dict, label="Neurona")
        self.c2 = Concept.objects.create(dictionary=self.dict, label="Sin clasificar")
        TaxonomyNode.objects.create(taxonomy=self.tax, label="Neurona", concept=self.c1)
        assign_subject_taxonomy(self.subj, self.tax, role="class", is_primary=True)

    def test_profile_lists_taxonomies_and_unclassified(self):
        profile = subject_curriculum_profile(self.subj)
        self.assertEqual(len(profile.dictionaries), 1)
        self.assertEqual(len(profile.taxonomies_by_role["class"]), 1)
        self.assertEqual(profile.completeness.unclassified_count, 1)
        self.assertIn(self.c2, profile.unclassified_concepts)

    def test_concept_classifications_breadcrumb(self):
        classifications = concept_classifications(self.c1)
        self.assertEqual(len(classifications), 1)
        self.assertEqual(classifications[0].breadcrumb, ["Neurona"])
        self.assertEqual(classifications[0].taxonomy.slug, "neuro-tax")


class SubjectPageTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def test_neurociencia_page_after_seed(self):
        call_command("seed_curriculum")
        response = self.client.get(reverse("biblioteca:subject", kwargs={"slug": "neurociencia"}))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Taxonomías de clases", content)
        self.assertIn("Neurociencia", content)
        self.assertIn("Diccionarios", content)
        self.assertIn("Completitud curricular", content)
        self.assertTrue(
            SubjectTaxonomy.objects.filter(
                subject__slug="neurociencia", taxonomy__slug="neurociencia", role="class",
            ).exists()
        )


class TopicClassificationTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def test_topic_shows_classification_paths(self):
        call_command("seed_curriculum")
        neurona = Concept.objects.get(dictionary__subject__slug="neurociencia", label="Neurona")
        response = self.client.get(reverse("biblioteca:topic", kwargs={"uuid": neurona.uuid}))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Clasificación", content)
        self.assertIn("Neurociencia", content)


class AuditCommandTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def test_audit_runs_after_seed(self):
        call_command("seed_curriculum")
        call_command("audit_subject_taxonomies", slug="neurociencia")
