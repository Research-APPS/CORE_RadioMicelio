from django.conf import settings


def institute(request):
    return {
        "institute": getattr(settings, "CORE_INSTITUTE_NAME", "CORE Radio Micelio"),
        "static_export": getattr(request, "static_export", False),
    }
