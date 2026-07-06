from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ontologizar_app.models import (
    Concept, ConceptDefinition, ConceptProperty,
    Dictionary, Subject, Taxonomy, TaxonomyNode,
)
from ontologizar_app.services.knowledge_depth import (
    build_taxonomy_knowledge_map,
    score_from_metrics,
)
from ontologizar_app.services.taxonomy_nodes import add_taxonomy_node, dictionary_for_taxonomy


class KnowledgeDepthTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def test_score_from_metrics(self):
        self.assertEqual(score_from_metrics(0, 0, 0), 0)
        self.assertEqual(score_from_metrics(50, 0, 0), 1)
        self.assertEqual(score_from_metrics(200, 1, 1), 4)

    def test_subtree_aggregation(self):
        subj = Subject.objects.create(slug="micologia", name="Micología")
        dic = Dictionary.objects.create(subject=subj, slug="h", name="H")
        tax = Taxonomy.objects.create(slug="hongos", name="Hongos")
        root_c = Concept.objects.create(dictionary=dic, label="Raíz")
        child_c = Concept.objects.create(dictionary=dic, label="Hijo")
        ConceptDefinition.objects.create(concept=child_c, text="Texto largo " * 30, kind="definition")
        ConceptProperty.objects.create(concept=child_c, key="tipo", value="basidiomiceto")
        root = TaxonomyNode.objects.create(taxonomy=tax, label="Raíz", concept=root_c)
        TaxonomyNode.objects.create(taxonomy=tax, label="Hijo", concept=child_c, parent=root)

        knowledge = build_taxonomy_knowledge_map(tax)
        child_node = TaxonomyNode.objects.get(label="Hijo")
        self.assertGreater(knowledge[child_node.uuid].level, 0)
        self.assertGreaterEqual(knowledge[root.uuid].level, knowledge[child_node.uuid].level)
        self.assertGreater(knowledge[root.uuid].text_chars, 0)

    def test_add_node_creates_concept(self):
        subj = Subject.objects.create(slug="micologia", name="Micología")
        dic = Dictionary.objects.create(subject=subj, slug="h", name="H")
        tax = Taxonomy.objects.create(slug="hongos", name="Hongos")
        root_c = Concept.objects.create(dictionary=dic, label="Micelio")
        TaxonomyNode.objects.create(taxonomy=tax, label="Micelio", concept=root_c)

        self.assertEqual(dictionary_for_taxonomy(tax), dic)
        node = add_taxonomy_node(tax, "Nueva clase", parent=None)
        self.assertEqual(node.label, "Nueva clase")
        self.assertEqual(node.concept.dictionary, dic)


class TaxonomyAddNodeViewTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def setUp(self):
        subj = Subject.objects.create(slug="micologia", name="Micología")
        self.dic = Dictionary.objects.create(subject=subj, slug="h", name="H")
        self.tax = Taxonomy.objects.create(slug="hongos", name="Hongos")
        root_c = Concept.objects.create(dictionary=self.dic, label="Raíz")
        self.root = TaxonomyNode.objects.create(taxonomy=self.tax, label="Raíz", concept=root_c)

    def test_add_requires_login(self):
        url = reverse("biblioteca:taxonomy_add_node", kwargs={"slug": "hongos"})
        r = self.client.post(url, {"label": "Clase nueva"})
        self.assertEqual(r.status_code, 302)
        self.assertIn("/cms/login/", r.url)

    def test_add_node_when_logged_in(self):
        get_user_model().objects.create_user(username="editor", password="secret")
        self.client.login(username="editor", password="secret")
        url = reverse("biblioteca:taxonomy_add_node", kwargs={"slug": "hongos"})
        r = self.client.post(url, {"label": "Anatomía", "parent_uuid": str(self.root.uuid)})
        self.assertEqual(r.status_code, 302)
        child = TaxonomyNode.objects.get(taxonomy=self.tax, label="Anatomía")
        self.assertEqual(child.parent, self.root)
