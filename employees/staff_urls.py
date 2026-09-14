from django.urls import path

from . import staff_views


urlpatterns = [
    path('', staff_views.employee_dashboard, name='employee_dashboard'),
    path('dashboard/', staff_views.employee_dashboard, name='employee_dashboard_page'),
    path('products/', staff_views.employee_products, name='employee_products'),
    path('products/<int:pk>/', staff_views.employee_product_detail, name='employee_product_detail'),
    path('inventory/', staff_views.employee_inventory, name='employee_inventory'),
    path('inventory/alerts/', staff_views.employee_stock_alerts, name='employee_stock_alerts'),
    path('sales/', staff_views.employee_sales, name='employee_sales'),
    path('sales/new/', staff_views.employee_new_sale, name='employee_new_sale'),
    path('sales/<int:pk>/', staff_views.employee_sale_detail, name='employee_sale_detail'),
    path('invoices/', staff_views.employee_invoices, name='employee_invoices'),
    path('invoices/<int:pk>/', staff_views.employee_invoice_detail, name='employee_invoice_detail'),
    path('invoices/<int:pk>/print/', staff_views.employee_invoice_print, name='employee_invoice_print'),
    path('invoices/<int:pk>/pdf/', staff_views.employee_invoice_pdf, name='employee_invoice_pdf'),
    path('customers/', staff_views.employee_customers, name='employee_customers'),
    path('customers/add/', staff_views.employee_add_customer, name='employee_add_customer'),
    path('customers/<int:id>/', staff_views.employee_customer_detail, name='employee_customer_detail'),
    path('customers/<int:id>/edit/', staff_views.employee_customer_edit, name='employee_customer_edit'),
    path('notifications/', staff_views.employee_notifications, name='employee_notifications'),
    path('profile/', staff_views.employee_profile, name='employee_profile'),
    path('change-password/', staff_views.employee_change_password, name='employee_change_password'),
]
