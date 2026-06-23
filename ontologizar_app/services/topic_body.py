from __future__ import annotations

from django.utils.html import escape
from django.utils.safestring import mark_safe

from ontologizar_app.models import Concept
from ontologizar_app.services.wiki_links import linkify_plaintext


def render_topic_body(concept: Concept, *, site_root: str = "/") -> str:
    if not site_root.endswith("/"):
        site_root = f"{site_root}/"

    parts: list[str] = []
    subject = concept.dictionary.subject
    dictionary = concept.dictionary

    parts.append(
        f'<nav class="wiki-context">'
        f'<a href="{site_root}biblioteca/asignaturas/{subject.slug}/" class="wiki-link">{escape(subject.name)}</a>'
        f' · <a href="{site_root}biblioteca/diccionarios/{subject.slug}/{dictionary.slug}/" class="wiki-link">'
        f"{escape(dictionary.name)}</a></nav>"
    )

    definition = concept.definitions.filter(is_active=True, kind="definition").first()
    if definition:
        parts.append(
            f'<p class="topic-definition">{linkify_plaintext(definition.text, site_root=site_root)}</p>'
        )

    props = concept.properties.all()
    if props:
        items = "".join(
            f"<li><strong>{escape(p.key)}</strong>: "
            f"{linkify_plaintext(p.value, site_root=site_root)}</li>"
            for p in props
        )
        parts.append(f'<section class="topic-properties"><h3>Propiedades</h3><ul>{items}</ul></section>')

    rels = concept.outgoing_relations.select_related("target").all()
    if rels:
        links = "".join(
            f'<li><a href="{site_root}biblioteca/temas/{r.target.uuid}/" class="wiki-link">'
            f"{escape(r.target.label)}</a>"
            f' <span class="rel-type">({escape(r.relation_type)})</span></li>'
            for r in rels
        )
        parts.append(f'<section class="topic-relations"><h3>Relaciones</h3><ul>{links}</ul></section>')

    incoming = concept.incoming_relations.select_related("source").all()
    if incoming:
        links = "".join(
            f'<li><a href="{site_root}biblioteca/temas/{r.source.uuid}/" class="wiki-link">'
            f"{escape(r.source.label)}</a>"
            f' <span class="rel-type">({escape(r.relation_type)})</span></li>'
            for r in incoming
        )
        parts.append(f'<section class="topic-relations"><h3>Mencionado desde</h3><ul>{links}</ul></section>')

    if not definition and not props and not rels and not incoming:
        parts.append("<p class=\"topic-empty\">Este concepto aún no tiene contenido editorial.</p>")

    return mark_safe("".join(parts))
