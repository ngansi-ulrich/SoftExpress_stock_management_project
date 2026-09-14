from django.urls import path
from . import views

urlpatterns = [
    path('', views.settings_view, name='settings_view'),
    path('save/general/', views.settings_save_general, name='settings_save_general'),
    path('save/notifications/', views.settings_save_notifications, name='settings_save_notifications'),
]