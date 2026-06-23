from django.test import TestCase
from django.urls import reverse

from ontologizar_app.models import (
    Concept, ConceptDefinition, ConceptProperty, ConceptRelation, Dictionary, Subject,
)
from ontologizar_app.services.concept_indicators import compute_concept_indicators


class ConceptIndicatorsTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def setUp(self):
        self.micologia = Subject.objects.create(slug="micologia", name="Micología")
        self.emociones = Subject.objects.create(slug="emociones", name="Emociones")
        self.dict_hongos = Dictionary.objects.create(subject=self.micologia, slug="ontohongo", name="Hongos")
        self.dict_emo = Dictionary.objects.create(subject=self.emociones, slug="ontoemo", name="Emo")

    def _concept(self, dictionary, label):
        return Concept.objects.create(dictionary=dictionary, label=label)

    def _reload(self, concept):
        return Concept.objects.prefetch_related(
            "definitions", "properties",
            "outgoing_relations__target__dictionary",
            "incoming_relations__source__dictionary",
        ).get(pk=concept.pk)

    def test_empty_concept_shows_no_content(self):
        c = self._reload(self._concept(self.dict_hongos, "Vacío"))
        ind = compute_concept_indicators(c)
        self.assertTrue(ind.is_empty)
        self.assertFalse(ind.has_relations)
        self.assertFalse(ind.has_properties)
        self.assertFalse(ind.has_examples)
        self.assertFalse(ind.has_cross_ontology_links)
        self.assertFalse(ind.has_official_source)

    def test_content_only(self):
        c = self._concept(self.dict_hongos, "Micelio")
        ConceptDefinition.objects.create(concept=c, text="Red de hifas.", kind="definition")
        ind = compute_concept_indicators(self._reload(c))
        self.assertTrue(ind.has_content)
        self.assertFalse(ind.is_empty)

    def test_relations(self):
        a = self._concept(self.dict_hongos, "Hifa")
        b = self._concept(self.dict_hongos, "Micelio")
        ConceptRelation.objects.create(source=a, target=b, relation_type="partOf")
        ind = compute_concept_indicators(self._reload(a))
        self.assertTrue(ind.has_relations)

    def test_ontology_properties(self):
        c = self._concept(self.dict_hongos, "Conidióforo")
        ConceptProperty.objects.create(concept=c, key="dominio", value="micología")
        ConceptProperty.objects.create(concept=c, key="hashtag", value="#ontoHongo")
        ind = compute_concept_indicators(self._reload(c))
        self.assertTrue(ind.has_properties)

    def test_examples(self):
        c = self._concept(self.dict_hongos, "Espora")
        ConceptDefinition.objects.create(
            concept=c, text="Esporas de *Amanita muscaria*.", kind="example",
        )
        ind = compute_concept_indicators(self._reload(c))
        self.assertTrue(ind.has_examples)
        self.assertTrue(ind.has_content)

    def test_cross_ontology_relation(self):
        hongo = self._concept(self.dict_hongos, "Dopamina ref")
        emo = self._concept(self.dict_emo, "Alegría")
        ConceptRelation.objects.create(source=hongo, target=emo, relation_type="related")
        ind = compute_concept_indicators(self._reload(hongo))
        self.assertTrue(ind.has_cross_ontology_links)

    def test_cross_ontology_property_sameas(self):
        c = self._concept(self.dict_hongos, "Basidio")
        ConceptProperty.objects.create(
            concept=c, key="sameAs",
            value="http://purl.obolibrary.org/obo/UBERON_0000956",
        )
        ind = compute_concept_indicators(self._reload(c))
        self.assertTrue(ind.has_cross_ontology_links)

    def test_cross_ontology_wiki_link(self):
        c = self._concept(self.dict_hongos, "Bosque")
        ConceptDefinition.objects.create(
            concept=c,
            text="Relacionado con [[Alegría]] en otra ontología.",
            kind="definition",
        )
        self._concept(self.dict_emo, "Alegría")
        ind = compute_concept_indicators(self._reload(c))
        self.assertTrue(ind.has_cross_ontology_links)

    def test_official_source_orcid_and_institution(self):
        c = self._concept(self.dict_hongos, "Micorrízico")
        ConceptProperty.objects.create(concept=c, key="orcid", value="0000-0002-1825-0097")
        ConceptProperty.objects.create(
            concept=c, key="institution",
            value="Real Jardín Botánico, CSIC",
        )
        ConceptProperty.objects.create(
            concept=c, key="source_url",
            value="https://www.mycobank.org/",
        )
        ind = compute_concept_indicators(self._reload(c))
        self.assertTrue(ind.has_official_source)

    def test_official_source_reference_definition(self):
        c = self._concept(self.dict_hongos, "Saprófito")
        ConceptDefinition.objects.create(
            concept=c,
            text="Kirk et al. (2008). Dictionary of the Fungi.",
            kind="reference",
        )
        ind = compute_concept_indicators(self._reload(c))
        self.assertTrue(ind.has_official_source)

    def test_provenance_keys_not_counted_as_ontology_properties(self):
        c = self._concept(self.dict_hongos, "Parásito")
        ConceptProperty.objects.create(concept=c, key="doi", value="10.1038/nature12345")
        ind = compute_concept_indicators(self._reload(c))
        self.assertTrue(ind.has_official_source)
        self.assertFalse(ind.has_properties)

    def test_full_stack_concept(self):
        c = self._concept(self.dict_hongos, "Micelio completo")
        other = self._concept(self.dict_emo, "Tristeza")
        ConceptDefinition.objects.create(concept=c, text="Definición base.", kind="definition")
        ConceptDefinition.objects.create(concept=c, text="Ejemplo en roble.", kind="example")
        ConceptProperty.objects.create(concept=c, key="dominio", value="micología")
        ConceptProperty.objects.create(concept=c, key="orcid", value="0000-0001-2345-6789")
        ConceptRelation.objects.create(source=c, target=other, relation_type="related")
        ind = compute_concept_indicators(self._reload(c))
        self.assertTrue(ind.has_content)
        self.assertTrue(ind.has_relations)
        self.assertTrue(ind.has_properties)
        self.assertTrue(ind.has_examples)
        self.assertTrue(ind.has_cross_ontology_links)
        self.assertTrue(ind.has_official_source)
        self.assertFalse(ind.is_empty)


class DictionaryPageIndicatorsTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def test_dictionary_page_renders_all_indicator_types(self):
        micologia = Subject.objects.create(slug="micologia", name="Micología")
        emociones = Subject.objects.create(slug="emociones", name="Emociones")
        d_hongos = Dictionary.objects.create(subject=micologia, slug="ontohongo", name="Hongos")
        d_emo = Dictionary.objects.create(subject=emociones, slug="ontoemo", name="Emo")

        empty = Concept.objects.create(dictionary=d_hongos, label="Sin texto")
        with_rel = Concept.objects.create(dictionary=d_hongos, label="Con relación")
        with_prop = Concept.objects.create(dictionary=d_hongos, label="Con propiedad")
        with_ex = Concept.objects.create(dictionary=d_hongos, label="Con ejemplo")
        with_cross = Concept.objects.create(dictionary=d_hongos, label="Con enlace externo")
        with_src = Concept.objects.create(dictionary=d_hongos, label="Con fuente")
        emo = Concept.objects.create(dictionary=d_emo, label="Remoto")

        ConceptRelation.objects.create(source=with_rel, target=empty, relation_type="related")
        ConceptProperty.objects.create(concept=with_prop, key="dominio", value="test")
        ConceptDefinition.objects.create(concept=with_ex, text="Un ejemplo.", kind="example")
        ConceptRelation.objects.create(source=with_cross, target=emo, relation_type="related")
        ConceptProperty.objects.create(concept=with_src, key="orcid", value="0000-0002-1825-0097")

        url = reverse("biblioteca:dictionary", kwargs={"subject_slug": "micologia", "dict_slug": "ontohongo"})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "concept-indicator--empty")
        self.assertContains(r, "concept-indicator--relations")
        self.assertContains(r, "concept-indicator--properties")
        self.assertContains(r, "concept-indicator--examples")
        self.assertContains(r, "concept-indicator--external")
        self.assertContains(r, "concept-indicator--source")
        self.assertContains(r, "Leyenda de iconos")

    def test_topic_page_shows_indicators(self):
        micologia = Subject.objects.create(slug="micologia", name="Micología")
        d_hongos = Dictionary.objects.create(subject=micologia, slug="ontohongo", name="Hongos")
        c = Concept.objects.create(dictionary=d_hongos, label="Micelio")
        ConceptDefinition.objects.create(concept=c, text="Red de hifas.", kind="definition")
        ConceptProperty.objects.create(concept=c, key="dominio", value="micología")
        ConceptProperty.objects.create(concept=c, key="orcid", value="0000-0002-1825-0097")
        other = Concept.objects.create(dictionary=d_hongos, label="Hifa")
        ConceptRelation.objects.create(source=other, target=c, relation_type="partOf")

        r = self.client.get(reverse("biblioteca:topic", kwargs={"uuid": c.uuid}))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "concept-indicators")
        self.assertContains(r, "concept-indicator--relations")
        self.assertContains(r, "concept-indicator--properties")
        self.assertContains(r, "concept-indicator--source")
        self.assertContains(r, 'href="#topic-relations"')
        self.assertContains(r, 'id="topic-relations"')
        self.assertContains(r, 'id="topic-properties"')
        self.assertContains(r, 'id="topic-sources"')
        self.assertContains(r, "topic-section-badge")
        self.assertFalse(compute_concept_indicators(c).is_empty)
