from __future__ import annotations
from django.utils.html import escape
from django.utils.safestring import mark_safe

from knowledge_app.models import Concept


def render_topic_body(concept: Concept) -> str:
    parts: list[str] = []
    definition = concept.definitions.filter(is_active=True, kind="definition").first()
    if definition:
        parts.append(f"<p class=\"topic-definition\">{escape(definition.text)}</p>")
    props = concept.properties.all()
    if props:
        items = "".join(
            f"<li><strong>{escape(p.key)}</strong>: {escape(p.value)}</li>" for p in props
        )
        parts.append(f"<section class=\"topic-properties\"><h3>Propiedades</h3><ul>{items}</ul></section>")
    rels = concept.outgoing_relations.select_related("target").all()
    if rels:
        links = "".join(
            f'<li><a href="/biblioteca/temas/{r.target.uuid}/">{escape(r.target.label)}</a>'
            f' <span class="rel-type">({escape(r.relation_type)})</span></li>'
            for r in rels
        )
        parts.append(f"<section class=\"topic-relations\"><h3>Relaciones</h3><ul>{links}</ul></section>")
    if not parts:
        parts.append("<p class=\"topic-empty\">Este concepto aún no tiene contenido editorial.</p>")
    return mark_safe("".join(parts))
