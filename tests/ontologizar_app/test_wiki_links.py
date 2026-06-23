from django.test import TestCase

from ontologizar_app.models import Concept, Dictionary, Subject
from ontologizar_app.services.subject_body import render_subject_body
from ontologizar_app.services.topic_body import render_topic_body
from ontologizar_app.services.wiki_links import clear_link_index_cache, linkify_plaintext


class WikiLinksTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def setUp(self):
        clear_link_index_cache()

    def test_autolink_concept_and_subject(self):
        subj = Subject.objects.create(slug="micologia", name="Micología")
        dic = Dictionary.objects.create(subject=subj, slug="vocab", name="Vocabulario")
        Concept.objects.create(dictionary=dic, label="Micelio")
        html = linkify_plaintext("El Micelio crece en la Micología.", site_root="/")
        self.assertIn('href="/biblioteca/temas/', html)
        self.assertIn('href="/biblioteca/asignaturas/micologia/"', html)

    def test_wiki_bracket_syntax(self):
        subj = Subject.objects.create(slug="micologia", name="Micología")
        html = linkify_plaintext("Ver [[asignatura:micologia|micología avanzada]]", site_root="/")
        self.assertIn('href="/biblioteca/asignaturas/micologia/"', html)
        self.assertIn("micología avanzada", html)

    def test_subject_body_no_cross_domain_autolinks(self):
        subj = Subject.objects.create(slug="ciencias-naturales", name="Ciencias Naturales")
        mic = Subject.objects.create(slug="micologia", name="Micología")
        dic = Dictionary.objects.create(subject=mic, slug="v", name="V")
        Concept.objects.create(dictionary=dic, label="Micelio")
        from ontologizar_app.models import SubjectMaterial
        SubjectMaterial.objects.create(
            subject=subj, slug="u", title="Unidad",
            body="Estudia el Micelio y la asignatura Micología.",
        )
        html = render_subject_body(subj, site_root="/")
        self.assertNotIn("/biblioteca/temas/", html)
        self.assertNotIn("/biblioteca/asignaturas/micologia/", html)

    def test_topic_body_links_relations(self):
        subj = Subject.objects.create(slug="m", name="M")
        dic = Dictionary.objects.create(subject=subj, slug="d", name="D")
        a = Concept.objects.create(dictionary=dic, label="A")
        b = Concept.objects.create(dictionary=dic, label="B")
        from ontologizar_app.models import ConceptRelation
        ConceptRelation.objects.create(source=a, target=b, relation_type="related")
        html = render_topic_body(a, site_root="/")
        self.assertIn(f'/biblioteca/temas/{b.uuid}/', html)
