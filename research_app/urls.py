from django.urls import path
from research_app import views

app_name = "research"

urlpatterns = [
    path("", views.proyecto_list, name="proyecto_list"),
    path("investigaciones/", views.activity_list, name="activity_list"),
    path("investigaciones/nueva/", views.activity_create, name="activity_create"),
    path("investigaciones/<uuid:uuid>/editar/", views.activity_edit, name="activity_edit"),
    path("proyectos/<uuid:uuid>/", views.proyecto_detail, name="proyecto_detail"),
    path("proyectos/<uuid:uuid>/ontologia/", views.proyecto_ontology, name="proyecto_ontology"),
    path("proyectos/<uuid:uuid>/ontologia.json", views.proyecto_ontology_json, name="proyecto_ontology_json"),
    path("proyectos/<uuid:uuid>/digital-profile.json", views.digital_profile_json, name="digital_profile_json"),
    path(
        "proyectos/<uuid:uuid>/marcadores/<uuid:concept_uuid>/jsonld/",
        views.marker_jsonld,
        name="marker_jsonld",
    ),
]
