from django.core.management import call_command
from django.test import TestCase

from ontologizar_app.models import Concept, ConceptProperty, Dictionary, Subject, SubjectMaterial


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
            encierro.properties.get(key="concept_type").value, "narrative_function",
        )

    def test_meta_vocabulary_has_no_instances(self):
        call_command("seed_narrativa_ontologia")
        meta = Dictionary.objects.get(slug="ontonarrativa")
        labels = set(meta.concepts.values_list("label", flat=True))
        self.assertNotIn("Don Quijote", labels)
        self.assertNotIn("Segismundo", labels)


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
        self.assertGreaterEqual(len(interpretations), 1)
        self.assertEqual(interpretations[0].attribution.framework, "critica_literaria")
