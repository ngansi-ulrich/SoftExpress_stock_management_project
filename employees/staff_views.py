from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import F, Sum
from django.shortcuts import render
from django.utils import timezone

from accounts.permissions import get_employee, role_required
from customers.models import Customer
from dashboard.views import notifications_view
from inventory.models import Inventory
from products.models import Product
from sales.models import Sale, SaleItem


@role_required('STAFF')
def employee_dashboard(request):
    employee = get_employee(request.user)
    if employee is None or employee.role != 'STAFF':
        raise PermissionDenied
    agency = employee.agency
    if agency is None:
        return render(request, 'employees/employee_dashboard.html', {
            'employee': employee,
            'no_agency': True,
        })

    today = timezone.localdate()
    own_sales = Sale.objects.filter(
        employee=employee,
        agency=agency,
        status='COMPLETED',
    )
    sales_today = own_sales.filter(created_at__date=today)
    inventory = Inventory.objects.filter(agency=agency).select_related('product')
    recent_sales = Sale.objects.filter(
        employee=employee,
        agency=agency,
    ).select_related('customer').order_by('-created_at')[:5]

    context = {
        'employee': employee,
        'agency': agency,
        'no_agency': False,
        'todays_sales_count': sales_today.count(),
        'todays_revenue': sales_today.aggregate(total=Sum('total_amount'))['total'] or 0,
        'products_sold': sales_today.aggregate(total=Sum('items__quantity'))['total'] or 0,
        'customers_served': sales_today.values('customer').distinct().count(),
        'recent_sales': recent_sales,
        'low_stock_items': inventory.filter(quantity__lte=F('minimum_stock')).order_by('quantity', 'product__name')[:5],
        'low_stock_count': inventory.filter(quantity__lte=F('minimum_stock')).count(),
    }
    return render(request, 'employees/employee_dashboard.html', context)


@role_required('STAFF')
def employee_products(request):
    from products.views import product_list
    return product_list(request)


@role_required('STAFF')
def employee_product_detail(request, pk):
    from products.views import product_detail
    return product_detail(request, pk)


@role_required('STAFF')
def employee_inventory(request):
    from inventory.views import inventory_list
    return inventory_list(request)


@role_required('STAFF')
def employee_stock_alerts(request):
    from inventory.views import stock_alerts
    return stock_alerts(request)


@role_required('STAFF')
def employee_new_sale(request):
    from sales.views import sale_create
    return sale_create(request)


@role_required('STAFF')
def employee_sales(request):
    from sales.views import sale_list
    return sale_list(request)


@role_required('STAFF')
def employee_sale_detail(request, pk):
    from sales.views import sale_detail
    return sale_detail(request, pk)


@role_required('STAFF')
def employee_invoices(request):
    from sales.views import invoice_list
    return invoice_list(request)


@role_required('STAFF')
def employee_invoice_detail(request, pk):
    from sales.views import invoice_detail
    return invoice_detail(request, pk)


@role_required('STAFF')
def employee_invoice_print(request, pk):
    from sales.views import invoice_print
    return invoice_print(request, pk)


@role_required('STAFF')
def employee_invoice_pdf(request, pk):
    from sales.views import invoice_pdf
    return invoice_pdf(request, pk)


@role_required('STAFF')
def employee_customers(request):
    from customers.views import customer_list
    return customer_list(request)


@role_required('STAFF')
def employee_add_customer(request):
    from customers.views import add_customer
    return add_customer(request)


@role_required('STAFF')
def employee_customer_detail(request, id):
    from customers.views import customer_detail
    return customer_detail(request, id)


@role_required('STAFF')
def employee_customer_edit(request, id):
    from customers.views import customer_edit
    return customer_edit(request, id)


@role_required('STAFF')
def employee_notifications(request):
    return notifications_view(request)


@role_required('STAFF')
def employee_profile(request):
    from accounts.views import profile_view
    return profile_view(request)


@role_required('STAFF')
def employee_change_password(request):
    from accounts.views import change_password
    return change_password(request)
