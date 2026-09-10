from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_dashboard, name='reports_dashboard'),
    path('export/csv/', views.reports_export_csv, name='reports_export_csv'),
    path('sales/', views.sales_report, name='sales_report'),
    path('inventory/', views.inventory_report, name='inventory_report'),
    path('agencies/', views.agency_report, name='agency_report'),
    path('employees/', views.employee_report, name='employee_report'),
]