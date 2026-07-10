from django.test import TestCase

from ontologizar_app.models import Concept, ConceptDefinition, Dictionary, Subject
from ontologizar_app.services.citations import (
    SourceKind,
    citation_badge,
    concept_citations,
    concept_has_terminological_reference,
    concept_provenance_level,
    format_reference_line,
    parse_reference_line,
)


class CitationsTests(TestCase):
    databases = {"default", "research_db", "ontologizar_db"}

    def test_parse_reference_line_v2(self):
        line = (
            "IUPAC Gold Book — valence | https://goldbook.iupac.org/terms/view/V06588 "
            "| referencia_terminologica | IUPAC | terminological_reference"
        )
        citation = parse_reference_line(line)
        self.assertIsNotNone(citation)
        assert citation is not None
        self.assertEqual(citation.label, "IUPAC Gold Book — valence")
        self.assertEqual(citation.kind, SourceKind.REFERENCIA_TERMINOLOGICA)
        self.assertEqual(citation.authority, "IUPAC")
        self.assertEqual(citation.authority_level, "terminological_reference")

    def test_parse_legacy_standard_alias(self):
        citation = parse_reference_line(
            "IUPAC Gold Book | https://goldbook.iupac.org/terms/view/V06588 | standard"
        )
        self.assertIsNotNone(citation)
        assert citation is not None
        self.assertEqual(citation.kind, SourceKind.REFERENCIA_TERMINOLOGICA)

    def test_citation_badge_iupac(self):
        citation = parse_reference_line(
            "IUPAC Gold Book — valence | https://goldbook.iupac.org/terms/view/V06588 "
            "| referencia_terminologica | IUPAC | terminological_reference"
        )
        assert citation is not None
        self.assertEqual(citation_badge(citation), "referencia IUPAC")

    def test_citation_badge_dataset(self):
        citation = parse_reference_line(
            "NIST Chemistry WebBook | https://webbook.nist.gov/chemistry/ | dataset | NIST | dataset"
        )
        assert citation is not None
        self.assertEqual(citation_badge(citation), "base de datos")

    def test_format_round_trip(self):
        original = parse_reference_line(
            "NIST Chemistry WebBook | https://webbook.nist.gov/chemistry/ | dataset | NIST | dataset"
        )
        assert original is not None
        restored = parse_reference_line(format_reference_line(original))
        self.assertEqual(restored, original)

    def test_concept_citations_order(self):
        subj = Subject.objects.create(slug="quimica", name="Química")
        dic = Dictionary.objects.create(subject=subj, slug="ontoquim", name="Vocabulario químico")
        concept = Concept.objects.create(dictionary=dic, label="Valencia química")
        ConceptDefinition.objects.create(
            concept=concept,
            kind="reference",
            text="NIST Chemistry WebBook | https://webbook.nist.gov/chemistry/ | dataset | NIST | dataset",
        )
        ConceptDefinition.objects.create(
            concept=concept,
            kind="reference",
            text=(
                "IUPAC Gold Book — valence | https://goldbook.iupac.org/terms/view/V06588 "
                "| referencia_terminologica | IUPAC | terminological_reference"
            ),
        )
        citations = concept_citations(concept)
        self.assertEqual(len(citations), 2)
        self.assertEqual(citations[0].authority, "IUPAC")
        self.assertTrue(concept_has_terminological_reference(concept))
        self.assertEqual(concept_provenance_level(concept), "terminological_reference")
