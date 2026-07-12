from __future__ import annotations
from dataclasses import dataclass, field

COMPETENCY_SPECS = [
    {
        "slug": "logs",
        "public_slug": "medir",
        "label": "Medir",
        "category": "digital",
        "tagline": "uso, adopción y recurrencia",
        "definition": (
            "Registrar y analizar cómo se utiliza un recurso digital: quién entra, "
            "qué consulta, con qué frecuencia y si vuelve. Es la competencia de "
            "«saber si alguien aprende o usa lo que has publicado»."
        ),
        "learning_outcome": "Comprender quién utiliza un resultado y cómo evoluciona ese uso.",
        "school_analogy": "Como las estadísticas de uso del aula virtual o de un material didáctico.",
        "result_types": ["métricas", "informes", "analíticas"],
        "mvp_active": True,
    },
    {
        "slug": "ontology",
        "public_slug": "ontologizar",
        "label": "Vincular conocimiento",
        "category": "digital",
        "tagline": "conceptos, relaciones y vocabularios",
        "definition": (
            "Integrar contenido nuevo al conocimiento ya estructurado: vincular textos y "
            "observaciones con conceptos, diccionarios y taxonomías existentes. "
            "No crea un vocabulario paralelo: propone y revisa antes de integrar."
        ),
        "learning_outcome": "Modelar conceptos y las relaciones entre ellos.",
        "school_analogy": "Como el glosario de una asignatura o el índice temático de un libro.",
        "result_types": ["taxonomías", "ontologías", "JSON-LD", "SKOS"],
        "mvp_active": True,
    },
    {
        "slug": "dataset",
        "public_slug": "catalogar",
        "label": "Catalogar",
        "category": "digital",
        "tagline": "inventarios y descripciones normalizadas",
        "definition": (
            "Describir recursos — textos, imágenes, piezas, muestras — con metadatos "
            "estables para que otros puedan encontrarlos y reutilizarlos. "
            "No es publicar todavía: es inventariar bien."
        ),
        "learning_outcome": "Describir recursos de forma normalizada y reutilizable.",
        "school_analogy": "Como la ficha de un libro en la biblioteca del centro.",
        "result_types": ["catálogos", "inventarios", "metadatos"],
        "mvp_active": True,
    },
    {
        "slug": "geodata",
        "public_slug": "geolocalizar",
        "label": "Geolocalizar",
        "category": "digital",
        "tagline": "mapas, territorio y coordenadas",
        "definition": (
            "Vincular conocimiento con lugares: mapas, coordenadas, rutas y capas "
            "espaciales. Sirve cuando el proyecto necesita responder «¿dónde ocurre esto?»."
        ),
        "learning_outcome": "Relacionar conocimiento y territorio.",
        "school_analogy": "Como el mapa mural del pueblo o un plano del instituto con datos.",
        "result_types": ["mapas", "GeoJSON", "datasets espaciales"],
        "mvp_active": True,
    },
    {
        "slug": "publish",
        "public_slug": "publicar",
        "label": "Publicar",
        "category": "digital",
        "tagline": "difundir resultados de forma abierta",
        "definition": (
            "Poner a disposición de otros los resultados de un proyecto: páginas web, "
            "APIs, portales y objetos FAIR. Es el paso final del cuaderno de investigación."
        ),
        "learning_outcome": "Difundir resultados para que otros puedan consultarlos y citarlos.",
        "school_analogy": "Como la exposición de fin de curso o el trabajo entregado al profesorado.",
        "result_types": ["webs", "APIs", "portales FAIR"],
        "mvp_active": True,
    },
    {
        "slug": "analysis",
        "public_slug": "analizar",
        "label": "Analizar",
        "category": "digital",
        "tagline": "interpretar datos y evidencias",
        "definition": (
            "Cruzar marcadores, mediciones y fuentes para sacar conclusiones. "
            "Va más allá de medir: explica patrones y responde preguntas de investigación."
        ),
        "learning_outcome": "Interpretar datos y evidencias reunidas en el proyecto.",
        "school_analogy": "Como la parte de conclusiones de un trabajo de investigación escolar.",
        "result_types": ["informes de análisis", "gráficos interpretados"],
        "mvp_active": False,
    },
    {
        "slug": "visualize",
        "public_slug": "visualizar",
        "label": "Visualizar",
        "category": "digital",
        "tagline": "gráficos, mapas mentales y paneles",
        "definition": (
            "Representar información de forma visual para facilitar su comprensión: "
            "diagramas, líneas temporales, paneles interactivos."
        ),
        "learning_outcome": "Representar conocimiento de forma clara y visual.",
        "school_analogy": "Como un cartel científico o un mural explicativo en el pasillo.",
        "result_types": ["visualizaciones", "paneles", "infografías"],
        "mvp_active": False,
    },
    {
        "slug": "preserve",
        "public_slug": "preservar",
        "label": "Preservar",
        "category": "digital",
        "tagline": "archivo, versiones y persistencia FAIR",
        "definition": (
            "Garantizar que los resultados sigan siendo accesibles en el tiempo: "
            "versionado, copias de seguridad, identificadores persistentes."
        ),
        "learning_outcome": "Mantener resultados accesibles y citables a largo plazo.",
        "school_analogy": "Como el archivo del centro que guarda los mejores proyectos de cada curso.",
        "result_types": ["archivos", "versiones", "repositorios"],
        "mvp_active": False,
    },
    {
        "slug": "narrate",
        "public_slug": "narrar",
        "label": "Narrar",
        "category": "interpretive",
        "tagline": "estructuras narrativas, dramaturgia, relato",
        "definition": (
            "Organizar y producir relatos: identificar unidades narrativas, escenas, "
            "conflictos y arcos dramáticos en cualquier medio — novela, teatro, cine, "
            "cómic, audio o relato oral."
        ),
        "learning_outcome": "Reconocer y construir estructuras narrativas coherentes.",
        "school_analogy": "Como analizar la estructura de un cuento o escribir el guion de una obra escolar.",
        "result_types": ["guiones", "relatos", "mapas narrativos", "corpus documentados"],
        "mvp_active": True,
    },
    {
        "slug": "archetype",
        "public_slug": "arquetipar",
        "label": "Arquetipar",
        "category": "interpretive",
        "tagline": "funciones, patrones y figuras recurrentes",
        "definition": (
            "Reconocer funciones, patrones y figuras recurrentes en una narración: "
            "roles dramáticos, transformaciones y símbolos que se repiten entre obras, "
            "sin reducir personajes a listas cerradas ni clasificaciones psicológicas."
        ),
        "intro_note": (
            "Arquetipar no consiste en reducir personajes a una lista cerrada, sino en "
            "describir las funciones, conflictos, transformaciones y símbolos que se "
            "repiten entre obras."
        ),
        "learning_outcome": "Identificar figuras y funciones narrativas que atraviesan distintas obras y medios.",
        "school_analogy": "Como reconocer el arco del héroe en un mito y volver a encontrarlo en una novela o una obra de teatro.",
        "result_types": ["análisis de figuras", "patrones narrativos", "fichas de funciones"],
        "mvp_active": True,
    },
    {
        "slug": "interpret",
        "public_slug": "interpretar",
        "label": "Interpretar",
        "category": "interpretive",
        "tagline": "símbolos, contextos, significados",
        "definition": (
            "Atribuir significados a elementos narrativos documentando la fuente, "
            "el marco analítico y el alcance de cada lectura. Distingue hechos "
            "documentales de interpretaciones fundamentadas."
        ),
        "learning_outcome": "Formular lecturas argumentadas y distinguirlas de los datos documentales.",
        "school_analogy": "Como la interpretación de un poema en clase, citando el texto y explicando el marco con el que se lee.",
        "result_types": ["lecturas documentadas", "relaciones interpretativas", "notas críticas"],
        "mvp_active": True,
    },
    {
        "slug": "argue",
        "public_slug": "argumentar",
        "label": "Argumentar",
        "category": "interpretive",
        "tagline": "pensamiento crítico, investigación, documentación",
        "definition": (
            "Construir razonamientos fundamentados: plantear hipótesis, reunir "
            "evidencias, contrastar fuentes y documentar conclusiones de forma "
            "revisable."
        ),
        "learning_outcome": "Sostener una tesis con evidencias y referencias verificables.",
        "school_analogy": "Como el ensayo de historia o el trabajo de investigación con bibliografía y citas.",
        "result_types": ["ensayos", "informes argumentados", "revisiones bibliográficas"],
        "mvp_active": False,
    },
]

