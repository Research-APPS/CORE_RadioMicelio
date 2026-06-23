from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request


def fetch_wikipedia_summary(title: str, lang: str = "es") -> dict | None:
    """Resumen de Wikipedia (REST API). Devuelve extract, description y content_urls."""
    slug = urllib.parse.quote(title.replace(" ", "_"), safe="/")
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{slug}"
    request = urllib.request.Request(url, headers={"User-Agent": "CORE-RadioMicelio/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError):
        return None
    extract = (data.get("extract") or "").strip()
    if not extract:
        return None
    page_url = (data.get("content_urls") or {}).get("desktop", {}).get("page", "")
    return {
        "extract": extract,
        "description": (data.get("description") or "").strip(),
        "page_url": page_url,
        "title": data.get("title") or title,
    }
