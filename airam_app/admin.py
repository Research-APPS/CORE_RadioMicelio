from django.contrib import admin

from airam_app.models import AiramConceptWeight, AiramSession

admin.site.register(AiramSession)
admin.site.register(AiramConceptWeight)
