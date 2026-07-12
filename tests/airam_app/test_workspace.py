import json
import uuid

from django.core.management import call_command
from django.test import Client, TestCase

from airam_app.models import AiramConceptWeight, AiramSession
from ontologizar_app.models import Concept, Dictionary, Subject, Taxonomy, TaxonomyNode
from research_app.models import LearningMarker, ProyectoInvestigacion


class AiramWorkspaceTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def setUp(self):
        self.client = Client()
        call_command("seed_curriculum")
        subj = Subject.objects.create(slug="narrativa-ws", name="Narrativa WS")
        dic = Dictionary.objects.create(subject=subj, slug="meta", name="Meta")
        self.tax_a = Taxonomy.objects.create(slug="tax-a", name="Tax A")
        self.tax_b = Taxonomy.objects.create(slug="tax-b", name="Tax B")
        self.c_a = Concept.objects.create(dictionary=dic, label="Neurona WS")
        self.c_b = Concept.objects.create(dictionary=dic, label="Héroe WS")
        TaxonomyNode.objects.create(taxonomy=self.tax_a, label="Neurona WS", concept=self.c_a)
        TaxonomyNode.objects.create(taxonomy=self.tax_b, label="Héroe WS", concept=self.c_b)
        self.project = ProyectoInvestigacion.objects.first()

    def test_create_and_record_cross_taxonomy(self):
        r = self.client.post("/airam/workspace/", data="{}", content_type="application/json")
        self.assertEqual(r.status_code, 201)
        wid = r.json()["uuid"]
        self.assertEqual(r.json()["session_kind"], "workspace")

        r2 = self.client.patch(
            f"/airam/workspace/{wid}/",
            data=json.dumps({
                "action": "record_concept",
                "concept_uuid": str(self.c_a.uuid),
                "event_type": "visited",
            }),
            content_type="application/json",
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["frame"][0]["label"], "Neurona WS")
        self.assertEqual(r2.json()["frame"][0]["weight"], 1)

        r3 = self.client.patch(
            f"/airam/workspace/{wid}/",
            data=json.dumps({
                "action": "record_concept",
                "concept_uuid": str(self.c_b.uuid),
            }),
            content_type="application/json",
        )
        self.assertEqual(r3.status_code, 200)
        labels = {row["label"] for row in r3.json()["frame"]}
        self.assertEqual(labels, {"Neurona WS", "Héroe WS"})

        r4 = self.client.patch(
            f"/airam/workspace/{wid}/",
            data=json.dumps({
                "action": "record_concept",
                "concept_uuid": str(self.c_a.uuid),
            }),
            content_type="application/json",
        )
        self.assertEqual(r4.json()["frame"][0]["weight"], 2)
        self.assertEqual(r4.json()["frame"][0]["visit_count"], 2)

    def test_link_project_and_promote_markers(self):
        if not self.project:
            self.skipTest("Sin proyectos en seed")
        r = self.client.post("/airam/workspace/", data="{}", content_type="application/json")
        wid = r.json()["uuid"]
        self.client.patch(
            f"/airam/workspace/{wid}/",
            data=json.dumps({
                "action": "record_concept",
                "concept_uuid": str(self.c_a.uuid),
            }),
            content_type="application/json",
        )
        for _ in range(5):
            self.client.patch(
                f"/airam/workspace/{wid}/",
                data=json.dumps({
                    "action": "record_concept",
                    "concept_uuid": str(self.c_a.uuid),
                }),
                content_type="application/json",
            )

        r_link = self.client.patch(
            f"/airam/workspace/{wid}/",
            data=json.dumps({
                "action": "link_project",
                "project_uuid": str(self.project.uuid),
            }),
            content_type="application/json",
        )
        self.assertEqual(r_link.status_code, 200)
        self.assertEqual(r_link.json()["project_uuid"], str(self.project.uuid))

        before = LearningMarker.objects.filter(
            project=self.project, concept_uuid=self.c_a.uuid,
        ).count()
        r_promote = self.client.patch(
            f"/airam/workspace/{wid}/",
            data=json.dumps({"action": "promote_markers", "min_weight": 3}),
            content_type="application/json",
        )
        self.assertEqual(r_promote.status_code, 200)
        after = LearningMarker.objects.filter(
            project=self.project, concept_uuid=self.c_a.uuid,
        ).count()
        self.assertEqual(after, before + 1)

    def test_workspace_get_or_create_idempotent(self):
        r1 = self.client.post("/airam/workspace/", data="{}", content_type="application/json")
        r2 = self.client.post("/airam/workspace/", data="{}", content_type="application/json")
        self.assertEqual(r1.json()["uuid"], r2.json()["uuid"])

    def test_temario_sessions_unaffected(self):
        node = TaxonomyNode.objects.get(taxonomy=self.tax_a)
        r = self.client.post(
            "/airam/sessions/",
            data=json.dumps({
                "taxonomy_slug": "tax-a",
                "node_uuid": str(node.uuid),
            }),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 201)
        session = AiramSession.objects.get(uuid=r.json()["uuid"])
        self.assertEqual(session.session_kind, "temario")
        self.assertIsNotNone(session.taxonomy_id)

    def test_workspace_projects_list(self):
        r = self.client.get("/airam/workspace/projects/")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(len(r.json()["projects"]) >= 1)
