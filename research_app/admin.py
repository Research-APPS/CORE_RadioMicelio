from django.contrib import admin
from research_app.models import (
    LearningMarker, ProjectCurriculumDeclaration, ProyectoInvestigacion,
    ScientificActivity, ScientificResult,
)

admin.site.register(ProyectoInvestigacion)
admin.site.register(ProjectCurriculumDeclaration)
admin.site.register(LearningMarker)
admin.site.register(ScientificActivity)
admin.site.register(ScientificResult)
