import re

from django.db import models

from ontologizar_app.models import Concept, Dictionary

_ARTICULOS_INICIALES = re.compile(r"^(el|la|los|las|un|una)\s+", re.IGNORECASE)


def normalizar_texto(texto):
    """"don Quijote" / "Don Quijote" / "el hidalgo don Quijote" -> comparables entre sí."""
    t = texto.strip().lower()
    t = _ARTICULOS_INICIALES.sub("", t)
    return t


def buscar_concept_por_texto(dictionary, texto):
    """Intenta encontrar un Concept ya curado (dentro de `dictionary`) cuyo label
    coincida con `texto`, primero exacto (case-insensitive) y si no por forma normalizada."""
    match = Concept.objects.filter(dictionary=dictionary, label__iexact=texto).first()
    if match:
        return match
    objetivo = normalizar_texto(texto)
    for c in Concept.objects.filter(dictionary=dictionary):
        if normalizar_texto(c.label) == objetivo:
            return c
    return None


class Capitulo(models.Model):
    PARTE_CHOICES = [("I", "Primera parte"), ("II", "Segunda parte")]

    dictionary = models.ForeignKey(Dictionary, on_delete=models.CASCADE, related_name="capitulos")
    parte = models.CharField(max_length=3, choices=PARTE_CHOICES)
    numero = models.PositiveIntegerField()
    numeral = models.CharField(max_length=20)
    titulo = models.CharField(max_length=500, blank=True)
    orden = models.PositiveIntegerField()

    class Meta:
        ordering = ["orden"]
        constraints = [
            models.UniqueConstraint(fields=["dictionary", "parte", "numero"], name="unique_capitulo"),
        ]

    def __str__(self):
        return f"[{self.parte}] Capítulo {self.numeral} — {self.titulo[:60]}"


class Parrafo(models.Model):
    LABEL_CHOICES = [
        ("W", "Worldbuilding"),
        ("P", "Personaje"),
        ("N", "Narración"),
        ("D", "Diálogo"),
        ("S", "Simbolismo"),
        ("Q", "Pregunta abierta"),
    ]

    # Valores de airam.temporal.OrientacionTemporal (paquete externo /2026/AIRAM) — 13 en total.
    ORIENTACION_CHOICES = [
        ("pasado_narrativo", "Pasado narrativo"),
        ("pasado_recordado", "Pasado recordado"),
        ("pasado_anterior", "Pasado anterior"),
        ("presente_actual", "Presente actual"),
        ("presente_historico", "Presente histórico"),
        ("futuro_previsto", "Futuro previsto"),
        ("futuro_hipotetico", "Futuro hipotético"),
        ("futuro_mitico", "Futuro mítico"),
        ("habitual", "Habitual"),
        ("simultaneidad", "Simultaneidad"),
        ("posterioridad", "Posterioridad"),
        ("atemporalidad", "Atemporalidad"),
        ("incertidumbre", "Incertidumbre"),
    ]

    capitulo = models.ForeignKey(Capitulo, on_delete=models.CASCADE, related_name="parrafos")
    orden = models.PositiveIntegerField()
    texto = models.TextField()
    label = models.CharField(max_length=1, choices=LABEL_CHOICES, blank=True)
    temporalidad = models.CharField(max_length=50, choices=ORIENTACION_CHOICES, blank=True)
    subtype = models.CharField(max_length=50, blank=True)
    notas = models.TextField(blank=True)

    class Meta:
        ordering = ["capitulo", "orden"]
        constraints = [
            models.UniqueConstraint(fields=["capitulo", "orden"], name="unique_parrafo_orden"),
        ]

    def __str__(self):
        return f"[{self.capitulo.numeral}:{self.orden}] {self.texto[:60]}"


class Mencion(models.Model):
    """Ancla un Concept (ontologizar_app) a un párrafo concreto — bridge entre la
    capa textual (corpus_app) y la capa de conceptos/grafo (ontologizar_app)."""

    parrafo = models.ForeignKey(Parrafo, on_delete=models.CASCADE, related_name="menciones")
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name="menciones")
    texto_superficie = models.CharField(max_length=200, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["parrafo", "concept"], name="unique_mencion"),
        ]

    def __str__(self):
        return f"{self.concept.label} @ {self.parrafo}"


