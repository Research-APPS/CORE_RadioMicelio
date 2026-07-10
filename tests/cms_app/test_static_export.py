from pathlib import Path

from django.test import TestCase, override_settings

from cms_app.static_export import export_static_site
from ontologizar_app.models import Concept, Dictionary, Subject


class StaticExportTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def _export(self, out: Path, **settings):
        if out.exists():
            import shutil
            shutil.rmtree(out)
        with override_settings(**settings):
            return export_static_site(out)

    def test_export_creates_biblioteca_and_graph(self):
        out = Path("dist-test-export")
        counts = self._export(out)
        self.assertGreater(counts["pages"], 0)
        self.assertTrue((out / "index.html").exists())
        self.assertTrue((out / "biblioteca" / "index.html").exists())
        self.assertTrue((out / "airam" / "graph.json").exists())
        self.assertTrue((out / "assets" / "core" / "css" / "core.css").exists())
        self.assertTrue((out / ".nojekyll").exists())
        import shutil
        shutil.rmtree(out)

    def test_export_uses_github_pages_subpath(self):
        out = Path("dist-test-export-subpath")
        site = "https://research-apps.github.io/CORE_RadioMicelio"
        if out.exists():
            import shutil
            shutil.rmtree(out)
        with self.settings(SITE_URL=site):
            export_static_site(out)
        index = (out / "index.html").read_text(encoding="utf-8")
        biblioteca = (out / "biblioteca" / "index.html").read_text(encoding="utf-8")
        self.assertIn('url=/CORE_RadioMicelio/biblioteca/', index)
        self.assertIn('href="/CORE_RadioMicelio/biblioteca/"', biblioteca)
        self.assertIn('href="/CORE_RadioMicelio/airam/graph.json"', biblioteca)
        import shutil
        shutil.rmtree(out)

    def test_export_no_airam_temario_on_taxonomy(self):
        from ontologizar_app.models import Taxonomy, TaxonomyNode
        Subject.objects.create(slug="s", name="S")
        tax = Taxonomy.objects.create(slug="t-export", name="T")
        TaxonomyNode.objects.create(taxonomy=tax, label="N")
        out = Path("dist-test-airam-static")
        if out.exists():
            import shutil
            shutil.rmtree(out)
        self._export(out)
        html = (out / "biblioteca" / "taxonomias" / "t-export" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("taxonomy-airam-btn", html)
        self.assertNotIn("airam_temario.js", html)
        import shutil
        shutil.rmtree(out)

    def test_export_quimica_valencia_topic(self):
        from django.core.management import call_command

        call_command("seed_curriculum")
        from ontologizar_app.models import Concept

        valencia = Concept.objects.get(label="Valencia química")
        out = Path("dist-test-export-quimica")
        if out.exists():
            import shutil
            shutil.rmtree(out)
        self._export(out)
        subject_page = (out / "biblioteca" / "asignaturas" / "quimica" / "index.html").read_text(encoding="utf-8")
        topic_page = (out / "biblioteca" / "temas" / str(valencia.uuid) / "index.html").read_text(encoding="utf-8")
        self.assertIn("Química", subject_page)
        self.assertIn("Fuentes y referencias", topic_page)
        self.assertIn("referencia IUPAC", topic_page)
        self.assertIn("base de datos", topic_page)
        self.assertIn('"citation"', topic_page)
        self.assertIn("10.1351/goldbook.V06588", topic_page)
        import shutil
        shutil.rmtree(out)

    def test_export_normalizes_mixed_case_site_url(self):
        out = Path("dist-test-export-case")
        site = "https://Research-APPS.github.io/CORE_RadioMicelio"
        if out.exists():
            import shutil
            shutil.rmtree(out)
        with self.settings(SITE_URL=site, ALLOWED_HOSTS=["127.0.0.1", "localhost"]):
            export_static_site(out)
        self.assertTrue((out / "biblioteca" / "index.html").exists())
        index = (out / "index.html").read_text(encoding="utf-8")
        self.assertIn('url=/CORE_RadioMicelio/biblioteca/', index)
        import shutil
        shutil.rmtree(out)
