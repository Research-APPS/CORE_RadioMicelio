from __future__ import annotations

import re

from django.utils.html import escape

from ontologizar_app.models import Concept, Dictionary, Subject, Taxonomy

_WIKI_BRACKET = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
_BOUNDARY_BEFORE = r"(?:(?<=^)|(?<=[^\wáéíóúñÁÉÍÓÚÑüÜ]))"
_BOUNDARY_AFTER = r"(?:(?=$)|(?=[^\wáéíóúñÁÉÍÓÚÑüÜ]))"


def _build_link_index(
    site_root: str,
    *,
    subject_slug: str | None = None,
    dictionary_id: int | None = None,
) -> tuple[tuple[str, str, str], dict[str, str]]:
    if not site_root.endswith("/"):
        site_root = f"{site_root}/"

    by_label: dict[str, tuple[str, str]] = {}
    explicit: dict[str, str] = {}

    def add(label: str, url: str, aliases: tuple[str, ...] = ()):
        key = label.lower()
        if key not in by_label:
            by_label[key] = (url, label)
        for alias in aliases:
            ak = alias.lower()
            if ak not in by_label:
                by_label[ak] = (url, label)

    concepts = Concept.objects.select_related("dictionary__subject")
    if dictionary_id is not None:
        concepts = concepts.filter(dictionary_id=dictionary_id)
    elif subject_slug is not None:
        concepts = concepts.filter(dictionary__subject__slug=subject_slug)

    for concept in concepts:
        url = f"{site_root}biblioteca/temas/{concept.uuid}/"
        add(concept.label, url)
        explicit[f"concept:{concept.uuid}"] = url
        explicit[f"tema:{concept.uuid}"] = url
        explicit[f"concepto:{concept.uuid}"] = url

    if subject_slug is not None:
        subject = Subject.objects.filter(slug=subject_slug, is_active=True).first()
        if subject:
            url = f"{site_root}biblioteca/asignaturas/{subject.slug}/"
            add(subject.name, url)
            explicit[f"subject:{subject.slug}"] = url
            explicit[f"asignatura:{subject.slug}"] = url
            for dictionary in subject.dictionaries.filter(is_active=True):
                durl = f"{site_root}biblioteca/diccionarios/{subject.slug}/{dictionary.slug}/"
                add(dictionary.name, durl)
                explicit[f"dictionary:{subject.slug}/{dictionary.slug}"] = durl
                explicit[f"diccionario:{subject.slug}/{dictionary.slug}"] = durl
    elif dictionary_id is None:
        for subject in Subject.objects.filter(is_active=True):
            url = f"{site_root}biblioteca/asignaturas/{subject.slug}/"
            add(subject.name, url)
            explicit[f"subject:{subject.slug}"] = url
            explicit[f"asignatura:{subject.slug}"] = url

        for dictionary in Dictionary.objects.filter(is_active=True).select_related("subject"):
            url = f"{site_root}biblioteca/diccionarios/{dictionary.subject.slug}/{dictionary.slug}/"
            add(dictionary.name, url)
            explicit[f"dictionary:{dictionary.subject.slug}/{dictionary.slug}"] = url
            explicit[f"diccionario:{dictionary.subject.slug}/{dictionary.slug}"] = url

        for tax in Taxonomy.objects.filter(is_active=True):
            url = f"{site_root}biblioteca/taxonomias/{tax.slug}/"
            add(tax.name, url, aliases=(tax.slug.replace("-", " "),))
            explicit[f"taxonomy:{tax.slug}"] = url
            explicit[f"taxonomia:{tax.slug}"] = url

    ordered = tuple(
        (label, data[0], data[1])
        for label, data in sorted(by_label.items(), key=lambda item: len(item[0]), reverse=True)
    )
    return ordered, explicit


def clear_link_index_cache() -> None:
    pass


def _resolve_bracket(
    key: str, display: str, site_root: str,
    *, subject_slug: str | None = None, dictionary_id: int | None = None,
) -> str:
    ordered, explicit = _build_link_index(
        site_root, subject_slug=subject_slug, dictionary_id=dictionary_id,
    )
    key_lower = key.strip().lower()
    url = explicit.get(key_lower)
    canonical = key.strip()
    if not url:
        for label, link_url, label_display in ordered:
            if label == key_lower:
                url, canonical = link_url, label_display
                break
    if not url:
        return escape(f"[[{key}|{display}]]" if display else f"[[{key}]]")
    label = display.strip() or canonical
    return f'<a href="{url}" class="wiki-link">{escape(label)}</a>'


def _autolink_terms(
    escaped_text: str, site_root: str,
    *, subject_slug: str | None = None, dictionary_id: int | None = None,
) -> str:
    if not escaped_text:
        return ""
    ordered, _ = _build_link_index(
        site_root, subject_slug=subject_slug, dictionary_id=dictionary_id,
    )
    result = escaped_text
    for label_lower, url, display in ordered:
        label_esc = escape(display)
        pattern = re.compile(
            rf"{_BOUNDARY_BEFORE}{re.escape(label_esc)}{_BOUNDARY_AFTER}",
            re.IGNORECASE,
        )
        result = pattern.sub(
            f'<a href="{url}" class="wiki-link">{label_esc}</a>',
            result,
        )
    return result


def linkify_plaintext(
    text: str,
    *,
    site_root: str = "/",
    subject_slug: str | None = None,
    dictionary_id: int | None = None,
) -> str:
    """Texto plano → HTML con [[wiki]] y auto-enlaces dentro del mismo dominio."""
    if not text or not text.strip():
        return ""

    parts: list[str] = []
    last = 0
    for match in _WIKI_BRACKET.finditer(text):
        if match.start() > last:
            parts.append(_autolink_terms(
                escape(text[last:match.start()]), site_root,
                subject_slug=subject_slug, dictionary_id=dictionary_id,
            ))
        parts.append(_resolve_bracket(
            match.group(1), match.group(2) or "", site_root,
            subject_slug=subject_slug, dictionary_id=dictionary_id,
        ))
        last = match.end()
    if last < len(text):
        parts.append(_autolink_terms(
            escape(text[last:]), site_root,
            subject_slug=subject_slug, dictionary_id=dictionary_id,
        ))
    return "".join(parts)


def linkify_paragraphs(
    text: str,
    *,
    site_root: str = "/",
    subject_slug: str | None = None,
    dictionary_id: int | None = None,
) -> str:
    blocks = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not blocks:
        blocks = [line.strip() for line in text.split("\n") if line.strip()]
    return "".join(
        f"<p>{linkify_plaintext(block, site_root=site_root, subject_slug=subject_slug, dictionary_id=dictionary_id)}</p>"
        for block in blocks
    )
