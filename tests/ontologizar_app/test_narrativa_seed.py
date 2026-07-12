from django.core.management import call_command
from django.test import TestCase

from ontologizar_app.models import (
    Concept, ConceptProperty, Dictionary, Subject, SubjectMaterial,
    SubjectTaxonomy, Taxonomy,
)


class SeedNarrativaOntologiaTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def test_seed_is_idempotent(self):
        call_command("seed_narrativa_ontologia")
        call_command("seed_narrativa_ontologia")
        subject = Subject.objects.get(slug="narrativa")
        self.assertEqual(subject.name, "Narrativa")
        self.assertTrue(subject.materials.filter(slug="intro-narrativa").exists())
        meta = Dictionary.objects.get(subject=subject, slug="ontonarrativa")
        self.assertTrue(Concept.objects.filter(dictionary=meta, label="Personaje").exists())
        self.assertTrue(Concept.objects.filter(dictionary=meta, label="Encierro").exists())
        personaje = Concept.objects.get(dictionary=meta, label="Personaje")
        self.assertEqual(
            personaje.properties.get(key="concept_type").value, "narrative_entity",
        )
        encierro = Concept.objects.get(dictionary=meta, label="Encierro")
        self.assertEqual(
            encierro.properties.get(key="concept_type").value, "narrative_motif",
        )
        heroe = Concept.objects.get(dictionary=meta, label="Héroe idealista")
        self.assertEqual(
            heroe.properties.get(key="concept_type").value, "narrative_figure",
        )

    def test_four_taxonomies_with_groups(self):
        call_command("seed_narrativa_ontologia")
        subject = Subject.objects.get(slug="narrativa")
        assignments = SubjectTaxonomy.objects.filter(subject=subject, role="class").order_by("position")
        self.assertEqual(assignments.count(), 4)
        groups = {a.taxonomy_group for a in assignments}
        self.assertEqual(groups, {"estructural", "arquetipico", "tematico", "simbolico"})
        slugs = set(assignments.values_list("taxonomy__slug", flat=True))
        self.assertEqual(slugs, {
            "narrativa", "narrativa-arquetipico",
            "narrativa-tematico", "narrativa-simbolico",
        })
        primary = assignments.filter(is_primary=True).first()
        self.assertEqual(primary.taxonomy.slug, "narrativa")
        self.assertEqual(primary.taxonomy_group, "estructural")

    def test_meta_vocabulary_has_no_instances(self):
        call_command("seed_narrativa_ontologia")
        meta = Dictionary.objects.get(slug="ontonarrativa")
        labels = set(meta.concepts.values_list("label", flat=True))
        self.assertNotIn("Don Quijote", labels)
        self.assertNotIn("Segismundo", labels)

    def test_motifs_only_in_tematico_taxonomy(self):
        call_command("seed_narrativa_ontologia")
        tematico = Taxonomy.objects.get(slug="narrativa-tematico")
        motif_nodes = tematico.nodes.filter(label="Traición", concept__isnull=False)
        self.assertTrue(motif_nodes.exists())
        estructural = Taxonomy.objects.get(slug="narrativa")
        self.assertFalse(
            estructural.nodes.filter(label="Traición", concept__isnull=False).exists()
        )


class AlignQuijoteNarrativaTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def test_align_creates_obra_and_interpretation(self):
        call_command("seed_quijote_ontologia")
        call_command("seed_narrativa_ontologia")
        call_command("align_quijote_narrativa")

        quijote_dict = Dictionary.objects.get(slug="quijote")
        obra = Concept.objects.get(dictionary=quijote_dict, label="Don Quijote de la Mancha")
        self.assertEqual(obra.properties.get(key="medium").value, "novela")
        don_q = Concept.objects.get(dictionary=quijote_dict, label="Don Quijote")
        self.assertEqual(don_q.properties.get(key="concept_type").value, "Personaje")

        from ontologizar_app.services.attributed_relations import concept_interpretations
        interpretations = concept_interpretations(don_q)
        self.assertGreaterEqual(len(interpretations), 2)
        frameworks = {r.attribution.framework for r in interpretations}
        self.assertIn("critica_literaria", frameworks)
        self.assertIn("arquetipico", frameworks)

    def test_align_places_characters_in_quijote_taxonomy(self):
        call_command("seed_quijote_ontologia")
        call_command("seed_narrativa_ontologia")
        call_command("align_quijote_narrativa")

        from ontologizar_app.models import TaxonomyNode
        tax = Taxonomy.objects.get(slug="quijote")
        placed = TaxonomyNode.objects.filter(
            taxonomy=tax, parent__label="Personajes", concept__label="Don Quijote",
        )
        self.assertTrue(placed.exists())
