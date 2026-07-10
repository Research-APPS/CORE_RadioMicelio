



Te propongo este documento como contexto de diseño para que Claude implemente el dominio en **CORE_RadioMicelio**, alineado con AIRAM, CHORDIA, Ontologías y la biblioteca pública.

:::writing{variant="document" id="58142"}
# #ontoArquetipos — Integración transmedia en CORE_RadioMicelio

## Objetivo

Incorporar un nuevo dominio ontológico denominado **#ontoArquetipos** dentro de CORE_RadioMicelio y AIRAM.

El objetivo no es clasificar personajes mediante etiquetas rígidas, sino permitir el estudio y la navegación entre:

- Mitología
- Arquetipos
- Dramaturgia
- Símbolos
- Funciones expresivas
- Recursos musicales

para construir una infraestructura útil para:

- Humanidades Digitales
- Dramaturgia
- Música
- Narrativa transmedia
- Docencia
- GEO/LLM

---

# Principios de diseño

## No modelar personajes, modelar patrones

La pregunta principal no es:

> ¿Es Sísmico un Segismundo?

Sino:

> ¿Qué patrones arquetípicos presentes en Segismundo pueden reutilizarse para construir a Sísmico?

Los personajes son combinaciones de patrones.

Ejemplo:

Segismundo

- Héroe
- Prisionero
- Hijo rechazado
- Rey legítimo
- Sombra potencial
- Renacido
- Buscador de identidad

Sísmico

- Trickster
- Marginado
- Viajero
- Héroe involuntario
- Rebelde
- Renacido

La ontología debe permitir visualizar coincidencias, diferencias y genealogías narrativas.

---

# Jerarquía conceptual

Se propone la siguiente estructura:

```text
#ontoMitologiaGriega
        ↓ expresses

#ontoArquetipos
        ↓ appears_in

#ontoDramaturgia
        ↓ evokes

#ontoMusica
```

---

## Nivel 1 — Mitología

Entidades concretas.

Ejemplos:

- Zeus
- Atenea
- Hermes
- Apolo
- Artemisa
- Dioniso
- Hades
- Perséfone
- Prometeo
- Atlas

No son arquetipos.

Son figuras mitológicas.

---

### Relaciones

```yaml
Atenea:

instance_of:
  - Deidad

expresses:
  - Mentora
  - Viejo Sabio

symbols:
  - búho
  - olivo
  - lanza

domains:
  - estrategia
  - conocimiento
```

```yaml
Hermes:

instance_of:
  - Deidad

expresses:
  - Trickster
  - Mensajero

symbols:
  - sandalias aladas
  - caminos
  - comercio
```

```yaml
Dioniso:

instance_of:
  - Deidad

expresses:
  - Transformador
  - Renacimiento
  - Caos creativo

symbols:
  - vino
  - máscara
  - teatro
```

---

# Nivel 2 — Arquetipos

Inspirados principalmente en:

- Jung
- Campbell
- Vogler
- Tradición dramatúrgica

Ejemplos:

- Héroe
- Trickster
- Mentor
- Sombra
- Rey
- Madre
- Renacido
- Exiliado
- Mártir
- Guardián del Umbral
- Buscador
- Shapeshifter

---

### Modelo propuesto

```yaml
name: Trickster

symbols:
  - camino
  - máscara
  - frontera

themes:
  - cambio
  - engaño
  - transformación

functions:
  - romper reglas
  - alterar el orden
  - revelar verdades ocultas
```

---

# Nivel 3 — Dramaturgia

Personajes concretos.

Ejemplos:

- Segismundo
- Hamlet
- Don Quijote
- Vaquero Atómico
- Sísmico
- Marza

---

### Ejemplo

```yaml
name: Segismundo

archetypes:
  - Heroe
  - Prisionero
  - Rey
  - Renacido

dramatic_functions:
  - Transformacion
  - Revelacion
  - Redencion

symbols:
  - Torre
  - Cadena
  - Sueño
  - Libertad

themes:
  - Identidad
  - Destino
  - Libre albedrio
```

---

### Ejemplo Radio Micelio

