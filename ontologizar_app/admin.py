from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from ontologizar_app.models import (
    AttributedRelation, Concept, ConceptDefinition, ConceptProperty, ConceptRelation,
    Dictionary, Subject, SubjectMaterial, SubjectTaxonomy, Taxonomy, TaxonomyNode,
)

admin.site.register(Subject)
admin.site.register(SubjectMaterial)
admin.site.register(Dictionary)
admin.site.register(Taxonomy)
admin.site.register(SubjectTaxonomy)


@admin.register(Concept)
class ConceptAdmin(admin.ModelAdmin):
    # search_fields es necesario para que corpus_app pueda usar
    # autocomplete_fields hacia Concept desde sus admins de curación.
    list_display = ("label", "dictionary")
    list_filter = ("dictionary",)
    search_fields = ("label",)


admin.site.register(TaxonomyNode, MPTTModelAdmin)
admin.site.register(ConceptDefinition)
admin.site.register(ConceptProperty)
admin.site.register(ConceptRelation)


@admin.register(AttributedRelation)
class AttributedRelationAdmin(admin.ModelAdmin):
    list_display = ("relation", "authority_layer", "framework", "asserted_by", "confidence")
    list_filter = ("authority_layer", "framework", "confidence")
    search_fields = ("asserted_by", "source_work", "framework")
