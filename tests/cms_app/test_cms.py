from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase

from knowledge_app.models import Concept, ConceptProperty, Dictionary, Subject, Taxonomy, TaxonomyNode
from knowledge_app.services.taxonomy_import import import_taxonomy_from_json


class CmsTests(TestCase):
    databases = {"default", "research_db", "knowledge_db"}

    def setUp(self):
        self.client = Client()

    def test_cms_requires_login(self):
        r = self.client.get("/cms/")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/cms/login/", r.url)

    def test_ensure_cms_user(self):
        call_command("ensure_cms_user")
        self.assertTrue(get_user_model().objects.filter(username="ivansimo").exists())

    def test_concept_shared_across_taxonomies(self):
        subj = Subject.objects.create(slug="nat", name="Naturaleza")
        dic = Dictionary.objects.create(subject=subj, slug="vida", name="Vida")
        c = Concept.objects.create(dictionary=dic, label="Micelio")
        t1 = Taxonomy.objects.create(slug="fungi", name="Fungi")
        t2 = Taxonomy.objects.create(slug="eco", name="Ecología")
        TaxonomyNode.objects.create(taxonomy=t1, label="Micelio", concept=c)
        TaxonomyNode.objects.create(taxonomy=t2, label="Micelio", concept=c)
        self.assertEqual(TaxonomyNode.objects.filter(concept=c).count(), 2)

    def test_taxonomy_import_reuses_concept(self):
        subj = Subject.objects.create(slug="s1", name="S")
        dic = Dictionary.objects.create(subject=subj, slug="d1", name="D")
        tax = Taxonomy.objects.create(slug="t-import", name="T")
        data = {"Raíz": {"Hoja": None}}
        ok, _, _ = import_taxonomy_from_json(tax, dic, data)
        self.assertTrue(ok)
        self.assertEqual(Concept.objects.filter(dictionary=dic).count(), 2)

    def test_topic_page_public_and_jsonld(self):
        subj = Subject.objects.create(slug="mus", name="Música")
        dic = Dictionary.objects.create(subject=subj, slug="emo", name="Emo")
        c = Concept.objects.create(dictionary=dic, label="Alegría")
        ConceptProperty.objects.create(concept=c, key="intensidad", value="alta")
        r = self.client.get(f"/biblioteca/temas/{c.uuid}/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Alegría")
        self.assertContains(r, "application/ld+json")
        self.assertContains(r, "additionalProperty")
