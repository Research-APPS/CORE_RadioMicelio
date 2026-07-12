from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from research_app.models import ProyectoInvestigacion, ScientificActivity, ScientificResult


class ActivityViewsTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def setUp(self):
        call_command("seed_curriculum")
        self.project = ProyectoInvestigacion.objects.get(acron="PFC-2")
        self.project_p1 = ProyectoInvestigacion.objects.get(acron="PFC-1")
        self.activity = ScientificActivity.objects.get(slug="observar-hongos")
        self.client = Client()
        User.objects.get_or_create(username="ivansimo", defaults={"is_staff": True})

    def test_activity_list_renders(self):
        url = reverse("research:activity_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Observación de hongos", html)
        self.assertIn("Emociones en un poema", html)
        self.assertIn("Investigaciones", html)

    def test_activity_links_multiple_notebooks_after_seed(self):
        notebooks = list(self.activity.get_notebooks())
        acrons = {nb.acron for nb in notebooks}
        self.assertIn("PFC-1", acrons)
        self.assertIn("PFC-2", acrons)

    def test_activity_edit_requires_login(self):
        url = reverse("research:activity_edit", kwargs={"uuid": self.activity.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/cms/login/", response.url)

    def test_activity_edit_shows_notebook_checkboxes(self):
        self.client.login(username="ivansimo", password="12345678")
        url = reverse("research:activity_edit", kwargs={"uuid": self.activity.uuid})
        response = self.client.get(url)
        html = response.content.decode()
        self.assertIn("Cuadernos", html)
        self.assertIn("notebook_uuids", html)

    def test_activity_edit_updates_multiple_capabilities(self):
        self.client.login(username="ivansimo", password="12345678")
        url = reverse("research:activity_edit", kwargs={"uuid": self.activity.uuid})
        response = self.client.post(url, {
            "action": "save_activity",
            "title": "Observación micológica",
            "notebook_uuids": [str(self.project.uuid), str(self.project_p1.uuid)],
            "capability_slugs": ["ontology", "geodata", "narrate"],
            "status": "completed",
            "description": "Salida al bosque.",
        })
        self.assertEqual(response.status_code, 302)
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.title, "Observación micológica")
        self.assertEqual(self.activity.status, "completed")
        self.assertEqual(set(self.activity.get_capability_slugs()), {"ontology", "geodata", "narrate"})
        self.assertEqual(len(self.activity.get_notebooks()), 2)

    def test_activity_create_and_add_result(self):
        self.client.login(username="ivansimo", password="12345678")
        create_url = reverse("research:activity_create")
        response = self.client.post(create_url, {
            "title": "Nueva actividad de prueba",
            "notebook_uuids": [str(self.project.uuid)],
            "capability_slugs": ["geodata", "publish"],
            "status": "planned",
            "description": "",
        })
        self.assertEqual(response.status_code, 302)
        activity = ScientificActivity.objects.get(title="Nueva actividad de prueba")
        self.assertEqual(set(activity.get_capability_slugs()), {"geodata", "publish"})
        self.assertEqual(list(activity.get_notebooks()), [self.project])
        edit_url = reverse("research:activity_edit", kwargs={"uuid": activity.uuid})
        response = self.client.post(edit_url, {
            "action": "add_result",
            "capability_slug": "geodata",
            "result_title": "mapa-test.geojson",
            "result_type": "geojson",
            "publish_url": "https://example.com/mapa.geojson",
            "artifact_url": "",
        })
        self.assertEqual(response.status_code, 302)
        result = ScientificResult.objects.get(activity=activity, title="mapa-test.geojson")
        self.assertEqual(result.capability_slug, "geodata")

    def test_result_linked_to_capability_in_edit_view(self):
        self.client.login(username="ivansimo", password="12345678")
        url = reverse("research:activity_edit", kwargs={"uuid": self.activity.uuid})
        response = self.client.get(url)
        html = response.content.decode()
        self.assertIn("ficha-hongos.jsonld", html)
        self.assertIn("Añadir resultado para Vincular conocimiento", html)

    def test_activity_edit_groups_capabilities_by_family(self):
        self.client.login(username="ivansimo", password="12345678")
        url = reverse("research:activity_edit", kwargs={"uuid": self.activity.uuid})
        response = self.client.get(url)
        html = response.content.decode()
        self.assertIn("Funcionalidades", html)
        self.assertIn("Estructurar", html)
        self.assertIn("Publicar", html)
        self.assertIn("Explorar", html)
        self.assertIn("Vincular conocimiento", html)
        self.assertIn("Competencias de investigación", html)

    def test_unchecking_capability_removes_its_results(self):
        self.client.login(username="ivansimo", password="12345678")
        url = reverse("research:activity_edit", kwargs={"uuid": self.activity.uuid})
        self.client.post(url, {
            "action": "save_activity",
            "title": self.activity.title,
            "notebook_uuids": [str(self.project.uuid)],
            "capability_slugs": ["publish"],
            "status": "active",
            "description": "",
        })
        self.assertFalse(
            ScientificResult.objects.filter(activity=self.activity, title="ficha-hongos.jsonld").exists()
        )

    def test_proyecto_detail_shows_shared_investigation(self):
        url = reverse("research:proyecto_detail", kwargs={"uuid": self.project_p1.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Observación de hongos", html)

    def test_proyecto_detail_shows_capability_labels(self):
        url = reverse("research:proyecto_detail", kwargs={"uuid": self.project.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Observación de hongos", html)
        self.assertIn("Vincular conocimiento", html)
        self.assertIn("ficha-hongos.jsonld", html)
