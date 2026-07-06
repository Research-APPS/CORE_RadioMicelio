import json

from django.test import Client, TestCase

from ontologizar_app.models import Concept, Dictionary, Subject, Taxonomy, TaxonomyNode
from airam_app.models import AiramSession
from airam_app.services.temario import session_nodes


class AiramSessionApiTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def setUp(self):
        self.client = Client()
        subj = Subject.objects.create(slug="micologia", name="Micología")
        dic = Dictionary.objects.create(subject=subj, slug="h", name="H")
        self.tax = Taxonomy.objects.create(slug="hongos", name="Hongos")
        c = Concept.objects.create(dictionary=dic, label="Micelio")
        self.node = TaxonomyNode.objects.create(taxonomy=self.tax, label="Micelio", concept=c)

    def test_create_get_patch_bookmark(self):
        r = self.client.post(
            "/airam/sessions/",
            data=json.dumps({
                "taxonomy_slug": "hongos",
                "node_uuid": str(self.node.uuid),
                "granularity": "normal",
            }),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 201)
        data = r.json()
        sid = data["uuid"]
        self.assertEqual(data["last_node_uuid"], str(self.node.uuid))
        self.assertIn("view", data)

        r2 = self.client.get(f"/airam/sessions/{sid}/")
        self.assertEqual(r2.status_code, 200)

        r3 = self.client.patch(
            f"/airam/sessions/{sid}/",
            data=json.dumps({"action": "set_granularity", "granularity": "profundo"}),
            content_type="application/json",
        )
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.json()["granularity"], "profundo")

        session = AiramSession.objects.get(uuid=sid)
        self.assertFalse(session.is_bookmarked)

        r4 = self.client.post(f"/airam/sessions/{sid}/bookmark/", data="{}", content_type="application/json")
        self.assertEqual(r4.status_code, 200)
        session.refresh_from_db()
        self.assertTrue(session.is_bookmarked)
        self.assertIsNotNone(session.bookmarked_at)

    def test_explore_concept_action(self):
        r = self.client.post(
            "/airam/sessions/",
            data=json.dumps({
                "taxonomy_slug": "hongos",
                "node_uuid": str(self.node.uuid),
            }),
            content_type="application/json",
        )
        sid = r.json()["uuid"]
        r2 = self.client.patch(
            f"/airam/sessions/{sid}/",
            data=json.dumps({
                "action": "explore_concept",
                "concept_uuid": str(self.node.concept.uuid),
            }),
            content_type="application/json",
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["view"]["mode"], "explore")

    def test_create_combined_session(self):
        child_c = Concept.objects.create(dictionary=self.node.concept.dictionary, label="Espora")
        child = TaxonomyNode.objects.create(
            taxonomy=self.tax, label="Espora", concept=child_c,
        )
        r = self.client.post(
            "/airam/sessions/",
            data=json.dumps({
                "taxonomy_slug": "hongos",
                "node_uuids": [str(self.node.uuid), str(child.uuid)],
                "granularity": "normal",
            }),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertEqual(len(data["combined_nodes"]), 2)
        self.assertIn("Micelio", data["title"])
        self.assertIn("Espora", data["title"])

    def test_add_class_to_session(self):
        child_c = Concept.objects.create(dictionary=self.node.concept.dictionary, label="Espora")
        child = TaxonomyNode.objects.create(
            taxonomy=self.tax, label="Espora", concept=child_c,
        )
        r = self.client.post(
            "/airam/sessions/",
            data=json.dumps({
                "taxonomy_slug": "hongos",
                "node_uuid": str(self.node.uuid),
            }),
            content_type="application/json",
        )
        sid = r.json()["uuid"]
        r2 = self.client.patch(
            f"/airam/sessions/{sid}/",
            data=json.dumps({"action": "add_class", "node_uuid": str(child.uuid)}),
            content_type="application/json",
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(len(r2.json()["combined_nodes"]), 2)
        session = AiramSession.objects.get(uuid=sid)
        flat = session_nodes(session)
        self.assertEqual([n.label for n in flat], ["Micelio", "Espora"])
