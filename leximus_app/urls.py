from django.urls import path
from leximus_app import views

app_name = "leximus"

urlpatterns = [
    path("taxonomies/<slug:slug>/", views.taxonomy_detail, name="taxonomy_detail"),
    path("api/taxonomies/<slug:slug>/", views.taxonomy_api, name="taxonomy_api"),
    path("api/taxonomies/<slug:slug>/jsonld/", views.taxonomy_jsonld, name="taxonomy_jsonld"),
]
