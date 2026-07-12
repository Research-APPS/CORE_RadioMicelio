from django.contrib import admin
from research_app.models import (
    LearningMarker, ProjectCurriculumDeclaration, ProyectoInvestigacion,
    ActivityCapability, ActivityNotebook, ScientificActivity, ScientificResult,
)

admin.site.register(ProyectoInvestigacion)
admin.site.register(ProjectCurriculumDeclaration)
admin.site.register(LearningMarker)
admin.site.register(ScientificActivity)
admin.site.register(ActivityNotebook)
admin.site.register(ActivityCapability)
admin.site.register(ScientificResult)
