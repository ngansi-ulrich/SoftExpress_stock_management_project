from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventory_list, name='inventory_list'),
    path('alerts/', views.stock_alerts, name='stock_alerts'),
    path('adjust/', views.stock_adjustment, name='stock_adjustment'),
]