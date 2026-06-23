from django.urls import path
from knowledge_app import views

app_name = "knowledge"

urlpatterns = [
    path("api/concepts/<uuid:uuid>/jsonld/", views.concept_jsonld, name="concept_jsonld"),
    path("api/taxonomies/<slug:slug>/jsonld/", views.taxonomy_jsonld, name="taxonomy_jsonld"),
]
