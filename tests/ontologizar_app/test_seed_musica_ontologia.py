from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from ontologizar_app.models import Concept, ConceptRelation, Dictionary, Subject, Taxonomy
from research_app.models import LearningMarker, ProyectoInvestigacion


class SeedMusicaOntologiaTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        path = Path(settings.BASE_DIR) / "core_ontologia_musica_v0.1.jsonld"
        if not path.is_file():
            raise FileNotFoundError(f"Falta fixture JSON-LD: {path}")

    def test_seed_creates_musica_subject_and_dictionary(self):
        call_command("seed_musica_ontologia")
        subject = Subject.objects.get(slug="musica")
        dictionary = Dictionary.objects.get(subject=subject, slug="musica")
        self.assertEqual(subject.name, "Música")
        self.assertIn("estructuras sonoras", subject.description)
        self.assertEqual(dictionary.concepts.count(), 115)

    def test_seed_creates_six_taxonomies(self):
        call_command("seed_musica_ontologia")
        subject = Subject.objects.get(slug="musica")
        slugs = set(subject.taxonomy_assignments.values_list("taxonomy__slug", flat=True))
        self.assertEqual(
            slugs,
            {
                "musica-instrumentos",
                "musica-tecnicas",
                "musica-recursos",
                "musica-generos",
                "musica-conceptos",
                "musica-propiedades",
            },
        )

    def test_seed_loads_hundred_dictionary_terms(self):
        call_command("seed_musica_ontologia")
        dictionary = Dictionary.objects.get(subject__slug="musica", slug="musica")
        term_labels = {
            c.label for c in dictionary.concepts.all()
            if c.properties.filter(key="entity_kind", value="class").exists()
            or not c.properties.filter(key="entity_kind", value="property").exists()
        }
        self.assertIn("Guitarra", term_labels)
        self.assertIn("Intercambio modal", term_labels)
        self.assertIn("Grunge", term_labels)
        self.assertEqual(
            dictionary.concepts.exclude(properties__key="entity_kind", properties__value="property").count(),
            105,
        )

    def test_seed_imports_relation_assertions(self):
        call_command("seed_musica_ontologia")
        guitarra = Concept.objects.get(dictionary__slug="musica", label="Guitarra")
        palm = Concept.objects.get(dictionary__slug="musica", label="Palm muting")
        rel = ConceptRelation.objects.filter(source=palm, target=guitarra, relation_type="works_via").first()
        self.assertIsNotNone(rel)

    def test_seed_creates_radio_micelio_notebook_with_markers(self):
        call_command("seed_musica_ontologia")
        notebook = ProyectoInvestigacion.objects.get(acron="RM")
        self.assertEqual(notebook.titulo, "Radio Micelio")
        self.assertGreaterEqual(notebook.markers.count(), 10)
        labels = set(notebook.markers.values_list("concept_label", flat=True))
        self.assertIn("Guitarra", labels)
        self.assertIn("Grunge", labels)

    def test_seed_is_idempotent(self):
        call_command("seed_musica_ontologia")
        count_before = Concept.objects.filter(dictionary__slug="musica").count()
        markers_before = LearningMarker.objects.filter(project__acron="RM").count()
        call_command("seed_musica_ontologia")
        self.assertEqual(Concept.objects.filter(dictionary__slug="musica").count(), count_before)
        self.assertEqual(LearningMarker.objects.filter(project__acron="RM").count(), markers_before)

    def test_property_taxonomy_exists(self):
        call_command("seed_musica_ontologia")
        prop_tax = Taxonomy.objects.get(slug="musica-propiedades")
        labels = set(prop_tax.nodes.values_list("label", flat=True))
        self.assertIn("parte_de", labels)
        self.assertIn("se_ejecuta_mediante", labels)