class MencionSugerida(models.Model):
    """Candidato a Mencion propuesto por AIRAM o un LLM, pendiente de curación humana.
    AIRAM/LLM sugiere, el admin confirma, el grafo (ontologizar_app) conserva."""

    FUENTE_CHOICES = [
        ("ner", "NER"),
        ("noun_chunk", "Frase nominal"),
        ("entidad_oscura", "Entidad oscura"),
        ("patron", "Patrón léxico"),
        ("llm", "LLM"),
    ]

    parrafo = models.ForeignKey(Parrafo, on_delete=models.CASCADE, related_name="menciones_sugeridas")
    texto_superficie = models.CharField(max_length=200)
    normalizado = models.CharField(max_length=220, db_index=True, blank=True)
    tipo_sugerido = models.CharField(max_length=50, blank=True)
    concept_sugerido = models.ForeignKey(
        Concept, null=True, blank=True, on_delete=models.SET_NULL, related_name="sugerencias"
    )
    confianza = models.FloatField(null=True, blank=True)
    fuente = models.CharField(max_length=20, choices=FUENTE_CHOICES, blank=True)
    aceptada = models.BooleanField(null=True, blank=True)

    class Meta:
        ordering = ["-confianza"]
        constraints = [
            models.UniqueConstraint(
                fields=["parrafo", "texto_superficie", "fuente"], name="unique_mencion_sugerida"
            ),
        ]

    def __str__(self):
        return f"{self.texto_superficie} @ {self.parrafo} ({self.tipo_sugerido})"

    def save(self, *args, **kwargs):
        self.normalizado = normalizar_texto(self.texto_superficie)
        super().save(*args, **kwargs)


class RelacionSugerida(models.Model):
    """Candidato a ConceptRelation (ontologizar_app) propuesto por un LLM, pendiente de
    curación. relation_type_normalizado se valida contra RELATION_TYPES (semantic_relations.py)
    pero NO es una FK — ConceptRelation.relation_type tampoco lo es."""

    parrafo = models.ForeignKey(Parrafo, on_delete=models.CASCADE, related_name="relaciones_sugeridas")
    origen_texto = models.CharField(max_length=200)
    relation_type = models.CharField(max_length=80)  # texto libre de la fuente, ej. "monta_a"
    destino_texto = models.CharField(max_length=200)
    evidencia = models.TextField(blank=True)
    confianza = models.FloatField(null=True, blank=True)
    fuente = models.CharField(max_length=20, default="llm")
    origen_concept = models.ForeignKey(
        Concept, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    destino_concept = models.ForeignKey(
        Concept, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    relation_type_normalizado = models.CharField(max_length=32, blank=True)
    aceptada = models.BooleanField(null=True, blank=True)

    class Meta:
        ordering = ["-confianza"]
        constraints = [
            models.UniqueConstraint(
                fields=["parrafo", "origen_texto", "relation_type", "destino_texto", "fuente"],
                name="unique_relacion_sugerida",
            ),
        ]

    def __str__(self):
        return f"{self.origen_texto} — {self.relation_type} — {self.destino_texto} @ {self.parrafo}"


class LabelSugerida(models.Model):
    """Candidato a Parrafo.label propuesto por un LLM, pendiente de curación."""

    parrafo = models.ForeignKey(Parrafo, on_delete=models.CASCADE, related_name="labels_sugeridas")
    label = models.CharField(max_length=1, choices=Parrafo.LABEL_CHOICES)
    razon = models.TextField(blank=True)
    confianza = models.FloatField(null=True, blank=True)
    fuente = models.CharField(max_length=20, default="llm")
    aceptada = models.BooleanField(null=True, blank=True)

    class Meta:
        ordering = ["-confianza"]
        constraints = [
            models.UniqueConstraint(fields=["parrafo", "fuente"], name="unique_label_sugerida"),
        ]

    def __str__(self):
        return f"{self.parrafo} -> {self.label} ({self.fuente})"


class TemporalidadSugerida(models.Model):
    """Candidato a Parrafo.temporalidad propuesto por airam.temporal.analizar_temporalidad,
    pendiente de curación. Dimensión distinta de `label`: no es "qué función narrativa cumple
    el párrafo" sino "desde qué orientación temporal está contado"."""

    parrafo = models.ForeignKey(Parrafo, on_delete=models.CASCADE, related_name="temporalidades_sugeridas")
    fuente = models.CharField(max_length=30, default="airam")
    orientacion = models.CharField(max_length=50, choices=Parrafo.ORIENTACION_CHOICES)
    confianza = models.FloatField(null=True, blank=True)
    marcador = models.TextField(blank=True)
    aceptada = models.BooleanField(null=True, blank=True)
    notas = models.TextField(blank=True)

    class Meta:
        ordering = ["-confianza"]
        constraints = [
            models.UniqueConstraint(
                fields=["parrafo", "fuente", "orientacion", "marcador"],
                name="unique_temporalidad_sugerida",
            ),
        ]

    def __str__(self):
        return f"{self.parrafo} -> {self.orientacion} ({self.fuente})"
