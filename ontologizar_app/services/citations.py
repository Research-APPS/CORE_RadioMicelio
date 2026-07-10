from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ontologizar_app.models import Concept

EDITORIAL_DISCLAIMER = (
    "Definición editorial de CORE Radio Micelio basada en terminología IUPAC. "
    "No se reproduce texto normativo literal."
)

AUTHORITY_LEVEL_PRIORITY = {
    "terminological_reference": 100,
    "technical_standard": 90,
    "scientific_publication": 80,
    "dataset": 70,
    "educational": 50,
    "historical_archive": 40,
}


class SourceKind(str, Enum):
    REFERENCIA_TERMINOLOGICA = "referencia_terminologica"
    DATASET = "dataset"
    RECURSO_DIDACTICO = "recurso_didactico"
    PUBLICACION_CIENTIFICA = "publicacion_cientifica"
    NORMA_TECNICA = "norma_tecnica"
    ARCHIVO_HISTORICO = "archivo_historico"

    @classmethod
    def from_value(cls, raw: str) -> SourceKind | None:
        normalized = raw.strip().lower().replace("-", "_").replace(" ", "_")
        aliases = {
            "standard": cls.REFERENCIA_TERMINOLOGICA,
            "educational": cls.RECURSO_DIDACTICO,
        }
        if normalized in aliases:
            return aliases[normalized]
        for member in cls:
            if member.value == normalized:
                return member
        return None


@dataclass(frozen=True)
class Citation:
    label: str
    url: str
    kind: SourceKind
    authority: str = ""
    authority_level: str = ""

    @property
    def sort_key(self) -> tuple[int, str]:
        priority = AUTHORITY_LEVEL_PRIORITY.get(self.authority_level, 0)
        return (-priority, self.label.lower())


def parse_reference_line(text: str) -> Citation | None:
    text = text.strip()
    if not text:
        return None
    parts = [p.strip() for p in text.split("|")]
    if len(parts) < 3:
        return None
    label, url, kind_raw = parts[0], parts[1], parts[2]
    if not label or not url:
        return None
    kind = SourceKind.from_value(kind_raw)
    if kind is None:
        return None
    authority = parts[3] if len(parts) > 3 else ""
    authority_level = parts[4] if len(parts) > 4 else ""
    return Citation(
        label=label,
        url=url,
        kind=kind,
        authority=authority,
        authority_level=authority_level,
    )


def format_reference_line(citation: Citation) -> str:
    parts = [citation.label, citation.url, citation.kind.value]
    if citation.authority or citation.authority_level:
        parts.extend([citation.authority, citation.authority_level])
    return " | ".join(parts)


def citation_badge(citation: Citation) -> str:
    if (
        citation.kind == SourceKind.REFERENCIA_TERMINOLOGICA
        and citation.authority.upper() == "IUPAC"
    ):
        return "referencia IUPAC"
    badges = {
        SourceKind.REFERENCIA_TERMINOLOGICA: "norma terminológica",
        SourceKind.DATASET: "base de datos",
        SourceKind.RECURSO_DIDACTICO: "recurso didáctico",
        SourceKind.PUBLICACION_CIENTIFICA: "publicación científica",
        SourceKind.NORMA_TECNICA: "norma técnica",
        SourceKind.ARCHIVO_HISTORICO: "archivo histórico",
    }
    return badges.get(citation.kind, citation.kind.value.replace("_", " "))


def concept_citations(concept: Concept) -> list[Citation]:
    citations: list[Citation] = []
    for definition in concept.definitions.filter(is_active=True, kind="reference"):
        parsed = parse_reference_line(definition.text)
        if parsed:
            citations.append(parsed)
    citations.sort(key=lambda c: c.sort_key)
    return citations


def concept_has_terminological_reference(concept: Concept) -> bool:
    return any(
        c.kind == SourceKind.REFERENCIA_TERMINOLOGICA
        and c.authority_level == "terminological_reference"
        for c in concept_citations(concept)
    )


def concept_provenance_level(concept: Concept) -> str | None:
    levels = [c.authority_level for c in concept_citations(concept) if c.authority_level]
    if not levels:
        return None
    return max(levels, key=lambda level: AUTHORITY_LEVEL_PRIORITY.get(level, 0))


def citations_to_jsonld(citations: list[Citation]) -> list[dict]:
    items: list[dict] = []
    for citation in citations:
        entry: dict = {
            "@type": "CreativeWork",
            "name": citation.label,
            "url": citation.url,
        }
        if citation.kind == SourceKind.DATASET:
            entry["additionalType"] = "https://schema.org/Dataset"
        if "goldbook" in citation.url and "V06588" in citation.url:
            entry["identifier"] = "10.1351/goldbook.V06588"
        items.append(entry)
    return items


def citations_is_based_on(citations: list[Citation]) -> list[dict]:
    for citation in citations:
        if (
            citation.kind == SourceKind.REFERENCIA_TERMINOLOGICA
            and citation.authority_level == "terminological_reference"
            and "V06588" in citation.url
        ):
            return [{"@id": "https://doi.org/10.1351/goldbook.V06588"}]
    return []
