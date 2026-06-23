from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from leximus_app.models import ProjectTaxonomyLink, Taxonomy, TaxonomyNode

admin.site.register(Taxonomy)
admin.site.register(TaxonomyNode, MPTTModelAdmin)
admin.site.register(ProjectTaxonomyLink)
