from __future__ import annotations

import re
from dataclasses import dataclass

from ontologizar_app.models import Concept, Dictionary

# Metadatos de procedencia / fuente científica (ORCID, DOI, institución…)
PROVENANCE_PROPERTY_KEYS = frozenset({
    "orcid", "source_url", "source", "fuente", "doi", "isbn", "citation",
    "bibliographic_citation", "institution", "institucion", "institución",
    "provider", "ontology_uri", "wikidata", "dbpedia", "neurolex_id",
    "nifstd_id", "purl", "prov_wasderivedfrom", "derived_from",
})

# Enlaces explícitos hacia otras ontologías / vocabularios externos
CROSS_ONTOLOGY_PROPERTY_KEYS = frozenset({
    "sameas", "same_as", "seealso", "see_also", "equivalentclass",
    "exactmatch", "closematch", "broadmatch", "narrowmatch",
    "owl_sameas", "skos_exactmatch", "external_id",
})

_WIKI_BRACKET = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
_EXTERNAL_URI = re.compile(r"^https?://", re.I)

# Anclas en la ficha pública del tema (iconos → sección)
ANCHOR_EMPTY = "topic-empty"
ANCHOR_CONTENT = "topic-definition"
ANCHOR_EXAMPLES = "topic-examples"
ANCHOR_RELATIONS = "topic-relations"
ANCHOR_PROPERTIES = "topic-properties"
ANCHOR_CROSS = "topic-cross-ontology"
ANCHOR_SOURCES = "topic-sources"


@dataclass(frozen=True)
class ConceptIndicators:
    has_content: bool
    has_relations: bool
    has_properties: bool
    has_examples: bool
    has_cross_ontology_links: bool
    has_official_source: bool

    @property
    def is_empty(self) -> bool:
        return not self.has_content


def _norm_key(key: str) -> str:
    return key.lower().replace("-", "_").replace(" ", "_")


def _is_ontology_property(key: str) -> bool:
    nk = _norm_key(key)
    return nk not in PROVENANCE_PROPERTY_KEYS and nk not in CROSS_ONTOLOGY_PROPERTY_KEYS


def _property_implies_official_source(key: str, value: str) -> bool:
    nk = _norm_key(key)
    value = value.strip()
    if not value:
        return False
    if nk in PROVENANCE_PROPERTY_KEYS:
        return True
    if nk == "orcid" or value.startswith("https://orcid.org/"):
        return True
    return nk.endswith("_url") and _EXTERNAL_URI.match(value)


def _property_implies_cross_ontology(key: str, value: str) -> bool:
    nk = _norm_key(key)
    value = value.strip()
    if nk in CROSS_ONTOLOGY_PROPERTY_KEYS and value:
        return True
    if _EXTERNAL_URI.match(value) and nk not in PROVENANCE_PROPERTY_KEYS:
        if any(host in value.lower() for host in (
            "wikidata.org", "dbpedia.org", "neurolex.org", "bioportal",
            "ebi.ac.uk", "ols4", "w3id.org", "purl.obolibrary.org",
        )):
            return True
    return False


def _wiki_links_other_dictionaries(concept: Concept, text: str) -> bool:
    if not text or "[[" not in text:
        return False
    for m in _WIKI_BRACKET.finditer(text):
        key = m.group(1).strip()
        if key.lower().startswith("asignatura:"):
            slug = key.split(":", 1)[1].lower()
            if slug != concept.dictionary.subject.slug:
                return True
    labels = [
        m.group(1).strip()
        for m in _WIKI_BRACKET.finditer(text)
        if not m.group(1).strip().lower().startswith("asignatura:")
    ]
    if not labels:
        return False
    return Concept.objects.filter(label__in=labels).exclude(
        dictionary_id=concept.dictionary_id,
    ).exists()


def compute_concept_indicators(concept: Concept) -> ConceptIndicators:
    definitions = [d for d in concept.definitions.all() if d.is_active]
    has_content = any(d.text.strip() for d in definitions)
    has_examples = any(d.kind == "example" and d.text.strip() for d in definitions)
    has_official_from_def = any(
        d.kind == "reference" and d.text.strip() for d in definitions
    )

    props = list(concept.properties.all())
    has_properties = any(_is_ontology_property(p.key) and p.value.strip() for p in props)
    has_official_from_props = any(
        _property_implies_official_source(p.key, p.value) for p in props
    )
    has_cross_from_props = any(
        _property_implies_cross_ontology(p.key, p.value) for p in props
    )

    outgoing = list(concept.outgoing_relations.all())
    incoming = list(concept.incoming_relations.all())
    has_relations = bool(outgoing or incoming)
    has_cross_from_rel = any(
        r.target.dictionary_id != concept.dictionary_id for r in outgoing
    ) or any(
        r.source.dictionary_id != concept.dictionary_id for r in incoming
    )

    editorial_text = " ".join(d.text for d in definitions if d.text.strip())
    has_cross_from_wiki = _wiki_links_other_dictionaries(concept, editorial_text)

    return ConceptIndicators(
        has_content=has_content,
        has_relations=has_relations,
        has_properties=has_properties,
        has_examples=has_examples,
        has_cross_ontology_links=has_cross_from_rel or has_cross_from_props or has_cross_from_wiki,
        has_official_source=has_official_from_def or has_official_from_props,
    )


@dataclass(frozen=True)
class TopicIndicatorAnchors:
    empty: str
    relations: str
    properties: str
    examples: str
    cross: str
    sources: str


def topic_indicator_anchors(concept: Concept) -> TopicIndicatorAnchors:
    dict_id = concept.dictionary_id
    outgoing = list(concept.outgoing_relations.all())
    incoming = list(concept.incoming_relations.all())
    props = list(concept.properties.all())

    has_local_rel = any(r.target.dictionary_id == dict_id for r in outgoing) or any(
        r.source.dictionary_id == dict_id for r in incoming
    )
    has_cross_rel = any(r.target.dictionary_id != dict_id for r in outgoing) or any(
        r.source.dictionary_id != dict_id for r in incoming
    )
    has_cross_section = has_cross_rel or any(
        _property_implies_cross_ontology(p.key, p.value) for p in props
    )

    relations_anchor = ANCHOR_RELATIONS if has_local_rel else ANCHOR_CROSS

    return TopicIndicatorAnchors(
        empty=ANCHOR_EMPTY,
        relations=relations_anchor,
        properties=ANCHOR_PROPERTIES,
        examples=ANCHOR_EXAMPLES,
        cross=ANCHOR_CROSS if has_cross_section else relations_anchor,
        sources=ANCHOR_SOURCES,
    )


def dictionary_concept_rows(dictionary: Dictionary) -> list[dict]:
    concepts = list(
        dictionary.concepts.prefetch_related(
            "definitions",
            "properties",
            "outgoing_relations__target__dictionary",
            "incoming_relations__source__dictionary",
        )
    )
    rows = []
    for concept in concepts:
        rows.append({
            "concept": concept,
            "indicators": compute_concept_indicators(concept),
        })
    return rows
