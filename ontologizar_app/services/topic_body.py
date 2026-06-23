from __future__ import annotations

from django.utils.html import escape
from django.utils.safestring import mark_safe

from ontologizar_app.models import Concept
from ontologizar_app.services.concept_indicators import (
    ANCHOR_CONTENT,
    ANCHOR_CROSS,
    ANCHOR_EMPTY,
    ANCHOR_EXAMPLES,
    ANCHOR_PROPERTIES,
    ANCHOR_RELATIONS,
    ANCHOR_SOURCES,
    _is_ontology_property,
    _property_implies_cross_ontology,
    _property_implies_official_source,
)
from ontologizar_app.services.wiki_links import linkify_plaintext

_SECTION_SVG = {
    "empty": '<svg viewBox="0 0 16 16" width="14" height="14"><path fill="currentColor" d="M3 2h10a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1zm1 2v8h8V4H4z" opacity=".45"/></svg>',
    "relations": '<svg viewBox="0 0 16 16" width="14" height="14"><circle cx="4" cy="8" r="2" fill="currentColor"/><circle cx="12" cy="4" r="2" fill="currentColor"/><circle cx="12" cy="12" r="2" fill="currentColor"/><path stroke="currentColor" stroke-width="1.2" fill="none" d="M6 7.2L10 5M6 8.8l4 2.2"/></svg>',
    "properties": '<svg viewBox="0 0 16 16" width="14" height="14"><path fill="currentColor" d="M2 4h5v2H4v6H2V4zm7 0h5v8h-2v-6H9V4z"/></svg>',
    "examples": '<svg viewBox="0 0 16 16" width="14" height="14"><path fill="currentColor" d="M8 1.5l1.1 3.4h3.5l-2.8 2.1 1.1 3.4L8 8.3l-2.9 2.1 1.1-3.4-2.8-2.1h3.5L8 1.5z"/></svg>',
    "external": '<svg viewBox="0 0 16 16" width="14" height="14"><path fill="currentColor" d="M9 2h5v5h-2V5.4l-5.3 5.3-1.4-1.4L10.6 4H9V2zM3 4h4v2H5v5H3V4z"/></svg>',
    "source": '<svg viewBox="0 0 16 16" width="14" height="14"><path fill="currentColor" d="M8 1a3 3 0 0 1 3 3v1h1a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h1V4a3 3 0 0 1 3-3zm0 2a1 1 0 0 0-1 1v1h2V4a1 1 0 0 0-1-1zm-3 4v6h6V7H5z"/></svg>',
}


def _badge(kind: str, title: str) -> str:
    svg = _SECTION_SVG.get(kind, "")
    return (
        f'<span class="topic-section-badge concept-indicator concept-indicator--{kind}" '
        f'title="{escape(title)}" aria-hidden="true">{svg}</span>'
    )


def _section_open(anchor: str, *, badge_kind: str | None = None, badge_title: str = "") -> str:
    badge = _badge(badge_kind, badge_title) if badge_kind else ""
    return f'<section id="{anchor}" class="topic-section topic-section--{anchor}">{badge}'


def _render_property_item(prop, *, site_root: str, dictionary_id: int, extra_class: str = "") -> str:
    cls = f' class="{extra_class}"' if extra_class else ""
    return (
        f"<li{cls}><strong>{escape(prop.key)}</strong>: "
        f"{linkify_plaintext(prop.value, site_root=site_root, dictionary_id=dictionary_id)}</li>"
    )


def _render_relation_item(rel, *, site_root: str, is_incoming: bool, cross: bool) -> str:
    concept = rel.source if is_incoming else rel.target
    cross_cls = " topic-item--cross" if cross else ""
    return (
        f'<li class="topic-relation-item{cross_cls}">'
        f'<a href="{site_root}biblioteca/temas/{concept.uuid}/" class="wiki-link">'
        f"{escape(concept.label)}</a>"
        f' <span class="rel-type">({escape(rel.relation_type)})</span></li>'
    )


