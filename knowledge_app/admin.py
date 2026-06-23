from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from knowledge_app.models import (
    Concept, ConceptDefinition, ConceptProperty, ConceptRelation,
    Dictionary, Subject, SubjectMaterial, Taxonomy, TaxonomyNode,
)

admin.site.register(Subject)
admin.site.register(SubjectMaterial)
admin.site.register(Dictionary)
admin.site.register(Taxonomy)
admin.site.register(Concept)
admin.site.register(TaxonomyNode, MPTTModelAdmin)
admin.site.register(ConceptDefinition)
admin.site.register(ConceptProperty)
admin.site.register(ConceptRelation)
