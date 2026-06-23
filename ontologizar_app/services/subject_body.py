from __future__ import annotations

from django.utils.html import escape
from django.utils.safestring import mark_safe

from ontologizar_app.models import Concept, Subject, Taxonomy
from ontologizar_app.services.wiki_links import linkify_paragraphs, linkify_plaintext


def render_subject_body(subject: Subject, *, site_root: str = "/") -> str:
    parts: list[str] = []

    if subject.description.strip():
        parts.append(f'<div class="wiki-lead">{linkify_paragraphs(subject.description, site_root=site_root)}</div>')
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
                block.append(linkify_paragraphs(body, site_root=site_root))
            sections.append("".join(block))
        parts.append(f'<div class="wiki-sections">{"".join(sections)}</div>')

    dictionaries = list(subject.dictionaries.filter(is_active=True))
    if dictionaries:
        links = "".join(
            f'<li><a href="{site_root}biblioteca/diccionarios/{subject.slug}/{d.slug}/" class="wiki-link">'
            f"{escape(d.name)}</a> ({d.concepts.count()} temas)</li>"
            for d in dictionaries
        )
        parts.append(f'<section class="wiki-aside"><h2>Diccionarios</h2><ul>{links}</ul></section>')

    concept_ids = set(
        subject.dictionaries.filter(is_active=True).values_list("concepts__uuid", flat=True)
    )
    concept_ids.discard(None)
    if concept_ids:
        related = []
        for tax in Taxonomy.objects.filter(is_active=True, nodes__concept__uuid__in=concept_ids).distinct():
            related.append(
                f'<li><a href="{site_root}biblioteca/taxonomias/{tax.slug}/" class="wiki-link">'
                f"{escape(tax.name)}</a></li>"
            )
        if related:
            parts.append(
                f'<section class="wiki-aside"><h2>Taxonomías relacionadas</h2><ul>{"".join(related)}</ul></section>'
            )

    other_subjects = Subject.objects.filter(is_active=True).exclude(pk=subject.pk).order_by("name")
    if other_subjects.exists():
        links = "".join(
            f'<li><a href="{site_root}biblioteca/asignaturas/{s.slug}/" class="wiki-link">'
            f"{escape(s.name)}</a></li>"
            for s in other_subjects
        )
        parts.append(f'<section class="wiki-aside"><h2>Otras asignaturas</h2><ul>{links}</ul></section>')

    if subject.source_url:
        parts.append(
            f'<p class="wiki-source">Fuente: <a href="{escape(subject.source_url)}" rel="noopener" class="wiki-link">'
            f"Wikipedia</a></p>"
        )

    return mark_safe(f'<article class="wiki-body">{"".join(parts)}</article>')
