"""
Carga core_ontologia_musica_v0.1.jsonld en Subject/Dictionary/Taxonomy/Concept.

Idempotente: re-ejecutar actualiza definiciones y nodos sin duplicar.
"""

from __future__ import annotations

import json
from pathlib import Path

from airam_app.services.semantic_relations import normalize_relation_type
from ontologizar_app.models import (
    AttributedRelation,
    Concept,
    ConceptDefinition,
    ConceptProperty,
    ConceptRelation,
    Dictionary,
    Subject,
    Taxonomy,
    TaxonomyNode,
)
from ontologizar_app.services.subject_taxonomy import assign_subject_taxonomy
from research_app.models import LearningMarker, ProyectoInvestigacion

BASE_IRI = "https://research-apps.github.io/CORE_RadioMicelio/id/"

TAXONOMY_SLUGS = {
    f"{BASE_IRI}taxonomia/musica/instrumentos": ("musica-instrumentos", "Instrumentos musicales", "class", 0),
    f"{BASE_IRI}taxonomia/musica/tecnicas": ("musica-tecnicas", "Técnicas de interpretación", "class", 1),
    f"{BASE_IRI}taxonomia/musica/recursos": ("musica-recursos", "Recursos musicales y estilísticos", "class", 2),
    f"{BASE_IRI}taxonomia/musica/generos": ("musica-generos", "Géneros y tradiciones musicales", "class", 3),
    f"{BASE_IRI}taxonomia/musica/conceptos": ("musica-conceptos", "Conceptos musicales generales", "class", 4),
    f"{BASE_IRI}taxonomia/musica/propiedades": ("musica-propiedades", "Propiedades ontológicas de Música", "property", 5),
}

CLASS_ROOT_IRIS = {
    f"{BASE_IRI}musica/clase/instrumentos": "musica-instrumentos",
    f"{BASE_IRI}musica/clase/tecnicas": "musica-tecnicas",
    f"{BASE_IRI}musica/clase/recursos": "musica-recursos",
    f"{BASE_IRI}musica/clase/generos": "musica-generos",
    f"{BASE_IRI}musica/clase/conceptos": "musica-conceptos",
}

JSONLD_RELATION_MAP = {
    "parte_de": "part_of",
    "se_ejecuta_mediante": "works_via",
    "utilizado_en": "used_in",
    "utilizado_por": "used_in",
    "produce": "produces",
    "requiere": "related",
    "permite": "enables",
    "contrasta_con": "distinct_from",
    "evoluciona_hacia": "evolves_to",
    "aparece_en": "appears_in",
    "influye_en": "related",
    "broader": "broader",
    "narrower": "narrower",
    "related": "related",
}


def _ref_id(value) -> str | None:
    if not value:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("@id")
    if isinstance(value, list) and value:
        return _ref_id(value[0])
    return None


def _label(node: dict) -> str:
    pref = node.get("prefLabel")
    if isinstance(pref, dict):
        return pref.get("@value", "").strip()
    if isinstance(pref, str):
        return pref.strip()
    return (node.get("name") or "").strip()


def _definition(node: dict) -> str:
    for key in ("definition", "description"):
        val = node.get(key)
        if isinstance(val, dict):
            text = val.get("@value", "").strip()
            if text:
                return text
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def _types(node: dict) -> set[str]:
    raw = node.get("@type", [])
    if isinstance(raw, str):
        return {raw}
    return set(raw or [])


def _map_relation(raw: str) -> str:
    mapped = JSONLD_RELATION_MAP.get(raw, raw)
    return normalize_relation_type(mapped)