PUBLIC_CAPABILITIES = COMPETENCY_SPECS

CAPABILITY_FAMILIES = [
    {
        "slug": "structure",
        "label": "Estructurar",
        "tagline": "Integrar contenido al conocimiento ya estructurado",
        "lineage": "Leximus",
    },
    {
        "slug": "publish",
        "label": "Publicar",
        "tagline": "Difundir resultados de forma abierta",
        "lineage": "Wagtail",
    },
    {
        "slug": "explore",
        "label": "Explorar",
        "tagline": "Navegar y visualizar el conocimiento existente",
        "lineage": "Teatrero",
        "label_variants": ["Navegar", "Explorar y visualizar"],
    },
]

_LEGACY_FAMILY_MAP: dict[str, str | None] = {
    "ontology": "structure",
    "dataset": "structure",
    "publish": "publish",
    "geodata": "explore",
    "visualize": "explore",
    "logs": "explore",
    "analysis": "explore",
    "preserve": None,
}


def legacy_slug_to_family(slug: str) -> str | None:
    return _LEGACY_FAMILY_MAP.get(slug)


ARCHETYPE_FIGURE_LABELS = frozenset({
    "Héroe idealista", "Mentor", "Antagonista", "Trickster",
    "Doncella", "Guardián", "Sombra",
})


