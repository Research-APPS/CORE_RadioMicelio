from django.urls import path
from airam_app import views

urlpatterns = [
    path("graph.json", views.graph_json, name="graph_json"),
]
