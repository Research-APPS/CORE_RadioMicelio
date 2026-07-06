"""
Registro semántico de relaciones (Fase 1 del plan "AIRAM grafo verbalizador").

Convierte un `ConceptRelation.relation_type` crudo (ej. "enables") en un bloque
verbalizado (icono + pregunta + frase) sin LLM: todo determinista desde
plantillas fijas en este módulo. No introduce ningún modelo nuevo — sigue
siendo el mismo `relation_type` de `ontologizar_app.ConceptRelation`, solo
cambia cómo se presenta.

`related`, `broader`, `narrower` son legacy SKOS (siguen aceptándose y
verbalizándose vía LEGACY_MAP). `partOf` (camelCase histórico) se normaliza
internamente a `part_of`; nunca se escribe camelCase en datos nuevos.
"""

from __future__ import annotations

from dataclasses import dataclass

# ─── Lista canónica (única fuente de verdad) ──────────────────────────────────

RELATION_TYPES = [
    "related",             # legacy SKOS
    "broader",             # legacy SKOS
    "narrower",            # legacy SKOS
    "part_of",
    "has_part",
    "produces",
    "enables",
    "participates_in",
    "works_via",
    "evolves_from",
    "evolves_to",
    "historically_after",
    "historically_before",
    "appears_in",
    "invented_by",
    "used_in",
    "transmits_to",
    "may_fail_as",
    "requires_maintenance",
    "may_lead_to",
    # Añadidos para el corpus literario del Quijote (mismo snake_case,
    # vocabulario en español porque es el idioma natural del dominio):
    "monta_a",
    "escudero_de",
    "ama_a",
    "ocurre_en",
    "advierte_a",
    "ataca_a",
]

# Alias de entrada histórica -> forma canónica.
LEGACY_ALIASES = {
    "partOf": "part_of",
}


@dataclass
class VerbalizedRelation:
    icon: str
    question: str
    sentence: str
    relation_type: str
    lens: str
    direction: str = "out"


# ─── Lentes de exploración ─────────────────────────────────────────────────────
# (declaradas aquí, no solo en Fase 4, porque RELATION_REGISTRY ya necesita
# asignar una lente por tipo desde el principio)

EXPLORATION_LENSES = {
    "temario":        {"icon": "📚", "label": "Temario"},
    "historia":       {"icon": "📜", "label": "Historia"},
    "funcionamiento": {"icon": "⚙️", "label": "Funcionamiento"},
    "componentes":    {"icon": "🧩", "label": "Componentes"},
    "averias":        {"icon": "🔧", "label": "Averías"},
    "personas":       {"icon": "👤", "label": "Personas"},
    "aplicaciones":   {"icon": "🏭", "label": "Aplicaciones"},
    "ciencia":        {"icon": "🔬", "label": "Ciencia"},
    "evolucion":      {"icon": "➡️", "label": "Evolución"},
}

_DEFAULT_LENS = "temario"


# ─── Verbalización de relaciones legacy SKOS ──────────────────────────────────

LEGACY_MAP = {
    "related": {
        "icon": "🔗",
        "question": "¿Con qué se relaciona {source}?",
        "sentence": "{source} se relaciona con {target}.",
        "lens": "temario",
        "inverse": {
            "question": "¿Con qué se relaciona {target}?",
            "sentence": "{target} se relaciona con {source}.",
        },
    },
    "broader": {
        "icon": "⬆️",
        "question": "¿De qué es un caso más específico {source}?",
        "sentence": "{source} es un caso más específico de {target}.",
        "lens": "temario",
        "inverse": {
            "question": "¿Qué casos más específicos tiene {target}?",
            "sentence": "{target} incluye a {source}.",
        },
    },
    "narrower": {
        "icon": "⬇️",
        "question": "¿Qué casos más específicos tiene {source}?",
        "sentence": "{source} incluye a {target}.",
        "lens": "temario",
        "inverse": {
            "question": "¿De qué es un caso más específico {target}?",
            "sentence": "{target} es un caso más específico de {source}.",
        },
    },
}


# ─── Registro semántico (tipos nuevos, snake_case) ────────────────────────────

