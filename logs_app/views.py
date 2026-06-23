from django.http import JsonResponse
from django.shortcuts import render

from logs_app.analytics import build_segment_summary
from logs_app.platforms import get_platform, list_platforms


def platform_selector(request):
    return render(request, "logs/platform_selector.html", {"platforms": list_platforms()})


def platform_dashboard(request, platform_slug):
    spec = get_platform(platform_slug)
    if not spec:
        return JsonResponse({"error": "unknown platform"}, status=404)
    summary = build_segment_summary(platform_slug)
    return render(
        request,
        "logs/platform_dashboard.html",
        {"platform": spec, "summary": summary},
    )


def segments_api(request, platform_slug):
    if not get_platform(platform_slug):
        return JsonResponse({"error": "unknown platform"}, status=404)
    return JsonResponse(build_segment_summary(platform_slug))