```yaml
name: Sismico

archetypes:
  - Trickster
  - Heroe
  - Renacido

mythological_echoes:
  - Hermes
  - Prometeo

symbols:
  - terremoto
  - portal
  - viaje

themes:
  - libertad
  - identidad
  - transformación
```

---

# Nivel 4 — Símbolos

Los símbolos deben ser nodos propios.

Ejemplos:

- Torre
- Cadena
- Portal
- Máscara
- Desierto
- Camino
- Cueva
- Estrella
- Laberinto

Permiten conectar:

Mitología ↔ Arquetipos ↔ Personajes ↔ Música

---

# Nivel 5 — Música

No se pretende afirmar relaciones universales.

El sistema debe documentar asociaciones culturales y dramatúrgicas frecuentes.

---

## Modelo recomendado

```yaml
resource:
  id: modal_interchange

musical_domain:
  harmony

evokes:
  - sorpresa
  - ambigüedad
  - transformación

commonly_associated_with:
  - Trickster
  - Shapeshifter
```

Importante:

NO:

```text
Intercambio modal = Trickster
```

SÍ:

```text
Intercambio modal
→ puede utilizarse para apoyar escenas
→ relacionadas con Trickster
```

---

# Relación con CHORDIA

No fusionar sistemas.

Mantener separación:

## CHORDIA

Transformaciones musicales.

Ejemplos:

- Intercambio modal
- Drop 2
- Pedal point
- Reducción
- Aumento
- SATB
- Big Band

---

## #ontoArquetipos

Contexto semántico y dramatúrgico.

---

### Extensión opcional para recursos

Añadir metadatos:

```yaml
resource:
  id: pedal_point

dramatic_uses:
  - tensión
  - espera
  - obsesión

related_archetypes:
  - Sombra
  - Guardian del Umbral

related_symbols:
  - cueva
  - vigilancia
  - amenaza
```

---

# Capa intermedia: Función Expresiva

Se propone una ontología específica.

```text
Recurso Musical
        ↓

Función Expresiva
        ↓

Arquetipo
```

Ejemplos:

```text
Tritono
↓
Inestabilidad
↓
Sombra
```

```text
Pedal Point
↓
Persistencia
↓
Destino
```

```text
Intercambio Modal
↓
Transformación
↓
Shapeshifter
```

---

# Navegación AIRAM

Ejemplos de recorridos:

## Ruta mitológica

```text
Hermes
↓
Trickster
↓
Sísmico
↓
Mixolidio
↓
Blues Rock
```

---

## Ruta dramatúrgica

```text
Segismundo
↓
Renacido
↓
Perséfone
↓
Muerte y retorno
↓
Recursos musicales asociados
```

---

## Ruta compositiva

```text
Transformación
↓
Shapeshifter
↓
Intercambio modal
↓
Cambio tímbrico
```

---

# Compatibilidad con Biblioteca AIRAM

Nueva asignatura:

```text
Humanidades Digitales
└── Arquetipos
```

Subdominios:

```text
#ontoArquetipos
#ontoMitologiaGriega
#ontoDramaturgia
#ontoSimbolos
#ontoExpresividad
```

Todos reutilizando:

- Subject
- Dictionary
- Taxonomy
- Article
- JSON-LD
- Relaciones AIRAM

---

# Relaciones ontológicas mínimas

Añadir verbalizadores para:

```text
expresses
echoes
appears_in
symbolizes
evokes
associated_with
supports
dramatically_used_for
```

---

# Objetivo final

Construir una ontología transmedia capaz de conectar:

Mitología
↓
Arquetipos
↓
Personajes
↓
Narrativas
↓
Símbolos
↓
Funciones expresivas
↓
Recursos musicales

permitiendo a AIRAM navegar y explicar las relaciones desde una perspectiva docente, dramatúrgica y musical, sin afirmar equivalencias universales y manteniendo siempre la trazabilidad cultural e histórica de cada asociación.
:::

Además, para CORE_RadioMicelio yo añadiría una tarea extra: crear una **semilla inicial de 20–30 arquetipos, 20 símbolos, 15 figuras mitológicas griegas y 10 personajes dramatúrgicos canónicos** (Segismundo, Hamlet, Don Quijote, Edipo, Antígona, etc.) para que AIRAM tenga ya una red navegable desde el primer despliegue.