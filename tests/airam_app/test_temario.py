from django.test import TestCase

from ontologizar_app.models import Concept, Dictionary, Subject, Taxonomy, TaxonomyNode
from airam_app.services.temario import (
    combined_subtree_nodes,
    narrate_node,
    next_node_in_subtree,
    subtree_nodes,
)


class TemarioServiceTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def setUp(self):
        subj = Subject.objects.create(slug="micologia", name="Micología")
        dic = Dictionary.objects.create(subject=subj, slug="h", name="H")
        self.tax = Taxonomy.objects.create(slug="hongos", name="Hongos")
        self.root_c = Concept.objects.create(dictionary=dic, label="Raíz")
        self.child_c = Concept.objects.create(dictionary=dic, label="Hijo")
        self.root = TaxonomyNode.objects.create(taxonomy=self.tax, label="Raíz", concept=self.root_c)
        self.child = TaxonomyNode.objects.create(
            taxonomy=self.tax, label="Hijo", concept=self.child_c, parent=self.root,
        )

    def test_subtree_dfs_order(self):
        nodes = subtree_nodes(self.root)
        self.assertEqual([n.label for n in nodes], ["Raíz", "Hijo"])

    def test_narrate_breve_and_normal(self):
        from ontologizar_app.models import ConceptDefinition
        ConceptDefinition.objects.create(
            concept=self.root_c, kind="definition",
            text="Primera oración. Segunda oración.", is_active=True,
        )
        breve = narrate_node(self.root, "breve")
        self.assertIn("Primera oración.", breve["paragraphs"][0])
        normal = narrate_node(self.root, "normal")
        self.assertEqual(len(normal["paragraphs"]), 2)

    def test_next_node(self):
        nxt = next_node_in_subtree(self.root, self.root)
        self.assertEqual(nxt, self.child)
        self.assertIsNone(next_node_in_subtree(self.root, self.child))

    def test_combined_subtree_nodes(self):
        other_c = Concept.objects.create(dictionary=self.root_c.dictionary, label="Otro")
        other = TaxonomyNode.objects.create(taxonomy=self.tax, label="Otro", concept=other_c)
        nodes = combined_subtree_nodes(
            self.tax.pk,
            [str(self.root.uuid), str(other.uuid)],
        )
        self.assertEqual([n.label for n in nodes], ["Raíz", "Hijo", "Otro"])
