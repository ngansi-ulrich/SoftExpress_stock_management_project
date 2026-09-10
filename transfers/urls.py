from django.urls import path
from . import views

urlpatterns = [
    path('', views.transfer_list, name='transfer_list'),
    path('add/', views.transfer_create, name='transfer_create'),
    path('history/', views.transfer_history, name='transfer_history'),
    path('<int:pk>/', views.transfer_detail, name='transfer_detail'),
    path('<int:pk>/approve/', views.transfer_approve, name='transfer_approve'),
    path('<int:pk>/reject/', views.transfer_reject, name='transfer_reject'),
]