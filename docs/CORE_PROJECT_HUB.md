# CORE Project Hub — CORE_RETIRO MVP

## Tesis

CORE es una plataforma de investigación basada en **capacidades digitales**, no en apps:

```text
Instituto → Proyecto → Capacidad → Resultado
```

**Mantra:** Las apps implementan capacidades; no definen el proyecto.

## Posicionamiento (Maeztu)

> CORE es una plataforma de investigación basada en capacidades digitales. Cada proyecto declara las capacidades que necesita (medir, ontologizar, catalogar, geolocalizar, publicar, analizar) y CORE proporciona una infraestructura común para gestionarlas, registrar su actividad, generar resultados FAIR y publicarlos mediante APIs y JSON-LD. Las aplicaciones específicas (Leximus, Fondos, SONARE, ChordIA, etc.) actúan como implementadores de capacidades, no como el centro del sistema, permitiendo que la plataforma sea reutilizable por distintos institutos y dominios científicos.

## MVP en este repo

| Módulo | Capacidad | Implementador |
|--------|-----------|---------------|
| research_app | Hub institucional | — |
| logs_app | `logs` (Medir) | logs |
| leximus_app | `ontology` (Ontologizar) | leximus |

### Endpoints clave

- `/research/proyectos/<uuid>/` — ficha con tarjetas de capacidades
- `/research/proyectos/<uuid>/digital-profile.json` — perfil digital
- `/research/proyectos/<uuid>/digital-profile.json?format=jsonld` — envelope JSON-LD
- `/logs/<platform>/` — dashboard segmentado (arias, dz)
- `/leximus/api/taxonomies/<slug>/jsonld/` — taxonomía publicada

### Arranque local

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py migrate --database=research_db
python manage.py migrate --database=leximus_db
python manage.py seed_demo
python manage.py runserver
```

### Docker

```bash
docker compose up --build
```
