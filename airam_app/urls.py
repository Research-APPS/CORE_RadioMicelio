from django.urls import path
from airam_app import views

urlpatterns = [
    path("graph.json", views.graph_json, name="graph_json"),
    path("sessions/", views.session_create, name="session_create"),
    path("sessions/<uuid:uuid>/", views.session_detail, name="session_detail"),
    path("sessions/<uuid:uuid>/bookmark/", views.session_bookmark, name="session_bookmark"),
    path("sessions/<uuid:uuid>/rdf/", views.session_rdf, name="session_rdf"),
    path("temario/rdf/", views.temario_rdf_export, name="temario_rdf_export"),
]
