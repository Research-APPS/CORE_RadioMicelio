from __future__ import annotations
from dataclasses import dataclass, field

COMPETENCY_SPECS = [
    {
        "slug": "logs",
        "public_slug": "medir",
        "label": "Medir",
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
        "label": "Ontologizar",
        "tagline": "conceptos, relaciones y vocabularios",
        "definition": (
            "Organizar el conocimiento en conceptos relacionados: diccionarios, taxonomías "
            "y fichas semánticas (JSON-LD). Permite que distintos proyectos compartan "
            "el mismo vocabulario sin copiar contenidos."
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
]

PUBLIC_CAPABILITIES = COMPETENCY_SPECS


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
