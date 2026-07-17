# CORE Project Hub — CORE Radio Micelio MVP

## Tesis

CORE es una plataforma de investigación basada en **capacidades digitales**, no en apps:

```text
Instituto → Proyecto → Capacidad → Resultado
```

**Mantra:** Las apps implementan capacidades; no definen el proyecto.

## Posicionamiento

> CORE es una plataforma de investigación basada en capacidades digitales. Cada proyecto declara las capacidades que necesita (medir, ontologizar, catalogar, geolocalizar, publicar, analizar) y CORE proporciona una infraestructura común para gestionarlas, registrar su actividad, generar resultados FAIR y publicarlos mediante APIs y JSON-LD. Los módulos del sistema (ontologizar, medir, biblioteca, etc.) actúan como implementadores de capacidades, no como el centro del sistema, permitiendo que la plataforma sea reutilizable por distintos centros y dominios.

## MVP en este repo

| Módulo | Capacidad | Implementador |
|--------|-----------|---------------|
| research_app | Hub institucional | — |
| logs_app | `logs` (Medir) | logs |
| ontologizar_app | `ontology` (Ontologizar) | ontologizar |

### Endpoints clave

- `/research/proyectos/<uuid>/` — ficha con tarjetas de capacidades
- `/research/proyectos/<uuid>/digital-profile.json` — perfil digital
- `/research/proyectos/<uuid>/digital-profile.json?format=jsonld` — envelope JSON-LD
- `/logs/<platform>/` — dashboard segmentado (arias, dz)
- `/ontologizar/api/taxonomies/<slug>/jsonld/` — taxonomía publicada

### Arranque local

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py migrate --database=research_db
python manage.py migrate --database=ontologizar_db
python manage.py seed_demo
python manage.py runserver
```

### Docker

```bash
docker compose up --build
```

## Reproducibilidad e instancias

CORE aspira a ser una infraestructura **replicable** por distintos centros: el
mismo código sirve a N instituciones y solo cambian configuración y datos.

- [`INSTANCE_CONTRACT.md`](INSTANCE_CONTRACT.md) — modelo de qué configura una instancia (código vs. configuración vs. datos).
- [`ROADMAP_REPRODUCIBILIDAD.md`](ROADMAP_REPRODUCIBILIDAD.md) — secuencia R1–R4, problemas concretos a corregir (secretos en Compose, `seed_demo` en arranque, nº de bases, SQLite versionadas) y generalización de la capa semántica.
