# Roadmap de reproducibilidad — CORE

> De "aplicación de Radio Micelio" a **infraestructura soberana y replicable**
> para instituciones de investigación y cooperativas.

La secuencia empieza por la **reproducibilidad operativa** (no solo escribir un
`.env.example`), definiendo primero un **contrato de instancia** (ver
`INSTANCE_CONTRACT.md`). La ontología es el corazón intelectual del sistema,
pero antes conviene asegurar que ese corazón pueda trasladarse de una
institución a otra sin arrastrar decisiones propias de Radio Micelio.

## Orden propuesto

```text
1. Contrato de instancia
2. Configuración + Docker Compose reproducible
3. Ciclo explícito de migración e inicialización
4. Exportación/importación de datos institucionales
5. Generalización de la capa semántica
6. Plantilla para nuevas instituciones
```

## Lo que ya existe (no reescribir, formalizar)

El repositorio está más cerca del objetivo de lo que parece:

- Variables `CORE_INSTITUTE_NAME`, `CORE_ENABLED_MODULES`, `CORE_URL_*`,
  `SITE_URL`, `STATIC_SITE_CNAME`.
- Conmutación SQLite / PostgreSQL y tres routers de base de datos.
- `Dockerfile` y `docker-compose.yml`.
- UUID en las entidades semánticas.
- Separación en `research_app`, `ontologizar_app`, `corpus_app`, `logs_app`,
  `cms_app` (+ `airam_app`).
- Comandos de importación y semillas.

Por tanto **no se parte de una arquitectura nueva**: se formaliza la existente.

## Problemas concretos a corregir primero

### 1. Secretos y valores institucionales en Compose

Hoy aparecen directamente en `docker-compose.yml`:

```yaml
POSTGRES_PASSWORD: core
SECRET_KEY: change-me-in-docker
CORE_INSTITUTE_NAME: CORE Radio Micelio
```

El Compose reutilizable debería **consumirlos** desde el entorno:

```yaml
env_file:
  - .env

environment:
  SECRET_KEY: ${SECRET_KEY:?SECRET_KEY is required}
  CORE_INSTITUTE_NAME: ${CORE_INSTITUTE_NAME:-CORE}
```

Docker Compose soporta expresamente variables, interpolación y archivos `.env`
para construir configuraciones reutilizables entre entornos.

### 2. `seed_demo` se ejecuta en cada arranque

El `CMD` del `Dockerfile` mezcla hoy tres operaciones distintas en el arranque:

```bash
migrate
migrate --database=research_db
migrate --database=ontologizar_db
seed_demo            # <- carga datos de demostración SIEMPRE
gunicorn ...
```

Aunque `seed_demo` sea idempotente, **una institución no debería cargar datos
demo automáticamente al reiniciar producción**. Se separan responsabilidades:

```text
arrancar aplicación     ≠   actualizar estructura   ≠   cargar contenido
```

Propuesta de flujo explícito:

```bash
docker compose up -d
docker compose run --rm web python manage.py migrate_all
docker compose run --rm web python manage.py bootstrap_instance
```

Y la semilla demo queda **voluntaria**:

```bash
docker compose run --rm web python manage.py seed_demo
```

### 3. PostgreSQL espera tres bases, pero Compose declara una

Django espera:

```text
core_default
core_research
core_ontologizar
```

Mientras que el contenedor de PostgreSQL solo recibe `POSTGRES_DB: core_default`
y **solo crea esa base inicial**. Hay que elegir explícitamente:

**Opción A — recomendada inicialmente.** Una sola base PostgreSQL y separación
por apps/modelos:

```text
core
```

Más fácil de desplegar, respaldar y replicar. Los routers actuales aportan
complejidad operativa sin equivaler a modularidad funcional.

**Opción B.** Mantener tres bases y añadir un script de inicialización:

```text
/docker-entrypoint-initdb.d/01-create-databases.sql
```

Para un CORE genérico: **una base por instancia**, salvo necesidad real de
aislar research y ontología a nivel físico.

### 4. Bases SQLite versionadas

El repositorio contiene:

