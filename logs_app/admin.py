from django.contrib import admin
from logs_app.models import EventLog, ProjectPlatformLink

admin.site.register(EventLog)
admin.site.register(ProjectPlatformLink)
