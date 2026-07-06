import json

from django.test import Client, TestCase

from airam_app.models import AiramSession
from airam_app.services.rdf_export import document_from_session, session_to_jsonld, session_to_turtle
from ontologizar_app.models import Concept, ConceptDefinition, ConceptProperty, Dictionary, Subject, Taxonomy, TaxonomyNode


class TemarioRdfExportTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def setUp(self):
        self.client = Client()
        subj = Subject.objects.create(slug="micologia", name="Micología")
        dic = Dictionary.objects.create(subject=subj, slug="h", name="H")
        self.tax = Taxonomy.objects.create(slug="hongos", name="Hongos")
        c1 = Concept.objects.create(dictionary=dic, label="Micelio")
        c2 = Concept.objects.create(dictionary=dic, label="Espora")
        ConceptDefinition.objects.create(
            concept=c1, kind="definition", text="Red de hifos.", is_active=True,
        )
        ConceptProperty.objects.create(concept=c1, key="tipo", value="estructura")
        self.n1 = TaxonomyNode.objects.create(taxonomy=self.tax, label="Micelio", concept=c1)
        self.n2 = TaxonomyNode.objects.create(taxonomy=self.tax, label="Espora", concept=c2)

    def _create_session(self):
        r = self.client.post(
            "/airam/sessions/",
            data=json.dumps({
                "taxonomy_slug": "hongos",
                "node_uuids": [str(self.n1.uuid), str(self.n2.uuid)],
            }),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 201)
        return r.json()["uuid"]

    def test_session_jsonld_contains_topics(self):
        sid = self._create_session()
        session = AiramSession.objects.get(uuid=sid)
        doc = session_to_jsonld(session)
        graph = doc["@graph"]
        self.assertTrue(any("airam:TemarioSession" in g.get("@type", []) for g in graph))
        topics = [g for g in graph if "airam:Topic" in g.get("@type", [])]
        self.assertEqual(len(topics), 2)
        micelio = next(g for g in topics if g["skos:prefLabel"] == "Micelio")
        self.assertIn("skos:definition", micelio)

    def test_session_rdf_endpoint_download(self):
        sid = self._create_session()
        r = self.client.get(f"/airam/sessions/{sid}/rdf/?format=json")
        self.assertEqual(r.status_code, 200)
        self.assertIn("application/ld+json", r["Content-Type"])
        self.assertIn("attachment", r["Content-Disposition"])
        payload = json.loads(r.content)
        self.assertIn("@graph", payload)

    def test_session_turtle_export(self):
        sid = self._create_session()
        session = AiramSession.objects.get(uuid=sid)
        ttl = session_to_turtle(session)
        self.assertIn("@prefix airam:", ttl)
        self.assertIn("airam:TemarioSession", ttl)
        self.assertIn("Micelio", ttl)

    def test_preview_export_from_queue(self):
        r = self.client.post(
            "/airam/temario/rdf/",
            data=json.dumps({
                "taxonomy_slug": "hongos",
                "node_uuids": [str(self.n1.uuid), str(self.n2.uuid)],
                "format": "jsonld",
            }),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("@graph", data)
        self.assertEqual(data["@graph"][0]["airam:topicCount"], 2)

    def test_document_from_session_play_order(self):
        sid = self._create_session()
        session = AiramSession.objects.get(uuid=sid)
        doc = document_from_session(session)
        self.assertEqual(len(doc.classes), 2)
        self.assertEqual(doc.play_order[0], str(self.n1.concept.uuid))
