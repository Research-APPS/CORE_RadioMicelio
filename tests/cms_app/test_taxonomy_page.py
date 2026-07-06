from django.test import TestCase
from django.urls import reverse

from ontologizar_app.models import Concept, Dictionary, Subject, Taxonomy, TaxonomyNode


class TaxonomyPageTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def test_taxonomy_tree_is_collapsible(self):
        subj = Subject.objects.create(slug="micologia", name="Micología")
        dic = Dictionary.objects.create(subject=subj, slug="h", name="H")
        tax = Taxonomy.objects.create(slug="hongos", name="Hongos")
        root_c = Concept.objects.create(dictionary=dic, label="Raíz")
        child_c = Concept.objects.create(dictionary=dic, label="Hijo")
        root = TaxonomyNode.objects.create(taxonomy=tax, label="Raíz", concept=root_c)
        TaxonomyNode.objects.create(taxonomy=tax, label="Hijo", concept=child_c, parent=root)

        url = reverse("biblioteca:taxonomy", kwargs={"slug": "hongos"})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "taxonomy-branch")
        self.assertContains(r, "taxonomy-node__summary")
        self.assertContains(r, 'data-level="0"')
        self.assertContains(r, 'data-level="1"')
        self.assertContains(r, "Expandir todo")
        self.assertContains(r, "taxonomy_tree.js")
        self.assertContains(r, "taxonomy-airam-btn")
        self.assertContains(r, "taxonomy-knowledge")
        self.assertContains(r, "Nv.")
        self.assertContains(r, "airam_temario.js")
        self.assertContains(r, "Tu progreso se conserva temporalmente")