def get_competency(slug: str) -> dict | None:
    for c in COMPETENCY_SPECS:
        if c["slug"] == slug or c["public_slug"] == slug:
            return c
    return None


def get_public_capability_by_slug(public_slug: str) -> dict | None:
    for c in COMPETENCY_SPECS:
        if c["public_slug"] == public_slug:
            return c
    return None


def capabilities_by_category(category: str) -> list[dict]:
    return [c for c in COMPETENCY_SPECS if c.get("category") == category]


_CAPABILITY_MODULE_MAP = {
    "logs": "logs",
    "ontology": "ontologizar",
    "dataset": "ontologizar",
    "geodata": "ontologizar",
    "publish": "research",
    "analysis": "research",
    "visualize": "research",
    "preserve": "research",
    "narrate": "ontologizar",
    "archetype": "ontologizar",
    "interpret": "ontologizar",
    "argue": "research",
}


def is_capability_module_enabled(slug: str) -> bool:
    from django.conf import settings

    mod = _CAPABILITY_MODULE_MAP.get(slug)
    if not mod:
        return False
    return mod in getattr(settings, "CORE_ENABLED_MODULES", [])


def _ui_capability_entry(cap: dict) -> dict:
    return {
        "slug": cap["slug"],
        "label": cap["label"],
        "tagline": cap["tagline"],
        "category": cap["category"],
        "public_slug": cap["public_slug"],
        "enabled": cap["mvp_active"] and is_capability_module_enabled(cap["slug"]),
        "coming_soon": not cap["mvp_active"],
        "definition": cap.get("definition", ""),
    }


def capabilities_grouped_by_family(category: str = "digital") -> list[dict]:
    """Agrupa acciones legacy bajo familias operativas (Fase 0 — sin cambio de BD)."""
    caps = capabilities_by_category(category)
    by_slug = {f["slug"]: {**f, "actions": []} for f in CAPABILITY_FAMILIES}
    for cap in caps:
        family_slug = legacy_slug_to_family(cap["slug"])
        if not family_slug or family_slug not in by_slug:
            continue
        by_slug[family_slug]["actions"].append(_ui_capability_entry(cap))
    return [by_slug[f["slug"]] for f in CAPABILITY_FAMILIES]


def homepage_capability_groups() -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {"digital": [], "interpretive": []}
    for cap in COMPETENCY_SPECS:
        entry = {
            "slug": cap["slug"],
            "label": cap["label"],
            "tagline": cap["tagline"],
            "category": cap["category"],
            "public_slug": cap["public_slug"],
            "enabled": cap["mvp_active"] and is_capability_module_enabled(cap["slug"]),
            "coming_soon": not cap["mvp_active"],
            "definition": cap.get("definition", ""),
        }
        groups.setdefault(cap["category"], []).append(entry)
    return groups


def is_digital_capability(slug: str) -> bool:
    cap = get_competency(slug)
    return bool(cap and cap.get("category") == "digital")


VALID_CAPABILITY_SLUGS = frozenset(c["slug"] for c in COMPETENCY_SPECS)


@dataclass
class ProjectCapabilityDescriptor:
    capability_slug: str
    implementation_slug: str
    source_module: str
    active: bool
    label: str
    manage_url: str | None = None
    api_url: str | None = None
    jsonld_url: str | None = None
    summary: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "capability_slug": self.capability_slug,
            "implementation_slug": self.implementation_slug,
            "source_module": self.source_module,
            "active": self.active,
            "label": self.label,
            "manage_url": self.manage_url,
            "api_url": self.api_url,
            "jsonld_url": self.jsonld_url,
            "summary": self.summary,
        }
