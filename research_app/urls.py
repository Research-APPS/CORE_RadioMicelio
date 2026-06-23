from django.urls import path
from research_app import views

app_name = "research"

urlpatterns = [
    path("", views.proyecto_list, name="proyecto_list"),
    path("proyectos/<uuid:uuid>/", views.proyecto_detail, name="proyecto_detail"),
    path("proyectos/<uuid:uuid>/digital-profile.json", views.digital_profile_json, name="digital_profile_json"),
]
