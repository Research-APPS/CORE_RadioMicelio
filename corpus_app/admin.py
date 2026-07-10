from django.contrib import admin

from ontologizar_app.models import ConceptRelation

from .models import (
    Capitulo,
    LabelSugerida,
    Mencion,
    MencionSugerida,
    Parrafo,
    RelacionSugerida,
    TemporalidadSugerida,
)


@admin.register(Capitulo)
class CapituloAdmin(admin.ModelAdmin):
    list_display = ("dictionary", "parte", "numero", "numeral", "titulo")
    list_filter = ("dictionary", "parte")
    search_fields = ("titulo", "numeral")
    ordering = ("orden",)


@admin.register(Parrafo)
class ParrafoAdmin(admin.ModelAdmin):
    list_display = ("capitulo", "orden", "texto_corto", "label", "temporalidad")
    list_filter = ("label", "temporalidad", "capitulo__parte")
    search_fields = ("texto",)
    list_editable = ("label", "temporalidad")
    list_select_related = ("capitulo",)
    autocomplete_fields = ("capitulo",)

    @admin.display(description="Texto")
    def texto_corto(self, obj):
        return obj.texto[:100]


@admin.register(Mencion)
class MencionAdmin(admin.ModelAdmin):
    list_display = ("concept", "parrafo", "texto_superficie")
    list_filter = ("concept__dictionary",)
    autocomplete_fields = ("parrafo", "concept")
    search_fields = ("texto_superficie",)


@admin.register(MencionSugerida)
class MencionSugeridaAdmin(admin.ModelAdmin):
    list_display = ("ver_parrafo", "texto_superficie", "tipo_sugerido", "fuente", "confianza", "concept_sugerido", "aceptada")
    list_display_links = ("ver_parrafo",)
    list_editable = ("concept_sugerido", "aceptada")
    list_filter = ("aceptada", "fuente", "tipo_sugerido", "parrafo__capitulo__parte")
    search_fields = ("texto_superficie",)
    autocomplete_fields = ("parrafo", "concept_sugerido")
    actions = ["promover_a_mencion"]

    @admin.display(description="Párrafo")
    def ver_parrafo(self, obj):
        return str(obj.parrafo)

    @admin.action(description="Promover seleccionadas a Mención real")
    def promover_a_mencion(self, request, queryset):
        promovidas, sin_concept = 0, 0
        for s in queryset.select_related("parrafo", "concept_sugerido"):
            if not s.concept_sugerido:
                sin_concept += 1
                continue
            Mencion.objects.get_or_create(
                parrafo=s.parrafo, concept=s.concept_sugerido,
                defaults={"texto_superficie": s.texto_superficie},
            )
            s.aceptada = True
            s.save(update_fields=["aceptada"])
            promovidas += 1
        self.message_user(
            request,
            f"{promovidas} promovidas a Mención. {sin_concept} omitidas (sin concept asignado).",
        )


@admin.register(RelacionSugerida)
class RelacionSugeridaAdmin(admin.ModelAdmin):
    list_display = (
        "ver_parrafo", "origen_texto", "relation_type", "destino_texto", "confianza",
        "origen_concept", "relation_type_normalizado", "destino_concept", "aceptada",
    )
    list_display_links = ("ver_parrafo",)
    list_editable = ("origen_concept", "destino_concept", "aceptada")
    list_filter = ("aceptada", "fuente", "parrafo__capitulo__parte")
    search_fields = ("origen_texto", "destino_texto", "relation_type")
    autocomplete_fields = ("parrafo", "origen_concept", "destino_concept")
    actions = ["promover_a_relacion"]

    @admin.display(description="Párrafo")
    def ver_parrafo(self, obj):
        return str(obj.parrafo)

    @admin.action(description="Promover seleccionadas a ConceptRelation real")
    def promover_a_relacion(self, request, queryset):
        promovidas, incompletas = 0, 0
        for s in queryset.select_related("origen_concept", "destino_concept"):
            if not (s.origen_concept and s.destino_concept and s.relation_type_normalizado):
                incompletas += 1
                continue
            ConceptRelation.objects.get_or_create(
                source=s.origen_concept, target=s.destino_concept,
                relation_type=s.relation_type_normalizado,
            )
            s.aceptada = True
            s.save(update_fields=["aceptada"])
            promovidas += 1
        self.message_user(
            request,
            f"{promovidas} promovidas a ConceptRelation. {incompletas} omitidas "
            "(falta origen/destino/tipo de relación por asignar).",
        )


@admin.register(LabelSugerida)
class LabelSugeridaAdmin(admin.ModelAdmin):
    list_display = ("ver_parrafo", "label", "confianza", "fuente", "aceptada")
    list_display_links = ("ver_parrafo",)
    list_editable = ("aceptada",)
    list_filter = ("aceptada", "label", "fuente", "parrafo__capitulo__parte")
    autocomplete_fields = ("parrafo",)
    actions = ["promover_a_label"]

    @admin.display(description="Párrafo")
    def ver_parrafo(self, obj):
        return str(obj.parrafo)[:100]

    @admin.action(description="Promover seleccionadas a clasificación real del párrafo")
    def promover_a_label(self, request, queryset):
        promovidas, ya_clasificados = 0, 0
        for s in queryset.select_related("parrafo"):
            if s.parrafo.label:
                ya_clasificados += 1
                continue
            s.parrafo.label = s.label
            if s.razon:
                s.parrafo.notas = s.razon
            s.parrafo.save(update_fields=["label", "notas"])
            s.aceptada = True
            s.save(update_fields=["aceptada"])
            promovidas += 1
        self.message_user(
            request,
            f"{promovidas} promovidas a Parrafo.label. {ya_clasificados} omitidas "
            "(el párrafo ya tenía una clasificación manual).",
        )


@admin.register(TemporalidadSugerida)
class TemporalidadSugeridaAdmin(admin.ModelAdmin):
    list_display = ("ver_parrafo", "orientacion", "confianza", "marcador_corto", "fuente", "aceptada")
    list_display_links = ("ver_parrafo",)
    list_editable = ("aceptada",)
    list_filter = ("aceptada", "orientacion", "fuente", "parrafo__capitulo__parte")
    autocomplete_fields = ("parrafo",)
    actions = ["promover_a_temporalidad"]

    @admin.display(description="Párrafo")
    def ver_parrafo(self, obj):
        return str(obj.parrafo)[:100]

    @admin.display(description="Marcador")
    def marcador_corto(self, obj):
        return obj.marcador[:60]

    @admin.action(description="Promover seleccionadas a Parrafo.temporalidad")
    def promover_a_temporalidad(self, request, queryset):
        promovidas, ya_clasificados = 0, 0
        for s in queryset.select_related("parrafo"):
            if s.parrafo.temporalidad:
                ya_clasificados += 1
                continue
            s.parrafo.temporalidad = s.orientacion
            s.parrafo.save(update_fields=["temporalidad"])
            s.aceptada = True
            s.save(update_fields=["aceptada"])
            promovidas += 1
        self.message_user(
            request,
            f"{promovidas} promovidas a Parrafo.temporalidad. {ya_clasificados} omitidas "
            "(el párrafo ya tenía una temporalidad curada).",
        )
