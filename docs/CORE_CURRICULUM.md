# CORE Radio Micelio — currículo escolar

## Enfoque

CORE Radio Micelio modela un **colegio** con:

- **Asignaturas** — dominios estables de conocimiento (biblioteca)
- **Proyectos de fin de curso (PFC)** — cuadernos transversales que marcan conceptos y producen resultados

No hay nombres de proyectos de investigación universitaria en el seed por defecto.

## Metáfora

```text
Asignaturas  = biblioteca
CMS          = libro (SubjectMaterial)
Marcadores   = subrayar una ficha para tu cuaderno PFC
Resultado    = entrega final del proyecto
```

## Seed de ejemplo

**Asignaturas:** Música, Ciencias Naturales, Micología (#ontoHongo), Historia, Geografía, Lengua y Literatura

**Proyectos PFC:**
- Emociones en un poema (Lengua + Música)
- El bosque y sus sonidos (Ciencias + Música)
- Mi pueblo en el mapa (Geografía + Historia)

```bash
python manage.py seed_curriculum
```