def render_topic_body(concept: Concept, *, site_root: str = "/") -> str:
    if not site_root.endswith("/"):
        site_root = f"{site_root}/"

    parts: list[str] = []
    subject = concept.dictionary.subject
    dictionary = concept.dictionary
    dict_id = dictionary.id

    parts.append(
        f'<nav class="wiki-context">'
        f'<a href="{site_root}biblioteca/asignaturas/{subject.slug}/" class="wiki-link">{escape(subject.name)}</a>'
        f' · <a href="{site_root}biblioteca/diccionarios/{subject.slug}/{dictionary.slug}/" class="wiki-link">'
        f"{escape(dictionary.name)}</a></nav>"
    )

    definitions = [d for d in concept.definitions.filter(is_active=True)]
    definition = next((d for d in definitions if d.kind == "definition" and d.text.strip()), None)
    examples = [d for d in definitions if d.kind == "example" and d.text.strip()]
    references = [d for d in definitions if d.kind == "reference" and d.text.strip()]

    props = list(concept.properties.all())
    ontology_props = [p for p in props if _is_ontology_property(p.key) and p.value.strip()]
    source_props = [p for p in props if _property_implies_official_source(p.key, p.value)]
    cross_props = [p for p in props if _property_implies_cross_ontology(p.key, p.value)]

    outgoing = list(concept.outgoing_relations.select_related("target__dictionary"))
    incoming = list(concept.incoming_relations.select_related("source__dictionary"))
    cross_out = [r for r in outgoing if r.target.dictionary_id != dict_id]
    cross_in = [r for r in incoming if r.source.dictionary_id != dict_id]

    has_editorial = bool(definition or examples or references)
    has_relations = bool(outgoing or incoming)
    has_any = has_editorial or ontology_props or source_props or cross_props or has_relations

    if definition:
        parts.append(
            f'{_section_open(ANCHOR_CONTENT)}'
            f'<h3 class="topic-section-title">Definición</h3>'
            f'<p class="topic-definition">{linkify_plaintext(definition.text, site_root=site_root, dictionary_id=dict_id)}</p>'
            f"</section>"
        )

    if examples:
        items = "".join(
            f"<li>{linkify_plaintext(ex.text, site_root=site_root, dictionary_id=dict_id)}</li>"
            for ex in examples
        )
        parts.append(
            f'{_section_open(ANCHOR_EXAMPLES, badge_kind="examples", badge_title="Ejemplos")}'
            f'<h3 class="topic-section-title">Ejemplos</h3><ul>{items}</ul></section>'
        )

    if source_props or references:
        items = "".join(
            f"<li>{linkify_plaintext(ref.text, site_root=site_root, dictionary_id=dict_id)}</li>"
            for ref in references
        )
        items += "".join(
            _render_property_item(p, site_root=site_root, dictionary_id=dict_id, extra_class="topic-source-item")
            for p in source_props
        )
        parts.append(
            f'{_section_open(ANCHOR_SOURCES, badge_kind="source", badge_title="Fuente científica")}'
            f'<h3 class="topic-section-title">Fuentes y procedencia</h3><ul>{items}</ul></section>'
        )

    if cross_props or cross_out or cross_in:
        items = "".join(
            _render_property_item(p, site_root=site_root, dictionary_id=dict_id, extra_class="topic-cross-item")
            for p in cross_props
        )
        items += "".join(
            _render_relation_item(r, site_root=site_root, is_incoming=False, cross=True) for r in cross_out
        )
        items += "".join(
            _render_relation_item(r, site_root=site_root, is_incoming=True, cross=True) for r in cross_in
        )
        parts.append(
            f'{_section_open(ANCHOR_CROSS, badge_kind="external", badge_title="Otras ontologías")}'
            f'<h3 class="topic-section-title">Enlaces con otras ontologías</h3><ul>{items}</ul></section>'
        )

    if ontology_props:
        items = "".join(
            _render_property_item(p, site_root=site_root, dictionary_id=dict_id, extra_class="topic-property-item")
            for p in ontology_props
        )
        parts.append(
            f'{_section_open(ANCHOR_PROPERTIES, badge_kind="properties", badge_title="Propiedades ontológicas")}'
            f'<h3 class="topic-section-title">Propiedades ontológicas</h3><ul>{items}</ul></section>'
        )

    local_out = [r for r in outgoing if r.target.dictionary_id == dict_id]
    local_in = [r for r in incoming if r.source.dictionary_id == dict_id]
    if local_out or local_in:
        links = "".join(
            _render_relation_item(r, site_root=site_root, is_incoming=False, cross=False) for r in local_out
        )
        links += "".join(
            _render_relation_item(r, site_root=site_root, is_incoming=True, cross=False) for r in local_in
        )
        parts.append(
            f'{_section_open(ANCHOR_RELATIONS, badge_kind="relations", badge_title="Relaciones ontológicas")}'
            f'<h3 class="topic-section-title">Relaciones</h3><ul>{links}</ul></section>'
        )

    if not has_any:
        parts.append(
            f'<section id="{ANCHOR_EMPTY}" class="topic-section topic-section--empty topic-empty">'
            f'{_badge("empty", "Sin contenido editorial")}'
            f'<p>Este concepto aún no tiene contenido editorial.</p></section>'
        )
    elif not has_editorial:
        parts.append(
            f'<section id="{ANCHOR_EMPTY}" class="topic-section topic-section--empty topic-empty topic-empty--inline">'
            f'{_badge("empty", "Sin texto definitorio")}'
            f'<p class="topic-empty-note">Sin definición ni ejemplos; solo metadatos estructurados.</p></section>'
        )

    return mark_safe("".join(parts))
