from __future__ import annotations
from uuid import UUID

from core_retiro.core_urls import module_url
from logs_app.analytics import build_segment_summary
from logs_app.models import ProjectPlatformLink
from logs_app.platforms import get_platform
from research_app.capability_registry import ProjectCapabilityDescriptor


def get_platforms_for_project(project_uuid: UUID):
    return ProjectPlatformLink.objects.filter(research_project_uuid=project_uuid).order_by("-is_primary", "platform_slug")


def get_primary_platform(project_uuid: UUID) -> str | None:
    link = ProjectPlatformLink.objects.filter(research_project_uuid=project_uuid, is_primary=True).first()
    return link.platform_slug if link else None


def activate_logs_for_project(project_uuid: UUID, platform_slug: str, username: str = "", *, is_primary: bool = True):
    if not get_platform(platform_slug):
        raise ValueError(f"Unknown platform: {platform_slug}")
    if is_primary:
        ProjectPlatformLink.objects.filter(research_project_uuid=project_uuid, is_primary=True).update(is_primary=False)
    link, _ = ProjectPlatformLink.objects.get_or_create(
        research_project_uuid=project_uuid,
        platform_slug=platform_slug,
        defaults={"is_primary": is_primary, "activated_by_username": username},
    )
    if not _ and is_primary:
        link.is_primary = True
        link.save(update_fields=["is_primary"])
    return link


def get_logs_descriptor(project_uuid: UUID) -> ProjectCapabilityDescriptor | None:
    link = ProjectPlatformLink.objects.filter(research_project_uuid=project_uuid).order_by("-is_primary").first()
    if not link:
        return ProjectCapabilityDescriptor(
            capability_slug="logs",
            implementation_slug="logs",
            source_module="logs_app",
            active=False,
            label="Medir",
            summary={"message": "Logs no activado para este proyecto"},
        )
    spec = get_platform(link.platform_slug)
    summary = build_segment_summary(link.platform_slug)
    manage_url = module_url("logs", f"{link.platform_slug}/")
    return ProjectCapabilityDescriptor(
        capability_slug="logs",
        implementation_slug="logs",
        source_module="logs_app",
        active=True,
        label="Medir",
        manage_url=manage_url,
        api_url=module_url("logs", f"logs/api/platforms/{link.platform_slug}/segments/"),
        summary={
            "platform_slug": link.platform_slug,
            "platform_label": spec.label if spec else link.platform_slug,
            **{k: summary.get(k) for k in ("total_events", "unique_users", "recurrence", "pareto")},
        },
    )


def get_segment_summary(project_uuid: UUID, platform_slug: str | None = None) -> dict:
    slug = platform_slug or get_primary_platform(project_uuid)
    if not slug:
        return {}
    return build_segment_summary(slug)
