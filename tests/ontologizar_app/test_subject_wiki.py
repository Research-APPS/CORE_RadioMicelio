from unittest.mock import patch

from django.test import TestCase

from cms_app.views_public import subject_detail
from ontologizar_app.models import Dictionary, Subject, SubjectMaterial
from ontologizar_app.services.subject_body import render_subject_body


class SubjectWikiTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def test_subject_body_renders_wiki_sections(self):
        subj = Subject.objects.create(
            slug="ciencias-naturales",
            name="Ciencias Naturales",
            description="Primer párrafo.\n\nSegundo párrafo.",
            source_url="https://es.wikipedia.org/wiki/Ciencias_naturales",
        )
        Dictionary.objects.create(subject=subj, slug="vocab", name="Vocabulario")
        SubjectMaterial.objects.create(
            subject=subj, slug="u1", title="Unidad 1",
            body="Texto de la unidad.",
        )
        html = render_subject_body(subj)
        self.assertIn("Primer párrafo", html)
        self.assertIn("Unidad 1", html)
        self.assertIn("wikipedia.org", html)

    def test_subject_detail_view(self):
        Subject.objects.create(slug="test-sub", name="Test", description="Hola wiki.")
        from django.test import RequestFactory
        request = RequestFactory().get("/biblioteca/asignaturas/test-sub/")
        response = subject_detail(request, slug="test-sub")
        self.assertContains(response, "Hola wiki.")
        self.assertContains(response, "wiki-body")

    @patch("ontologizar_app.services.wikipedia.fetch_wikipedia_summary")
    def test_wikipedia_fetch_used_in_seed_helper(self, mock_fetch):
        from research_app.management.commands.seed_curriculum import seed_subject_wiki

        mock_fetch.return_value = {
            "extract": "Resumen de prueba.",
            "page_url": "https://es.wikipedia.org/wiki/Test",
        }
        subj = Subject.objects.create(slug="ciencias-naturales", name="Ciencias Naturales")
        self.assertTrue(seed_subject_wiki(subj))
        subj.refresh_from_db()
        self.assertEqual(subj.description, "Resumen de prueba.")
        self.assertIn("wikipedia.org", subj.source_url)
