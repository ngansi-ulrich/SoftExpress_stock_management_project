from django.contrib import admin
from .models import SystemSettings, NotificationPreference

admin.site.register(SystemSettings)
admin.site.register(NotificationPreference)