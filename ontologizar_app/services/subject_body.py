from __future__ import annotations

from django.utils.html import escape
from django.utils.safestring import mark_safe

from ontologizar_app.models import Subject
from ontologizar_app.services.wiki_links import linkify_paragraphs, linkify_plaintext


def render_subject_body(subject: Subject, *, site_root: str = "/") -> str:
    parts: list[str] = []

    if subject.description.strip():
        parts.append(
            f'<div class="wiki-lead">{linkify_paragraphs(subject.description, site_root=site_root, subject_slug=subject.slug)}</div>'
        )
    else:
        parts.append(
            '<p class="wiki-empty">Esta asignatura aún no tiene artículo editorial. '
            "Puedes ampliarlo desde el CMS o ejecutar <code>seed_curriculum</code>.</p>"
        )

    materials = list(subject.materials.all())
    if materials:
        sections = []
        for material in materials:
            block = [f"<h2>{escape(material.title)}</h2>"]
            body = (material.body or material.summary or "").strip()
            if body:
                block.append(linkify_paragraphs(body, site_root=site_root, subject_slug=subject.slug))
            sections.append("".join(block))
        parts.append(f'<div class="wiki-sections">{"".join(sections)}</div>')

    if subject.source_url:
        parts.append(
            f'<p class="wiki-source">Fuente: <a href="{escape(subject.source_url)}" rel="noopener" class="wiki-link">'
            f"Wikipedia</a></p>"
        )

    return mark_safe(f'<article class="wiki-body">{"".join(parts)}</article>')
