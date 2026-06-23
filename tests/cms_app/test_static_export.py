from pathlib import Path

from django.test import TestCase

from cms_app.static_export import export_static_site
from ontologizar_app.models import Concept, Dictionary, Subject


class StaticExportTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def test_export_creates_biblioteca_and_graph(self):
        out = Path("dist-test-export")
        if out.exists():
            import shutil
            shutil.rmtree(out)
        counts = export_static_site(out)
        self.assertGreater(counts["pages"], 0)
        self.assertTrue((out / "index.html").exists())
        self.assertTrue((out / "biblioteca" / "index.html").exists())
        self.assertTrue((out / "airam" / "graph.json").exists())
        self.assertTrue((out / "assets" / "core" / "css" / "core.css").exists())
        import shutil
        shutil.rmtree(out)