class MusicaOntologyLoader:
    def __init__(self, graph: list[dict]):
        self.graph = graph
        self.by_id = {n["@id"]: n for n in graph if n.get("@id")}
        self.concepts_by_iri: dict[str, Concept] = {}
        self.taxonomies: dict[str, Taxonomy] = {}
        self.class_roots: dict[str, TaxonomyNode] = {}
        self.stats = {
            "concepts": 0,
            "definitions": 0,
            "taxonomy_nodes": 0,
            "relations": 0,
            "markers": 0,
        }

    def load(self) -> dict:
        subject = self._ensure_subject()
        dictionary = self._ensure_dictionary(subject)
        self._ensure_taxonomies(subject)
        self._load_class_roots(dictionary)
        self._load_terms(dictionary)
        self._load_properties(dictionary)
        self._load_relation_assertions()
        self._load_term_skos_relations()
        notebook = self._ensure_notebook(dictionary)
        self.stats["notebook"] = notebook.acron or notebook.titulo
        return self.stats

    def _ensure_subject(self) -> Subject:
        node = self.by_id[f"{BASE_IRI}asignatura/musica"]
        subject, created = Subject.objects.update_or_create(
            slug="musica",
            defaults={
                "name": _label(node) or "Música",
                "description": _definition(node),
                "is_active": True,
            },
        )
        self.stats["subject_created"] = created
        return subject

    def _ensure_dictionary(self, subject: Subject) -> Dictionary:
        node = self.by_id[f"{BASE_IRI}diccionario/musica"]
        dictionary, _ = Dictionary.objects.update_or_create(
            subject=subject,
            slug="musica",
            defaults={
                "name": _label(node) or "Diccionario de Música de CORE",
                "description": _definition(node),
                "is_active": True,
            },
        )
        return dictionary

    def _ensure_taxonomies(self, subject: Subject) -> None:
        for iri, (slug, name, role, position) in TAXONOMY_SLUGS.items():
            node = self.by_id.get(iri, {})
            taxonomy, _ = Taxonomy.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": _label(node) or name,
                    "description": _definition(node),
                    "is_active": True,
                },
            )
            self.taxonomies[iri] = taxonomy
            assign_subject_taxonomy(
                subject,
                taxonomy,
                role=role,
                taxonomy_group="Música",
                is_primary=(position == 0),
                position=position,
            )

    def _concept(self, dictionary: Dictionary, label: str, iri: str) -> Concept:
        concept, created = Concept.objects.get_or_create(
            dictionary=dictionary,
            label=label,
        )
        self.concepts_by_iri[iri] = concept
        if created:
            self.stats["concepts"] += 1
        ConceptProperty.objects.update_or_create(
            concept=concept,
            key="jsonld_id",
            defaults={"value": iri, "value_type": "url"},
        )
        return concept

    def _set_definition(self, concept: Concept, text: str) -> None:
        if not text:
            return
        defn, created = ConceptDefinition.objects.update_or_create(
            concept=concept,
            kind="definition",
            defaults={"text": text, "is_active": True},
        )
        if created or defn.text != text:
            defn.text = text
            defn.is_active = True
            defn.save(update_fields=["text", "is_active"])
            self.stats["definitions"] += 1

    def _taxonomy_node(
        self,
        taxonomy: Taxonomy,
        label: str,
        concept: Concept | None,
        parent: TaxonomyNode | None = None,
    ) -> TaxonomyNode:
        node, created = TaxonomyNode.objects.get_or_create(
            taxonomy=taxonomy,
            label=label,
            parent=parent,
            defaults={"concept": concept},
        )
        if concept and node.concept_id != concept.id:
            node.concept = concept
            node.save(update_fields=["concept"])
        if created:
            self.stats["taxonomy_nodes"] += 1
        return node

    def _load_class_roots(self, dictionary: Dictionary) -> None:
        for class_iri, tax_slug in CLASS_ROOT_IRIS.items():
            node = self.by_id.get(class_iri)
            if not node:
                continue
            label = _label(node)
            concept = self._concept(dictionary, label, class_iri)
            self._set_definition(concept, _definition(node))
            ConceptProperty.objects.update_or_create(
                concept=concept,
                key="entity_kind",
                defaults={"value": "class", "value_type": "text"},
            )
            taxonomy = Taxonomy.objects.get(slug=tax_slug)
            root = self._taxonomy_node(taxonomy, label, concept, parent=None)
            self.class_roots[class_iri] = root

    def _load_terms(self, dictionary: Dictionary) -> None:
        for iri, node in self.by_id.items():
            if "/musica/termino/" not in iri:
                continue
            label = _label(node)
            if not label:
                continue
            concept = self._concept(dictionary, label, iri)
            self._set_definition(concept, _definition(node))
            if node.get("termCode"):
                ConceptProperty.objects.update_or_create(
                    concept=concept,
                    key="term_code",
                    defaults={"value": str(node["termCode"]), "value_type": "text"},
                )
            if node.get("entityKind"):
                ConceptProperty.objects.update_or_create(
                    concept=concept,
                    key="entity_kind",
                    defaults={"value": str(node["entityKind"]), "value_type": "text"},
                )
            scheme_iri = _ref_id(node.get("inScheme"))
            broader_iri = _ref_id(node.get("broader"))
            parent_root = self.class_roots.get(broader_iri)
            if scheme_iri and scheme_iri in self.taxonomies:
                taxonomy = self.taxonomies[scheme_iri]
                parent = parent_root if parent_root and parent_root.taxonomy_id == taxonomy.id else None
                self._taxonomy_node(taxonomy, label, concept, parent=parent)

    def _load_properties(self, dictionary: Dictionary) -> None:
        prop_tax = self.taxonomies[f"{BASE_IRI}taxonomia/musica/propiedades"]
        for iri, node in self.by_id.items():
            if "/musica/propiedad/" not in iri:
                continue
            label = _label(node) or node.get("name", "")
            if not label:
                continue
            concept = self._concept(dictionary, label, iri)
            self._set_definition(concept, _definition(node))
            ConceptProperty.objects.update_or_create(
                concept=concept,
                key="entity_kind",
                defaults={"value": "property", "value_type": "text"},
            )
            ConceptProperty.objects.update_or_create(
                concept=concept,
                key="relation_slug",
                defaults={"value": label, "value_type": "text"},
            )
            self._taxonomy_node(prop_tax, label, concept, parent=None)

    def _relation(self, source: Concept, target: Concept, relation_type: str, *, editorial: bool = False) -> None:
        rel, created = ConceptRelation.objects.get_or_create(
            source=source,
            target=target,
            relation_type=relation_type,
        )
        if created:
            self.stats["relations"] += 1
        if editorial:
            AttributedRelation.objects.update_or_create(
                relation=rel,
                defaults={
                    "authority_layer": "factual",
                    "framework": "",
                    "asserted_by": "CORE Radio Micelio (editorial v0.1)",
                },
            )

    def _load_relation_assertions(self) -> None:
        for node in self.graph:
            if "core:RelationAssertion" not in _types(node):
                continue
            source_iri = _ref_id(node.get("source"))
            target_iri = _ref_id(node.get("target"))
            if not source_iri or not target_iri:
                continue
            source = self.concepts_by_iri.get(source_iri)
            target = self.concepts_by_iri.get(target_iri)
            if not source or not target:
                continue
            rel_type = _map_relation(node.get("relationType", "related"))
            editorial = node.get("core:authorityLayer") == "editorial"
            self._relation(source, target, rel_type, editorial=editorial)

    def _load_term_skos_relations(self) -> None:
        for iri, node in self.by_id.items():
            if "/musica/termino/" not in iri:
                continue
            source = self.concepts_by_iri.get(iri)
            if not source:
                continue
            for rel_field, rel_type in (("related", "related"), ("broader", "broader")):
                refs = node.get(rel_field)
                if not refs:
                    continue
                if isinstance(refs, dict):
                    refs = [refs]
                for ref in refs:
                    target_iri = _ref_id(ref)
                    target = self.concepts_by_iri.get(target_iri or "")
                    if target:
                        self._relation(source, target, rel_type)

    def _ensure_notebook(self, dictionary: Dictionary) -> ProyectoInvestigacion:
        cuaderno = self.by_id.get(f"{BASE_IRI}cuaderno/radio-micelio", {})
        proyecto = self.by_id.get(f"{BASE_IRI}proyecto/radio-micelio", {})
        notebook, _ = ProyectoInvestigacion.objects.update_or_create(
            acron="RM",
            defaults={
                "titulo": proyecto.get("name") or "Radio Micelio",
                "descripcion": _definition(cuaderno) or _definition(proyecto),
                "activo": True,
                "publico": True,
            },
        )
        applies = cuaderno.get("appliesConcept") or []
        if isinstance(applies, dict):
            applies = [applies]
        for ref in applies:
            term_iri = _ref_id(ref)
            concept = self.concepts_by_iri.get(term_iri or "")
            if not concept:
                continue
            taxonomy_slug = concept.primary_taxonomy_slug() or "musica-conceptos"
            _, created = LearningMarker.objects.get_or_create(
                project=notebook,
                concept_uuid=concept.uuid,
                defaults={
                    "subject_slug": "musica",
                    "dictionary_slug": dictionary.slug,
                    "taxonomy_slug": taxonomy_slug,
                    "concept_label": concept.label,
                    "status": "selected",
                    "note": "Marcador desde ontología Música v0.1 (appliesConcept)",
                },
            )
            if created:
                self.stats["markers"] += 1
        return notebook


def load_musica_ontology_from_file(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    graph = data.get("@graph", [])
    loader = MusicaOntologyLoader(graph)
    return loader.load()
