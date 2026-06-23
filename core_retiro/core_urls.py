from django.conf import settings

def _base(module, default):
    return (getattr(settings, "CORE_URL_MAP", {}).get(module) or default).rstrip("/")

def module_url(module, path=""):
    bases = {
        "research": _base("research", "http://127.0.0.1:8000/research"),
        "logs": _base("logs", "http://127.0.0.1:8000/logs"),
        "knowledge": _base("knowledge", "http://127.0.0.1:8000/knowledge"),
    }
    base = bases.get(module, "").rstrip("/")
    path = (path or "").lstrip("/")
    return f"{base}/{path}" if path else base
