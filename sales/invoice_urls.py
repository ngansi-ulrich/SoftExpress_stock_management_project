from django.urls import path
from . import views

# Mounted separately at /invoices/ in config/urls.py — kept inside the
# sales app since Invoice is a thin wrapper around Sale, not an
# independently-creatable resource.
urlpatterns = [
    path('', views.invoice_list, name='invoice_list'),
    path('<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('<int:pk>/print/', views.invoice_print, name='invoice_print'),
    path('<int:pk>/pdf/', views.invoice_pdf, name='invoice_pdf'),
]