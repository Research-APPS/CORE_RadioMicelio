# Contrato de instancia — CORE

> Modelo conceptual de **qué configura una instancia** de CORE.
> Objetivo: que el *corazón* del sistema (código + ontología) pueda trasladarse
> de una institución a otra **sin arrastrar decisiones propias de Radio Micelio**.

## Principio

Un "core" reproducible separa con disciplina tres planos:

```text
CÓDIGO         (el core, idéntico para todas las instituciones)  → git / imagen Docker
CONFIGURACIÓN  (lo propio de cada institución)                   → variables de entorno
DATOS          (el contenido de cada institución)                → volúmenes + importadores/fixtures
```

La replicabilidad existe cuando **el mismo código sirve a N instituciones** y lo
único que cambia entre despliegues es *configuración* + *datos*. Si algo
específico de una institución se cuela en el código, deja de ser un core y pasa
a ser un fork.

Esto sigue el principio *12-factor* de tratar la configuración, las bases de
datos y el almacenamiento como **recursos conectados al código, no incrustados
en él**.

## Modelo del contrato

Una instancia debería poder responder, mediante configuración, a estas
preguntas. Se expresa aquí en YAML por claridad conceptual; en producción puede
materializarse como variables de entorno.

```yaml
institution:
  slug: radio-micelio
  name: CORE Radio Micelio
  public_url: https://core.radiomicelio.es
  language: es
  timezone: Europe/Madrid

modules:            # capacidades activables/desactivables por instancia
  research: true
  ontology: true
  corpus: true
  logs: false
  cms: true

semantic:
  namespace: https://core.radiomicelio.es/id/   # base de las URIs de las entidades
  default_profile: research-institute

data:
  bootstrap_profile: radio_micelio              # paquete de datos de arranque
  demo_data: false                              # nunca cargar demo en producción por defecto
```

> No es obligatorio usar YAML en producción. Lo importante es que exista **un
> modelo documentado** de qué define una instancia, y que ese modelo se refleje
> en las variables de entorno reales.

## Mapeo con las variables de entorno actuales

El proyecto ya está cerca de este contrato. Variables existentes que lo
implementan (total o parcialmente):

| Concepto del contrato        | Variable actual              |
|------------------------------|------------------------------|
| `institution.name`           | `CORE_INSTITUTE_NAME`        |
| `modules.*`                  | `CORE_ENABLED_MODULES`       |
| URLs por módulo              | `CORE_URL_RESEARCH`, `CORE_URL_LOGS`, `CORE_URL_ONTOLOGIZAR` |
| `institution.public_url`     | `SITE_URL`                   |
| publicación estática         | `STATIC_SITE_CNAME`          |
| secreto de aplicación        | `SECRET_KEY`                 |
| modo                         | `DEBUG`                      |
| conmutación de base de datos | `POSTGRES_*` / SQLite        |

Pendientes de formalizar como configuración de instancia:

- `institution.slug`, `language`, `timezone`.
- `semantic.namespace` y `semantic.default_profile` (hoy implícitos).
- `data.bootstrap_profile` y `data.demo_data` (hoy la demo se carga en cada arranque; ver `ROADMAP_REPRODUCIBILIDAD.md`).

## Qué NO pertenece al contrato (debe salir del código)

- Vocabularios y relaciones específicas de un dominio (p. ej. `escudero_de`,
  `monta_a`, `ama_a`): pertenecen a un **paquete semántico** de la
  asignatura/institución, no al motor universal. Ver la sección "Capa semántica"
  en `ROADMAP_REPRODUCIBILIDAD.md`.
- Datos de demostración de Radio Micelio.
- Bases de datos SQLite versionadas con contenido real.

## Referencias

- The Twelve-Factor App — *Config* y *Backing services*.
- Docker Compose — variables de entorno, interpolación y archivos `.env`.
- Docker — volúmenes como mecanismo de persistencia independiente del contenedor.
- Django — *Deployment checklist* (`manage.py check --deploy`).
- W3C SKOS — modelo de `ConceptScheme`, conceptos y relaciones para vocabularios.