```text
db_default.sqlite3
db_research.sqlite3
db_ontologizar.sqlite3
db_knowledge.sqlite3
```

Esto difumina la separación entre **esquema reproducible**, **datos de
demostración** y **contenido real de Radio Micelio**. Deberían sustituirse
progresivamente por:

```text
migraciones          (estructura, igual para todos)
fixtures pequeños    (mínimos reproducibles)
paquetes de datos exportables
importadores
```

Los datos persistentes deben vivir **fuera de la imagen**, en volúmenes o
servicios de almacenamiento (recomendación oficial de Docker).

## Hito R1 — CORE como instancia reproducible

### Entregables

```text
.env.example
compose.yaml
compose.override.yaml
scripts/entrypoint.sh
scripts/bootstrap-instance.sh
core_micelio/config.py
docs/INSTANCE_CONTRACT.md          (este contrato, ya presente)
manage.py check --deploy documentado
tests/test_instance_configuration.py
```

### Prueba de aceptación

```bash
git clone ...
cp .env.example .env
docker compose up -d
docker compose exec web python manage.py bootstrap_instance
docker compose exec web python manage.py check --deploy
```

Después de eso debe cumplirse:

- la web responde;
- no contiene datos demo salvo petición expresa;
- la institución tiene su nombre y namespace propios;
- los módulos pueden activarse o desactivarse;
- reiniciar **no** modifica contenido;
- borrar los contenedores conservando los volúmenes **no** pierde datos;
- una instalación limpia puede reconstruirse con migraciones e importadores.

Django recomienda tratar por entorno los secretos, hosts, almacenamiento,
seguridad, caché y configuración de producción, y verificar el despliegue con su
*deployment checklist*.

## Capa semántica (después de R1)

Fijado el contrato, se entra en la ontología. El modelo actual tiene buena base:

```text
Subject
Dictionary
Taxonomy
Concept
ConceptRelation
AttributedRelation
```

Señal de que aún mezcla **motor universal** con **vocabulario concreto**:
`RELATION_TYPES` contiene tanto relaciones generales:

```text
broader
narrower
part_of
defined_in
interpreted_as
```

como relaciones específicas de una obra o dominio:

```text
escudero_de
monta_a
ama_a
ataca_a
```

Evolución correcta:

```text
RelationType como dato (no como código)
RelationScheme / SemanticProfile
relaciones básicas instaladas por CORE
relaciones específicas importadas por cada asignatura/institución
```

Así, `escudero_de` no formaría parte del código universal: pertenecería al
paquete semántico de `ontoNarrativa` u `ontoQuijote`.

Para taxonomías y vocabularios controlados, **SKOS** aporta un modelo compartido
de `ConceptScheme`, conceptos, etiquetas y relaciones (`broader`, `narrower`,
`related`). No obliga a que todo CORE sea RDF internamente, pero ofrece un buen
contrato de interoperabilidad para el JSON-LD que ya produce el sistema.

## Secuencia completa (decisión propuesta)

No se elige entre "Docker" y "ontología": se encadenan.

```text
R1. Convertir CORE_RadioMicelio en una instancia reproducible
R2. Extraer relaciones y vocabularios específicos fuera del código
R3. Definir paquetes institucionales (configuración + datos + semántica)
R4. Probar una segunda instancia ficticia
```

La prueba definitiva no es volver a levantar Radio Micelio, sino levantar, con
**el mismo repositorio**:

```text
CORE Radio Micelio
CORE Instituto Cajal Demo
CORE Cooperativa Cultural Demo
```

Cada uno con nombre, módulos, datos y vocabularios distintos, **sin cambiar una
línea del código base**. Ahí CORE deja de ser un portfolio o la app de Radio
Micelio y pasa a ser una **infraestructura soberana y extensible** para
organizar investigación, conocimiento y actividad institucional.

## Referencias

- The Twelve-Factor App — *Config*, *Backing services*, *Dev/prod parity*.
- Docker Compose — variables, interpolación y `.env`.
- Docker — volúmenes para datos persistentes.
- Django — *Deployment checklist* / `manage.py check --deploy`.
- W3C SKOS — vocabularios controlados e interoperabilidad JSON-LD.
