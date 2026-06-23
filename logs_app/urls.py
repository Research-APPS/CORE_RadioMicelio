from django.urls import path
from logs_app import views

app_name = "logs"

urlpatterns = [
    path("", views.platform_selector, name="platform_selector"),
    path("<slug:platform_slug>/", views.platform_dashboard, name="platform_dashboard"),
    path("api/platforms/<slug:platform_slug>/segments/", views.segments_api, name="segments_api"),
]