RELATION_REGISTRY = {
    "part_of": {
        "icon": "🧩",
        "question": "¿De qué es parte {source}?",
        "sentence": "{source} es parte de {target}.",
        "lens": "componentes",
        "inverse": {
            "question": "¿Qué partes tiene {target}?",
            "sentence": "{target} tiene como parte a {source}.",
        },
    },
    "has_part": {
        "icon": "🧩",
        "question": "¿Qué partes tiene {source}?",
        "sentence": "{source} tiene como parte a {target}.",
        "lens": "componentes",
        "inverse": {
            "question": "¿De qué es parte {target}?",
            "sentence": "{target} es parte de {source}.",
        },
    },
    "produces": {
        "icon": "🌱",
        "question": "¿Qué produce {source}?",
        "sentence": "{source} produce {target}.",
        "lens": "funcionamiento",
        "inverse": {
            "question": "¿Qué produce a {target}?",
            "sentence": "{target} es producido por {source}.",
        },
    },
    "enables": {
        "icon": "🌬️",
        "question": "¿Qué permite {source}?",
        "sentence": "{source} permite {target}.",
        "lens": "funcionamiento",
        "inverse": {
            "question": "¿Qué hace posible a {target}?",
            "sentence": "{target} es posible gracias a {source}.",
        },
    },
    "participates_in": {
        "icon": "⚔️",
        "question": "¿En qué participa {source}?",
        "sentence": "{source} participa en {target}.",
        "lens": "aplicaciones",
        "inverse": {
            "question": "¿Quién participa en {target}?",
            "sentence": "{target} tiene como participante a {source}.",
        },
    },
    "works_via": {
        "icon": "⚙️",
        "question": "¿Cómo funciona {source}?",
        "sentence": "{source} funciona mediante {target}.",
        "lens": "funcionamiento",
        "inverse": {
            "question": "¿Qué funciona mediante {target}?",
            "sentence": "{target} es el mecanismo de {source}.",
        },
    },
    "evolves_from": {
        "icon": "➡️",
        "question": "¿De qué evoluciona {source}?",
        "sentence": "{source} evoluciona de {target}.",
        "lens": "evolucion",
        "inverse": {
            "question": "¿En qué evoluciona {target}?",
            "sentence": "{target} evoluciona hacia {source}.",
        },
    },
    "evolves_to": {
        "icon": "➡️",
        "question": "¿En qué evoluciona {source}?",
        "sentence": "{source} evoluciona hacia {target}.",
        "lens": "evolucion",
        "inverse": {
            "question": "¿De qué evoluciona {target}?",
            "sentence": "{target} evoluciona de {source}.",
        },
    },
    "historically_after": {
        "icon": "📜",
        "question": "¿A qué sigue históricamente {source}?",
        "sentence": "{source} viene después de {target}.",
        "lens": "historia",
        "inverse": {
            "question": "¿Qué vino después de {target}?",
            "sentence": "{target} viene antes de {source}.",
        },
    },
    "historically_before": {
        "icon": "📜",
        "question": "¿A qué precede {source}?",
        "sentence": "{source} viene antes de {target}.",
        "lens": "historia",
        "inverse": {
            "question": "¿Qué precedió a {target}?",
            "sentence": "{target} viene después de {source}.",
        },
    },
    "appears_in": {
        "icon": "📖",
        "question": "¿Dónde aparece {source}?",
        "sentence": "{source} aparece en {target}.",
        "lens": "historia",
        "inverse": {
            "question": "¿Qué aparece en {target}?",
            "sentence": "{target} tiene apariciones de {source}.",
        },
    },
    "invented_by": {
        "icon": "👤",
        "question": "¿Quién inventó {source}?",
        "sentence": "{source} fue inventado por {target}.",
        "lens": "personas",
        "inverse": {
            "question": "¿Qué inventó {target}?",
            "sentence": "{target} inventó {source}.",
        },
    },
    "used_in": {
        "icon": "🏭",
        "question": "¿Dónde se usa {source}?",
        "sentence": "{source} se usa en {target}.",
        "lens": "aplicaciones",
        "inverse": {
            "question": "¿Qué se usa en {target}?",
            "sentence": "{target} usa {source}.",
        },
    },
    "transmits_to": {
        "icon": "🔧",
        "question": "¿A qué transmite movimiento {source}?",
        "sentence": "{source} transmite movimiento a {target}.",
        "lens": "componentes",
        "inverse": {
            "question": "¿Qué le transmite movimiento a {target}?",
            "sentence": "{target} recibe movimiento de {source}.",
        },
    },
    "may_fail_as": {
        "icon": "🔧",
        "question": "¿Cómo puede fallar {source}?",
        "sentence": "{source} puede fallar como {target}.",
        "lens": "averias",
        "inverse": {
            "question": "¿Qué componente puede causar {target}?",
            "sentence": "{target} puede deberse a un fallo en {source}.",
        },
    },
    "requires_maintenance": {
        "icon": "🔧",
        "question": "¿Qué mantenimiento requiere {source}?",
        "sentence": "{source} requiere {target}.",
        "lens": "averias",
        "inverse": {
            "question": "¿Qué requiere {target}?",
            "sentence": "{target} es requerido por {source}.",
        },
    },
    "may_lead_to": {
        "icon": "🔧",
        "question": "¿A qué puede llevar {source}?",
        "sentence": "{source} puede llevar a {target}.",
        "lens": "averias",
        "inverse": {
            "question": "¿Qué puede llevar a {target}?",
            "sentence": "{target} puede originarse en {source}.",
        },
    },
    # --- Quijote / corpus literario ---
    "monta_a": {
        "icon": "🐴",
        "question": "¿A qué monta {source}?",
        "sentence": "{source} monta a {target}.",
        "lens": "personas",
        "inverse": {
            "question": "¿Quién monta a {target}?",
            "sentence": "{target} es montado por {source}.",
        },
    },
    "escudero_de": {
        "icon": "🛡️",
        "question": "¿De quién es escudero {source}?",
        "sentence": "{source} es escudero de {target}.",
        "lens": "personas",
        "inverse": {
            "question": "¿Quién tiene por escudero a {target}?",
            "sentence": "{target} tiene por escudero a {source}.",
        },
    },
    "ama_a": {
        "icon": "❤️",
        "question": "¿A quién ama {source}?",
        "sentence": "{source} ama a {target}.",
        "lens": "personas",
        "inverse": {
            "question": "¿Quién ama a {target}?",
            "sentence": "{target} es amado/a por {source}.",
        },
    },
    "ocurre_en": {
        "icon": "📍",
        "question": "¿Dónde ocurre {source}?",
        "sentence": "{source} ocurre en {target}.",
        "lens": "historia",
        "inverse": {
            "question": "¿Qué ocurre en {target}?",
            "sentence": "{target} es escenario de {source}.",
        },
    },
    "advierte_a": {
        "icon": "⚠️",
        "question": "¿A quién advierte {source}?",
        "sentence": "{source} advierte a {target}.",
        "lens": "personas",
        "inverse": {
            "question": "¿Quién advierte a {target}?",
            "sentence": "{target} es advertido/a por {source}.",
        },
    },
    "ataca_a": {
        "icon": "⚔️",
        "question": "¿A quién o qué ataca {source}?",
        "sentence": "{source} ataca a {target}.",
        "lens": "aplicaciones",
        "inverse": {
            "question": "¿Quién ataca a {target}?",
            "sentence": "{target} es atacado/a por {source}.",
        },
    },
}


