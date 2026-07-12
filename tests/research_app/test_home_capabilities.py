from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from research_app.capability_registry import (
    COMPETENCY_SPECS,
    capabilities_by_category,
    capabilities_grouped_by_family,
    get_public_capability_by_slug,
    legacy_slug_to_family,
)


class CapabilityRegistryTests(TestCase):
    def test_interpretive_capabilities_registered(self):
        interpretive = capabilities_by_category("interpretive")
        labels = {c["label"] for c in interpretive}
        self.assertEqual(labels, {"Narrar", "Arquetipar", "Interpretar", "Argumentar"})

    def test_digital_capabilities_count(self):
        digital = capabilities_by_category("digital")
        self.assertEqual(len(digital), 8)

    def test_all_specs_have_category(self):
        for spec in COMPETENCY_SPECS:
            self.assertIn(spec["category"], ("digital", "interpretive"))

    def test_legacy_slug_to_family_mapping(self):
        self.assertEqual(legacy_slug_to_family("ontology"), "structure")
        self.assertEqual(legacy_slug_to_family("dataset"), "structure")
        self.assertEqual(legacy_slug_to_family("publish"), "publish")
        self.assertEqual(legacy_slug_to_family("geodata"), "explore")
        self.assertEqual(legacy_slug_to_family("logs"), "explore")
        self.assertIsNone(legacy_slug_to_family("preserve"))

    def test_capabilities_grouped_by_family(self):
        families = capabilities_grouped_by_family("digital")
        labels = [f["label"] for f in families]
        self.assertEqual(labels, ["Estructurar", "Publicar", "Explorar"])
        structure_actions = {a["slug"] for a in families[0]["actions"]}
        self.assertEqual(structure_actions, {"ontology", "dataset"})
        self.assertEqual(families[0]["actions"][0]["label"], "Vincular conocimiento")

    def test_arquetipar_has_controlled_copy(self):
        cap = get_public_capability_by_slug("arquetipar")
        self.assertIsNotNone(cap)
        assert cap is not None
        self.assertIn("intro_note", cap)
        self.assertIn("lista cerrada", cap["intro_note"])
        self.assertIn("funciones, patrones y figuras recurrentes", cap["tagline"])
        self.assertNotIn("Jung", cap["definition"])


class HomeViewTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def test_home_shows_both_capability_sections(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Funcionalidades", content)
        self.assertIn("Competencias de investigación", content)
        self.assertIn("Estructurar", content)
        self.assertIn("Publicar", content)
        self.assertIn("Explorar", content)
        self.assertIn("Plataforma para organizaciones que producen conocimiento", content)
        self.assertIn("nuevas formas de narración", content)

    def test_home_groups_digital_capabilities_by_family(self):
        response = self.client.get(reverse("home"))
        content = response.content.decode()
        self.assertIn("Vincular conocimiento", content)
        self.assertIn("Catalogar", content)

    def test_home_lists_interpretive_capabilities(self):
        response = self.client.get(reverse("home"))
        content = response.content.decode()
        self.assertIn("Narrar", content)
        self.assertIn("Arquetipar", content)
        self.assertIn("Interpretar", content)
        self.assertIn("Argumentar", content)
        self.assertIn("próximamente", content)

    def test_home_capability_links_use_reverse(self):
        response = self.client.get(reverse("home"))
        content = response.content.decode()
        narrar_url = reverse("capability_detail", kwargs={"public_slug": "narrar"})
        self.assertIn(f'href="{narrar_url}"', content)


class InterpretiveCapabilityDetailTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def test_narrar_page_without_seed_shows_hint(self):
        response = self.client.get(reverse("capability_detail", kwargs={"public_slug": "narrar"}))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Narrar", content)
        self.assertIn("seed_narrativa_ontologia", content)

    def test_arquetipar_page_shows_intro_note(self):
        response = self.client.get(reverse("capability_detail", kwargs={"public_slug": "arquetipar"}))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("lista cerrada", content)
        self.assertIn("Figuras narrativas", content)

    def test_interpretar_page_without_seed_shows_hint(self):
        response = self.client.get(reverse("capability_detail", kwargs={"public_slug": "interpretar"}))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Interpretar", content)
        self.assertIn("align_quijote_narrativa", content)

    def test_narrar_page_with_seed_links_biblioteca(self):
        call_command("seed_narrativa_ontologia")
        response = self.client.get(reverse("capability_detail", kwargs={"public_slug": "narrar"}))
        content = response.content.decode()
        subject_url = reverse("biblioteca:subject", kwargs={"slug": "narrativa"})
        self.assertIn(subject_url, content)
        self.assertIn("Vocabulario narrativo", content)

    def test_arquetipar_lists_figure_types_not_motifs(self):
        call_command("seed_narrativa_ontologia")
        response = self.client.get(reverse("capability_detail", kwargs={"public_slug": "arquetipar"}))
        content = response.content.decode()
        self.assertIn("Héroe idealista", content)
        self.assertIn("Mentor", content)
        self.assertNotIn("Traición", content)
        self.assertNotIn("Revelación", content)
        self.assertNotIn("Personaje", content)

    def test_interpretar_with_aligned_quijote_shows_readings(self):
        call_command("seed_quijote_ontologia")
        call_command("seed_narrativa_ontologia")
        call_command("align_quijote_narrativa")
        response = self.client.get(reverse("capability_detail", kwargs={"public_slug": "interpretar"}))
        content = response.content.decode()
        self.assertIn("El Quijote", content)
        self.assertIn("interpreted_as", content)
        self.assertIn("Reconocimiento", content)

    def test_argumentar_is_coming_soon(self):
        response = self.client.get(reverse("capability_detail", kwargs={"public_slug": "argumentar"}))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Pr\xc3\xb3ximamente", response.content)
