from django.urls import path
from . import views

urlpatterns = [
    path('', views.agency_list, name='agency_list'),
    path('add/', views.add_agency, name='add_agency'),
    path('edit/<int:id>/', views.edit_agency, name='edit_agency'),
    path('delete/<int:id>/', views.delete_agency, name='delete_agency'),
]