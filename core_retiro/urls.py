from django.contrib import admin
from django.urls import include, path
from core_retiro import views

urlpatterns = [
    path("", views.home, name="home"),
    path("capacidades/ontologizar/taxonomias/<slug:slug>/", views.ontology_taxonomy, name="ontology_taxonomy"),
    path("capacidades/<slug:public_slug>/", views.capability_detail, name="capability_detail"),
    path("resultados/", views.results_index, name="results_index"),
    path("airam/", include("airam_app.urls")),
    path("admin/", admin.site.urls),
    path("research/", include("research_app.urls")),
    path("logs/", include("logs_app.urls")),
    path("cms/", include("cms_app.urls")),
    path("biblioteca/", include(("cms_app.urls_public", "biblioteca"), namespace="biblioteca")),
    path("knowledge/", include("knowledge_app.urls")),
]
