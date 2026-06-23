from django.test import TestCase

from ontologizar_app.models import (
    Concept, ConceptDefinition, ConceptProperty, ConceptRelation, Dictionary, Subject,
)
from ontologizar_app.services.concept_indicators import topic_indicator_anchors
from ontologizar_app.services.topic_body import render_topic_body


class TopicBodySectionsTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def test_sections_have_anchors_and_badges(self):
        subj = Subject.objects.create(slug="m", name="M")
        dic = Dictionary.objects.create(subject=subj, slug="d", name="D")
        c = Concept.objects.create(dictionary=dic, label="Tema")
        other = Concept.objects.create(dictionary=dic, label="Otro")
        ConceptDefinition.objects.create(concept=c, text="Definición.", kind="definition")
        ConceptDefinition.objects.create(concept=c, text="Un ejemplo.", kind="example")
        ConceptProperty.objects.create(concept=c, key="dominio", value="test")
        ConceptProperty.objects.create(concept=c, key="orcid", value="0000-0001-2345-6789")
        ConceptRelation.objects.create(source=c, target=other, relation_type="related")

        html = render_topic_body(c, site_root="/")
        self.assertIn('id="topic-definition"', html)
        self.assertIn('id="topic-examples"', html)
        self.assertIn('id="topic-properties"', html)
        self.assertIn('id="topic-sources"', html)
        self.assertIn('id="topic-relations"', html)
        self.assertIn("topic-section-badge", html)
        self.assertIn("topic-property-item", html)
        self.assertIn("topic-source-item", html)

    def test_cross_relations_anchor_to_cross_section(self):
        mic = Subject.objects.create(slug="micologia", name="Micología")
        emo = Subject.objects.create(slug="emociones", name="Emociones")
        d1 = Dictionary.objects.create(subject=mic, slug="h", name="H")
        d2 = Dictionary.objects.create(subject=emo, slug="e", name="E")
        a = Concept.objects.create(dictionary=d1, label="A")
        b = Concept.objects.create(dictionary=d2, label="B")
        ConceptRelation.objects.create(source=a, target=b, relation_type="related")

        html = render_topic_body(a, site_root="/")
        self.assertIn('id="topic-cross-ontology"', html)
        anchors = topic_indicator_anchors(a)
        self.assertEqual(anchors.relations, anchors.cross)
