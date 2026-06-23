from __future__ import annotations
from dataclasses import dataclass, field
from uuid import UUID

from django.conf import settings

from core_retiro.core_urls import module_url
from research_app.capability_registry import ProjectCapabilityDescriptor
from research_app.models import (
    LearningMarker, ProyectoInvestigacion, ProjectCurriculumDeclaration,
    ScientificActivity, ScientificResult,
)


@dataclass
class ProjectDigitalProfile:
    project_uuid: str
    titulo: str
    acron: str
    institute: str
    markers: list[dict] = field(default_factory=list)
    curriculum: dict = field(default_factory=dict)
    capabilities: list[ProjectCapabilityDescriptor] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "project_uuid": self.project_uuid,
            "titulo": self.titulo,
            "acron": self.acron,
            "institute": self.institute,
            "markers": self.markers,
            "curriculum": self.curriculum,
            "capabilities": [c.to_dict() for c in self.capabilities],
            "metrics": self.metrics,
        }


def _logs_descriptor(project_uuid):
    from logs_app.services.research_bridge import get_logs_descriptor
    return get_logs_descriptor(project_uuid)


def get_project_digital_profile(project_uuid: UUID) -> ProjectDigitalProfile | None:
    project = ProyectoInvestigacion.objects.filter(uuid=project_uuid, activo=True).first()
    if not project:
        return None

    markers = [
        {
            "concept_uuid": str(m.concept_uuid),
            "concept_label": m.concept_label,
            "subject": m.subject_slug,
            "dictionary": m.dictionary_slug,
            "taxonomy": m.taxonomy_slug,
            "status": m.status,
            "jsonld_url": m.jsonld_url,
            "note": m.note,
        }
        for m in project.markers.all()
    ]

    declarations = list(
        project.declarations.values_list("capability_slug", flat=True)
    )
    activities = [
        {
            "slug": a.slug,
            "title": a.title,
            "capability": a.capability_slug,
            "status": a.status,
            "results": [r.title for r in a.results.all()],
        }
        for a in project.activities.all()
    ]

    capabilities = []
    if "logs" in getattr(settings, "CORE_ENABLED_MODULES", []):
        desc = _logs_descriptor(project_uuid)
        if desc:
            capabilities.append(desc)

    metrics = {"marker_count": len(markers), "activity_count": len(activities)}
    if capabilities and capabilities[0].summary.get("unique_users"):
        metrics["users"] = capabilities[0].summary.get("unique_users")
        metrics["visits"] = capabilities[0].summary.get("total_events")

    return ProjectDigitalProfile(
        project_uuid=str(project_uuid),
        titulo=project.titulo,
        acron=project.acron,
        institute=getattr(settings, "CORE_INSTITUTE_NAME", "CORE Radio Micelio"),
        markers=markers,
        curriculum={
            "declared_capabilities": declarations,
            "activities": activities,
        },
        capabilities=capabilities,
        metrics=metrics,
    )


def build_digital_profile_jsonld(profile: ProjectDigitalProfile) -> dict:
    ns = getattr(settings, "CORE_JSONLD_NAMESPACE", "https://core.radiomicelio/ns/")
    return {
        "@context": ["https://schema.org/", {"core": ns}],
        "@type": "ResearchProject",
        "@id": module_url("research", f"proyectos/{profile.project_uuid}"),
        "name": profile.titulo,
        "alternateName": profile.acron or None,
        "core:markers": profile.markers,
        "core:curriculum": profile.curriculum,
        "core:metrics": profile.metrics,
    }
