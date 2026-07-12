import json

from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from ontologizar_app.models import Concept
from research_app.models import ProyectoInvestigacion
from research_app.project_ontology import build_digital_profile_jsonld, build_project_ontology_graph
from research_app.project_hub import get_project_digital_profile


class ProjectOntologyTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def setUp(self):
        call_command("seed_curriculum")
        self.project = ProyectoInvestigacion.objects.get(acron="PFC-1")
        self.client = Client()

    def test_ontology_graph_has_classes_and_properties(self):
        graph = build_project_ontology_graph(self.project.uuid)
        self.assertIsNotNone(graph)
        kinds = {n["kind"] for n in graph["nodes"]}
        self.assertIn("project", kinds)
        self.assertIn("class", kinds)
        self.assertIn("property", kinds)

    def test_digital_profile_jsonld_includes_graph(self):
        profile = get_project_digital_profile(self.project.uuid)
        payload = build_digital_profile_jsonld(profile)
        self.assertIn("@graph", payload)
        types = []
        for node in payload["@graph"]:
            t = node.get("@type")
            if isinstance(t, list):
                types.extend(t)
            elif t:
                types.append(t)
        self.assertTrue(any("OntologyClass" in str(t) or t == "DefinedTerm" for t in types))

    def test_marker_jsonld_endpoint(self):
        marker = self.project.markers.first()
        url = reverse(
            "research:marker_jsonld",
            kwargs={"uuid": self.project.uuid, "concept_uuid": marker.concept_uuid},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("@graph", data)
        labels = [n.get("name") for n in data["@graph"] if n.get("name")]
        self.assertIn(marker.concept_label, labels)

    def test_ontology_viz_page_renders(self):
        url = reverse("research:proyecto_ontology", kwargs={"uuid": self.project.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ontology-synth", response.content)
        self.assertIn(b"ontology-graph-data", response.content)
        self.assertIn(b"ontology-synth-code", response.content)

    def test_concept_jsonld_graph_param(self):
        concept = Concept.objects.get(label="Alegría", dictionary__subject__slug="emociones")
        url = reverse("ontologizar:concept_jsonld", kwargs={"uuid": concept.uuid}) + "?graph=1"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("@graph", data)
        class_nodes = [n for n in data["@graph"] if "OntologyClass" in str(n.get("@type", ""))]
        self.assertTrue(class_nodes)
