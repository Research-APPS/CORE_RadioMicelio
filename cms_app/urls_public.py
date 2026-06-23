from django.urls import path
from cms_app import views_public

urlpatterns = [
    path("", views_public.biblioteca_index, name="index"),
    path("asignaturas/<slug:slug>/", views_public.subject_detail, name="subject"),
    path("diccionarios/<slug:subject_slug>/<slug:dict_slug>/", views_public.dictionary_detail, name="dictionary"),
    path("taxonomias/", views_public.taxonomy_list, name="taxonomy_list"),
    path("taxonomias/<slug:slug>/", views_public.taxonomy_detail, name="taxonomy"),
    path("temas/<uuid:uuid>/", views_public.topic_detail, name="topic"),
    path("temas/<uuid:uuid>/editar/", views_public.topic_edit, name="topic_edit"),
    path("asignaturas/<slug:slug>/editar/", views_public.subject_edit, name="subject_edit"),
    path(
        "asignaturas/<slug:slug>/materiales/<slug:mat_slug>/editar/",
        views_public.material_edit,
        name="material_edit",
    ),
]
