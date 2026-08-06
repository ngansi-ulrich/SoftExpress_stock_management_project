from django.urls import path
from . import views

urlpatterns = [
    # Match /agencies/
    path('', views.agency_list, name='agency_list'),
    
    # Match /agencies/add/
    path('add/', views.agency_create, name='agency_create'),
    
    # Match /agencies/<id>/edit/
    path('<int:pk>/edit/', views.agency_update, name='agency_update'),
    
    # Match /agencies/<id>/delete/
    path('<int:pk>/delete/', views.agency_delete, name='agency_delete'),
]