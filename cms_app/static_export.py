from __future__ import annotations

import json
import shutil
from pathlib import Path
from urllib.parse import urlparse

from django.conf import settings
from django.test import RequestFactory

from airam_app.graph import build_graph
from cms_app import views_public
from knowledge_app.models import Concept, Dictionary, Subject, Taxonomy


def _make_request(path: str):
    parsed = urlparse(settings.SITE_URL)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    request = RequestFactory().get(path)
    request.META["HTTP_HOST"] = parsed.netloc
    request.META["SERVER_NAME"] = parsed.hostname or "localhost"
    request.META["SERVER_PORT"] = str(port)
    request.META["wsgi.url_scheme"] = parsed.scheme or "http"
    request.static_export = True
    return request


def _write_html(out_dir: Path, rel_path: str, html: str) -> None:
    target = out_dir / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")


def _render(view, request, **kwargs) -> str:
    response = view(request, **kwargs)
    return response.content.decode("utf-8")


def _copy_assets(out_dir: Path) -> None:
    assets_dir = out_dir / "assets"
    if assets_dir.exists():
        shutil.rmtree(assets_dir)
    assets_dir.mkdir(parents=True)
    for static_dir in settings.STATICFILES_DIRS:
        src = Path(static_dir)
        if src.is_dir():
            shutil.copytree(src, assets_dir, dirs_exist_ok=True)


def export_static_site(out_dir: Path) -> dict:
    out_dir = Path(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    prev_static_url = settings.STATIC_URL
    settings.STATIC_URL = settings.STATIC_EXPORT_ASSETS_PREFIX

    try:
        _copy_assets(out_dir)
        counts = {"pages": 0, "concepts": 0}

        root_index = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="0; url=/biblioteca/">
  <link rel="canonical" href="/biblioteca/">
  <title>Biblioteca</title>
</head>
<body><p><a href="/biblioteca/">Ir a la biblioteca</a></p></body>
</html>"""
        _write_html(out_dir, "index.html", root_index)
        counts["pages"] += 1

        req = _make_request("/biblioteca/")
        _write_html(out_dir, "biblioteca/index.html", _render(views_public.biblioteca_index, req))
        counts["pages"] += 1

        req = _make_request("/biblioteca/taxonomias/")
        _write_html(out_dir, "biblioteca/taxonomias/index.html", _render(views_public.taxonomy_list, req))
        counts["pages"] += 1

        for subject in Subject.objects.filter(is_active=True):
            req = _make_request(f"/biblioteca/asignaturas/{subject.slug}/")
            html = _render(views_public.subject_detail, req, slug=subject.slug)
            _write_html(out_dir, f"biblioteca/asignaturas/{subject.slug}/index.html", html)
            counts["pages"] += 1
            for dictionary in subject.dictionaries.filter(is_active=True):
                path = f"/biblioteca/diccionarios/{subject.slug}/{dictionary.slug}/"
                req = _make_request(path)
                html = _render(views_public.dictionary_detail, req, subject_slug=subject.slug, dict_slug=dictionary.slug)
                _write_html(out_dir, f"biblioteca/diccionarios/{subject.slug}/{dictionary.slug}/index.html", html)
                counts["pages"] += 1

        for taxonomy in Taxonomy.objects.filter(is_active=True):
            req = _make_request(f"/biblioteca/taxonomias/{taxonomy.slug}/")
            html = _render(views_public.taxonomy_detail, req, slug=taxonomy.slug)
            _write_html(out_dir, f"biblioteca/taxonomias/{taxonomy.slug}/index.html", html)
            counts["pages"] += 1

        for concept in Concept.objects.select_related("dictionary__subject"):
            req = _make_request(f"/biblioteca/temas/{concept.uuid}/")
            html = _render(views_public.topic_detail, req, uuid=concept.uuid)
            _write_html(out_dir, f"biblioteca/temas/{concept.uuid}/index.html", html)
            counts["pages"] += 1
            counts["concepts"] += 1

        graph_path = out_dir / "airam" / "graph.json"
        graph_path.parent.mkdir(parents=True, exist_ok=True)
        graph_path.write_text(json.dumps(build_graph(), ensure_ascii=False, indent=2), encoding="utf-8")

        cname = getattr(settings, "STATIC_SITE_CNAME", "")
        if cname:
            (out_dir / "CNAME").write_text(cname.strip() + "\n", encoding="utf-8")

        return counts
    finally:
        settings.STATIC_URL = prev_static_url
