from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from ontologizar_app.models import Concept, ConceptDefinition, ConceptProperty, Dictionary, Subject, SubjectMaterial, Taxonomy, TaxonomyNode
from ontologizar_app.services.taxonomy_import import import_taxonomy_from_json


class CmsTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def setUp(self):
        self.client = Client()

    def test_cms_requires_login(self):
        r = self.client.get("/cms/")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/cms/login/", r.url)

    def test_ensure_cms_user(self):
        call_command("ensure_cms_user")
        self.assertTrue(get_user_model().objects.filter(username="ivansimo").exists())

    def test_concept_shared_across_taxonomies(self):
        subj = Subject.objects.create(slug="nat", name="Naturaleza")
        dic = Dictionary.objects.create(subject=subj, slug="vida", name="Vida")
        c = Concept.objects.create(dictionary=dic, label="Micelio")
        t1 = Taxonomy.objects.create(slug="fungi", name="Fungi")
        t2 = Taxonomy.objects.create(slug="eco", name="Ecología")
        TaxonomyNode.objects.create(taxonomy=t1, label="Micelio", concept=c)
        TaxonomyNode.objects.create(taxonomy=t2, label="Micelio", concept=c)
        self.assertEqual(TaxonomyNode.objects.filter(concept=c).count(), 2)

    def test_taxonomy_import_reuses_concept(self):
        subj = Subject.objects.create(slug="s1", name="S")
        dic = Dictionary.objects.create(subject=subj, slug="d1", name="D")
        tax = Taxonomy.objects.create(slug="t-import", name="T")
        data = {"Raíz": {"Hoja": None}}
        ok, _, _ = import_taxonomy_from_json(tax, dic, data)
        self.assertTrue(ok)
        self.assertEqual(Concept.objects.filter(dictionary=dic).count(), 2)

    def test_topic_page_public_and_jsonld(self):
        subj = Subject.objects.create(slug="mus", name="Música")
        dic = Dictionary.objects.create(subject=subj, slug="emo", name="Emo")
        c = Concept.objects.create(dictionary=dic, label="Alegría")
        ConceptProperty.objects.create(concept=c, key="intensidad", value="alta")
        r = self.client.get(f"/biblioteca/temas/{c.uuid}/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Alegría")
        self.assertContains(r, "application/ld+json")
        self.assertContains(r, "additionalProperty")

    def test_topic_edit_requires_login(self):
        subj = Subject.objects.create(slug="mus", name="Música")
        dic = Dictionary.objects.create(subject=subj, slug="emo", name="Emo")
        c = Concept.objects.create(dictionary=dic, label="Alegría")
        r = self.client.get(reverse("biblioteca:topic_edit", kwargs={"uuid": c.uuid}))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/cms/login/", r.url)

    def test_topic_edit_saves_definition(self):
        call_command("ensure_cms_user")
        User = get_user_model()
        self.client.login(username="ivansimo", password="12345678")
        subj = Subject.objects.create(slug="mus", name="Música")
        dic = Dictionary.objects.create(subject=subj, slug="emo", name="Emo")
        c = Concept.objects.create(dictionary=dic, label="Alegría")
        r = self.client.post(
            reverse("biblioteca:topic_edit", kwargs={"uuid": c.uuid}),
            {"body": "Emoción de valencia positiva.\n\nSegundo párrafo."},
        )
        self.assertEqual(r.status_code, 302)
        definition = ConceptDefinition.objects.get(concept=c, kind="definition", is_active=True)
        self.assertIn("Segundo párrafo", definition.text)
        public = self.client.get(reverse("biblioteca:topic", kwargs={"uuid": c.uuid}))
        self.assertContains(public, "Editar")
        self.assertContains(public, "Segundo párrafo")

    def test_topic_edit_saves_references(self):
        call_command("ensure_cms_user")
        self.client.login(username="ivansimo", password="12345678")
        subj = Subject.objects.create(slug="quimica", name="Química")
        dic = Dictionary.objects.create(subject=subj, slug="ontoquim", name="Vocabulario químico")
        c = Concept.objects.create(dictionary=dic, label="Valencia química")
        ref_line = (
            "IUPAC Gold Book — valence | https://goldbook.iupac.org/terms/view/V06588 "
            "| referencia_terminologica | IUPAC | terminological_reference"
        )
        r = self.client.post(
            reverse("biblioteca:topic_edit", kwargs={"uuid": c.uuid}),
            {"body": "Definición editorial.", "references": ref_line},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(ConceptDefinition.objects.filter(concept=c, kind="reference").count(), 1)
        public = self.client.get(reverse("biblioteca:topic", kwargs={"uuid": c.uuid}))
        self.assertContains(public, "Fuentes y referencias")
        self.assertContains(public, "referencia IUPAC")
        self.assertContains(public, "goldbook.iupac.org")

    def test_topic_page_shows_login_to_edit_when_anonymous(self):
        subj = Subject.objects.create(slug="mus", name="Música")
        dic = Dictionary.objects.create(subject=subj, slug="emo", name="Emo")
        c = Concept.objects.create(dictionary=dic, label="Alegría")
        r = self.client.get(reverse("biblioteca:topic", kwargs={"uuid": c.uuid}))
        self.assertContains(r, "Iniciar sesión para editar")

    def test_subject_edit_saves_description(self):
        call_command("ensure_cms_user")
        self.client.login(username="ivansimo", password="12345678")
        subj = Subject.objects.create(slug="nat", name="Naturaleza", description="Antes")
        r = self.client.post(
            reverse("biblioteca:subject_edit", kwargs={"slug": subj.slug}),
            {"description": "Texto wiki nuevo."},
        )
        self.assertEqual(r.status_code, 302)
        subj.refresh_from_db()
        self.assertEqual(subj.description, "Texto wiki nuevo.")

    def test_material_edit_saves_body(self):
        call_command("ensure_cms_user")
        self.client.login(username="ivansimo", password="12345678")
        subj = Subject.objects.create(slug="nat", name="Naturaleza")
        mat = SubjectMaterial.objects.create(subject=subj, slug="u1", title="Unidad", body="Viejo")
        r = self.client.post(
            reverse("biblioteca:material_edit", kwargs={"slug": subj.slug, "mat_slug": mat.slug}),
            {"title": "Unidad", "summary": "", "body": "Contenido actualizado."},
        )
        self.assertEqual(r.status_code, 302)
        mat.refresh_from_db()
        self.assertEqual(mat.body, "Contenido actualizado.")
