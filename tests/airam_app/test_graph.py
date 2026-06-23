from django.test import TestCase
from django.test.client import RequestFactory

from airam_app.graph import build_graph
from airam_app.views import graph_json
from ontologizar_app.models import Concept, ConceptRelation, Dictionary, Subject, Taxonomy, TaxonomyNode


class AiramGraphTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def test_graph_has_centro(self):
        g = build_graph()
        ids = {n["id"] for n in g["nodes"]}
        self.assertIn("centro:radio-micelio", ids)

    def test_graph_concept_relations(self):
        subj = Subject.objects.create(slug="n", name="N")
        dic = Dictionary.objects.create(subject=subj, slug="d", name="D")
        a = Concept.objects.create(dictionary=dic, label="A")
        b = Concept.objects.create(dictionary=dic, label="B")
        ConceptRelation.objects.create(source=a, target=b, relation_type="related")
        edges = build_graph()["edges"]
        self.assertTrue(any(e.get("relation") == "related" for e in edges))

    def test_graph_endpoint(self):
        rf = RequestFactory()
        resp = graph_json(rf.get("/airam/graph.json"))
        self.assertEqual(resp.status_code, 200)
