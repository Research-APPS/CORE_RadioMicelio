from django.test import TestCase

from ontologizar_app.models import (
    AttributedRelation, Concept, ConceptDefinition, ConceptRelation, Dictionary, Subject,
)
from ontologizar_app.services.attributed_relations import (
    concept_interpretations,
    create_attributed_relation,
    interpretation_is_complete,
)
from ontologizar_app.services.citations import SourceKind, parse_reference_line


class AttributedRelationTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def setUp(self):
        subj = Subject.objects.create(slug="narrativa", name="Narrativa")
        self.meta = Dictionary.objects.create(subject=subj, slug="ontonarrativa", name="Meta")
        self.corpus = Dictionary.objects.create(
            subject=Subject.objects.create(slug="lengua", name="Lengua"),
            slug="quijote", name="Quijote",
        )
        self.personaje_type = Concept.objects.create(dictionary=self.meta, label="Personaje")
        self.reconocimiento = Concept.objects.create(dictionary=self.meta, label="Reconocimiento")
        self.don_q = Concept.objects.create(dictionary=self.corpus, label="Don Quijote")

    def test_factual_relation_attribution(self):
        attr = create_attributed_relation(
            self.don_q, self.personaje_type, "related",
            authority_layer="factual",
            source_work="Demo",
        )
        self.assertEqual(attr.authority_layer, "factual")
        self.assertTrue(interpretation_is_complete(attr))

    def test_interpretive_relation_requires_source(self):
        attr = create_attributed_relation(
            self.don_q, self.reconocimiento, "interpreted_as",
            authority_layer="interpretive",
            framework="critica_literaria",
        )
        self.assertFalse(interpretation_is_complete(attr))

        attr.source_work = "Monografía X"
        attr.asserted_by = "Autor Y"
        attr.save()
        self.assertTrue(interpretation_is_complete(attr))

    def test_concept_interpretations_lists_interpretive_only(self):
        create_attributed_relation(
            self.don_q, self.reconocimiento, "interpreted_as",
            authority_layer="interpretive",
            framework="critica_literaria",
            asserted_by="Autor",
            source_work="Estudio",
        )
        create_attributed_relation(
            self.don_q, self.personaje_type, "related",
            authority_layer="factual",
        )
        views = concept_interpretations(self.don_q)
        self.assertEqual(len(views), 1)
        self.assertEqual(views[0].relation_type, "interpreted_as")

    def test_one_to_one_attribution_per_relation(self):
        create_attributed_relation(self.don_q, self.personaje_type, "related")
        self.assertEqual(AttributedRelation.objects.count(), 1)
        create_attributed_relation(
            self.don_q, self.personaje_type, "related",
            source_work="Actualizado",
        )
        self.assertEqual(AttributedRelation.objects.count(), 1)
        rel = ConceptRelation.objects.get(source=self.don_q, target=self.personaje_type)
        self.assertEqual(rel.attribution.source_work, "Actualizado")


class NarrativaCitationsTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def test_parse_academic_source_with_locator(self):
        line = (
            "Don Quijote | https://example.org/quijote | obra_literaria | "
            "Cervantes | primary | Cap. I"
        )
        citation = parse_reference_line(line)
        assert citation is not None
        self.assertEqual(citation.kind, SourceKind.OBRA_LITERARIA)
        self.assertEqual(citation.locator, "Cap. I")
        self.assertEqual(citation.authority_level, "primary")

    def test_definition_primary_kind(self):
        subj = Subject.objects.create(slug="narrativa", name="Narrativa")
        dic = Dictionary.objects.create(subject=subj, slug="ontonarrativa", name="Meta")
        concept = Concept.objects.create(dictionary=dic, label="Personaje")
        ConceptDefinition.objects.create(
            concept=concept, kind="definition_primary",
            text="Definición parafraseada verificable.", is_active=True,
        )
        self.assertTrue(concept.definitions.filter(kind="definition_primary").exists())