def normalize_relation_type(raw: str) -> str:
    """Normaliza un relation_type crudo a su forma canónica en RELATION_TYPES.

    - Alias legacy conocidos (ej. "partOf") -> forma canónica ("part_of").
    - Ya canónico -> sin cambio.
    - Desconocido -> "related" (fallback).
    """
    if not raw:
        return "related"
    if raw in LEGACY_ALIASES:
        return LEGACY_ALIASES[raw]
    if raw in RELATION_TYPES:
        return raw
    return "related"


def is_known_relation(raw: str) -> bool:
    return raw in RELATION_TYPES or raw in LEGACY_ALIASES


def relation_lens(relation_type: str) -> str:
    canonical = normalize_relation_type(relation_type)
    entry = RELATION_REGISTRY.get(canonical) or LEGACY_MAP.get(canonical)
    return entry["lens"] if entry else _DEFAULT_LENS


def verbalize_relation(source_label: str, target_label: str, relation_type: str, direction: str = "out") -> VerbalizedRelation:
    """Construye el bloque verbalizado {icono, pregunta, frase} para una relación.

    `direction="out"` verbaliza desde el punto de vista de `source` (plantilla
    principal); `direction="in"` usa la plantilla `inverse` (punto de vista de
    `target`), intercambiando qué label se llama `source`/`target` en el texto.
    """
    canonical = normalize_relation_type(relation_type)
    entry = RELATION_REGISTRY.get(canonical) or LEGACY_MAP.get(canonical) or LEGACY_MAP["related"]

    template = entry
    ctx = {"source": source_label, "target": target_label}
    if direction == "in" and "inverse" in entry:
        template = entry["inverse"]

    return VerbalizedRelation(
        icon=entry["icon"],
        question=template["question"].format(**ctx),
        sentence=template["sentence"].format(**ctx),
        relation_type=canonical,
        lens=entry["lens"],
        direction=direction,
    )
