from urllib.parse import urlparse

from django.conf import settings


def site_root_path(site_url: str) -> str:
    """Prefijo de ruta para Pages en subdirectorio (ej. /CORE_RadioMicelio/)."""
    path = urlparse(site_url).path.rstrip("/")
    return f"{path}/" if path else "/"


def script_prefix(site_url: str) -> str:
    return urlparse(site_url).path.rstrip("/")


def institute(request):
    return {
        "institute": getattr(settings, "CORE_INSTITUTE_NAME", "CORE Radio Micelio"),
        "static_export": getattr(request, "static_export", False),
        "site_root": site_root_path(getattr(settings, "SITE_URL", "http://127.0.0.1:8003")),
    }
