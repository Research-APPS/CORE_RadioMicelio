from django.test import SimpleTestCase

from airam_app.services.semantic_relations import (
    EXPLORATION_LENSES,
    LEGACY_MAP,
    RELATION_REGISTRY,
    RELATION_TYPES,
    is_known_relation,
    normalize_relation_type,
    relation_lens,
    verbalize_relation,
)


class NormalizeRelationTypeTests(SimpleTestCase):
    def test_legacy_camelcase_partof_normalizes_to_snake_case(self):
        self.assertEqual(normalize_relation_type("partOf"), "part_of")

    def test_canonical_type_unchanged(self):
        self.assertEqual(normalize_relation_type("enables"), "enables")
        self.assertEqual(normalize_relation_type("related"), "related")

    def test_unknown_type_falls_back_to_related(self):
        self.assertEqual(normalize_relation_type("algo_inventado"), "related")

    def test_empty_falls_back_to_related(self):
        self.assertEqual(normalize_relation_type(""), "related")

    def test_is_known_relation(self):
        self.assertTrue(is_known_relation("enables"))
        self.assertTrue(is_known_relation("partOf"))
        self.assertFalse(is_known_relation("algo_inventado"))


class LegacyMapTests(SimpleTestCase):
    def test_all_legacy_skos_types_have_templates(self):
        for legacy in ("related", "broader", "narrower"):
            self.assertIn(legacy, LEGACY_MAP)
            self.assertIn("icon", LEGACY_MAP[legacy])
            self.assertIn("question", LEGACY_MAP[legacy])
            self.assertIn("sentence", LEGACY_MAP[legacy])
            self.assertIn("lens", LEGACY_MAP[legacy])

    def test_part_of_is_not_in_legacy_map_but_in_registry(self):
        self.assertNotIn("part_of", LEGACY_MAP)
        self.assertIn("part_of", RELATION_REGISTRY)


class ExplorationLensesTests(SimpleTestCase):
    def test_lenses_have_icon_and_label(self):
        self.assertGreater(len(EXPLORATION_LENSES), 0)
        for slug, lens in EXPLORATION_LENSES.items():
            self.assertIn("icon", lens)
            self.assertIn("label", lens)

    def test_every_relation_type_has_a_valid_lens(self):
        all_entries = {**LEGACY_MAP, **RELATION_REGISTRY}
        for relation_type, entry in all_entries.items():
            self.assertIn(
                entry["lens"], EXPLORATION_LENSES,
                f"{relation_type} declara una lente desconocida: {entry['lens']}",
            )

    def test_relation_lens_helper(self):
        self.assertEqual(relation_lens("enables"), "funcionamiento")
        self.assertEqual(relation_lens("partOf"), "componentes")
        self.assertEqual(relation_lens("monta_a"), "personas")


class VerbalizeRelationTests(SimpleTestCase):
    def test_enables_outgoing(self):
        v = verbalize_relation("Espora", "Dispersión", "enables")
        self.assertEqual(v.icon, "🌬️")
        self.assertEqual(v.question, "¿Qué permite Espora?")
        self.assertEqual(v.sentence, "Espora permite Dispersión.")
        self.assertEqual(v.relation_type, "enables")
        self.assertEqual(v.lens, "funcionamiento")

    def test_enables_incoming_uses_inverse_template(self):
        v = verbalize_relation("Espora", "Dispersión", "enables", direction="in")
        self.assertEqual(v.question, "¿Qué hace posible a Dispersión?")
        self.assertEqual(v.sentence, "Dispersión es posible gracias a Espora.")
        self.assertEqual(v.direction, "in")

    def test_part_of_legacy_camelcase_input(self):
        v = verbalize_relation("Correa", "Distribución", "partOf")
        self.assertEqual(v.relation_type, "part_of")
        self.assertEqual(v.sentence, "Correa es parte de Distribución.")

    def test_unknown_relation_falls_back_to_related_verbalization(self):
        v = verbalize_relation("A", "B", "no_existe")
        self.assertEqual(v.relation_type, "related")
        self.assertEqual(v.sentence, "A se relaciona con B.")

    def test_quijote_relation_monta_a(self):
        v = verbalize_relation("Don Quijote", "Rocinante", "monta_a")
        self.assertEqual(v.sentence, "Don Quijote monta a Rocinante.")
        self.assertEqual(v.question, "¿A qué monta Don Quijote?")

    def test_all_relation_types_are_verbalizable_without_error(self):
        for relation_type in RELATION_TYPES:
            v = verbalize_relation("Origen", "Destino", relation_type)
            self.assertTrue(v.sentence)
            self.assertTrue(v.question)
