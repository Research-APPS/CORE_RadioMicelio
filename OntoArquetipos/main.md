# Infraestructura ontológica para estudiar narrativas

## Objetivo

CORE_RadioMicelio documenta **narrativas** — no es una ontología de arquetipos ni un repositorio del universo creativo de Radio Micelio.

El MVP es **#ontoNarrativa**: vocabulario universal de entidades, relaciones y eventos narrativos, visible en `/biblioteca` como asignatura **Narrativa**.

Visión a largo plazo: infraestructura tipo Wikidata para narrativas y modelos interpretativos, reutilizando AIRAM (`Subject`, `Dictionary`, `Concept`, `ConceptRelation`, JSON-LD, verbalizadores).

---

## Principios

### Tres capas

```text
Capa 0 — Documental     Obra, Personaje, Evento, Lugar, Objeto, relaciones fácticas
Capa 1 — Perspectivas   Marcos analíticos (forma abierta; no predecida)
Capa 2 — Interpretativa AttributedRelation con fuente, framework, asserted_by
```

### Neutralidad de medio

Sirve para novela, teatro, mitología, cine, cómic, videojuego, relato oral. El **medio** es propiedad de la obra (`medium=novela|teatro|cine|…`), no un tipo de entidad.

### Simplicidad documental

No crear tipos nuevos si basta una propiedad o relación. Toda entidad nueva debe justificar navegación que las estructuras existentes no permiten.

### Fuera de alcance (núcleo documental)

- Personajes propios de Radio Micelio (Sísmico, Vaquero Atómico…)
- CHORDIA y asociaciones musicales dramatúrgicas
- Listas populares de «12 arquetipos» como canon
- Relaciones sin fuente publicada

---

## Biblioteca

| Elemento | Valor |
|---|---|
| Subject | `narrativa` / **Narrativa** |
| URL | `/biblioteca/asignaturas/narrativa/` |
| Dictionary | `ontonarrativa` (#ontoNarrativa) |
| Taxonomy | `narrativa` |

**Nombre reservado:** puede evolucionar a «Estudios Narrativos» si el alcance académico lo justifica; el slug `narrativa` se mantiene por estabilidad de URLs.

```text
Narrativa (Subject)
├── ontonarrativa     ← meta-vocabulario (tipos, funciones) — MVP
├── quijote           ← corpus piloto (bajo lengua, puente documentado)
└── estudios          ← interpretaciones (AttributedRelation)
```

### Meta vs instancia

- `ontonarrativa` contiene **solo tipos** (Personaje, Evento, Obra…) y **funciones narrativas** (Encierro, Traición…)
- Instancias (Don Quijote, Sancho…) viven en diccionarios por obra (`quijote`, etc.)
- Puente: `ConceptProperty concept_type`

---

## Infraestructura (Fase 1)

### ConceptDefinition — kinds ampliados

- `definition_primary`, `definition_institutional`, `definition_scholarly`

### Citas — SourceKind ampliados

- `fuente_primaria`, `fuente_institucional`, `obra_literaria`, `estudio_academico`
- Formato: `label | url | kind | authority | authority_level | locator`

### AttributedRelation

Metadatos de procedencia para `ConceptRelation`:

- `authority_layer`: `factual` | `interpretive`
- `framework`, `asserted_by`, `source_work`, `locator`, `confidence`, `scope`

### Relaciones #ontoNarrativa

Documentales: `contiene`, `padre_de`, `hijo_de`, `enemigo_de`, `amigo_de`, `sirve_a`, `traiciona_a`, `participa_en`, `ocurre_en`, `posee`, `viaja_a`, `criado_por`, `enamorado_de`

Interpretativas: `interpreted_as`, `defined_in`, `develops`, `reinterprets`, `criticizes`, `distinct_from`

---

## Comandos

```bash
conda activate RM

# Migraciones (ontologizar_app vive en ontologizar_db, no en default)
python manage.py migrate --database=ontologizar_db

python manage.py seed_narrativa_ontologia   # asignatura + meta-vocabulario
python manage.py seed_quijote_ontologia      # esqueleto Quijote (si no existe)
python manage.py align_quijote_narrativa     # corpus piloto + interpretación demo
```

---

## Secuencia post-MVP

```text
#ontoNarrativa (MVP)
    ↓
Más corpus (teatro, cine, mitología…)
    ↓
Interpretaciones documentadas (AttributedRelation + framework)
    ↓
Marcos analíticos con vocabulario — solo si casos de uso lo exigen
    ↓
Estudios transversales como colecciones/proyectos
```

Jung, Campbell, Propp son **candidatos**, no compromisos de diseño.
