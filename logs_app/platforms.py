from __future__ import annotations
from dataclasses import dataclass

from django.db.models import Q


@dataclass(frozen=True)
class PlatformSpec:
    slug: str
    label: str
    description: str
    filter_q: Q


PLATFORMS = {
    "aula-virtual": PlatformSpec(
        slug="aula-virtual",
        label="Aula virtual",
        description="Recursos y actividades del aula digital",
        filter_q=Q(application__icontains="aula-virtual") | Q(application__icontains="aula"),
    ),
    "biblioteca-escolar": PlatformSpec(
        slug="biblioteca-escolar",
        label="Biblioteca escolar",
        description="Consultas a la biblioteca y materiales didácticos",
        filter_q=Q(application__icontains="biblioteca") | Q(name__icontains="recurso"),
    ),
}


def get_platform(slug: str) -> PlatformSpec | None:
    return PLATFORMS.get(slug)


def list_platforms():
    return list(PLATFORMS.values())
