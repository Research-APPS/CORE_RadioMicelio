from django.contrib.auth import views as auth_views
from django.urls import path
from cms_app import views

app_name = "cms"
urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="cms/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("taxonomias/nueva/", views.taxonomy_create, name="taxonomy_create"),
    path("taxonomias/<uuid:uuid>/editor/", views.taxonomy_editor, name="taxonomy_editor"),
    path("conceptos/<uuid:uuid>/editar/", views.concept_edit, name="concept_edit"),
]
