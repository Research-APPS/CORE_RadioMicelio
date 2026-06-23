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
