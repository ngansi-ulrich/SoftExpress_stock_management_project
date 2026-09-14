import csv
from datetime import date, timedelta

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, F, Count
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth

from sales.models import Sale, SaleItem
from agencies.models import Agency
from products.models import Category
from inventory.models import Inventory
from accounts.models import Employee
from accounts.permissions import get_agency_scope, UNRESTRICTED
from stock_movements.models import StockMovement


def _has_reports_access(user):
    """CEO/Admin AND Agency Manager — normal staff still can't see
    reports at all."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return Employee.objects.filter(user=user, role__in=['CEO', 'MANAGER']).exists()


def _parse_date(value, default):
    if not value:
        return default
    try:
        return date.fromisoformat(value)
    except ValueError:
        return default


def _growth(current, previous):
    if previous == 0:
        return None
    return round(((current - previous) / previous) * 100, 1)


def _get_filtered_querysets(request):
    """
    Agency scoping is applied FIRST and unconditionally for non-CEO
    users — the 'agency' GET parameter is only honored for CEOs.
    """
    scope = get_agency_scope(request.user)
    if scope is False:
        raise PermissionDenied

    today = date.today()
    start_date = _parse_date(request.GET.get('start_date'), today - timedelta(days=30))
    end_date = _parse_date(request.GET.get('end_date'), today)
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    category_id = request.GET.get('category') or ''

    sales_qs = Sale.objects.filter(
        status='COMPLETED',
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    )

    if scope is None:
        sales_qs = sales_qs.none()
        agency_id = ''
    elif scope is UNRESTRICTED:
        agency_id = request.GET.get('agency') or ''
        if agency_id:
            sales_qs = sales_qs.filter(agency_id=agency_id)
    else:
        sales_qs = sales_qs.filter(agency=scope)
        agency_id = str(scope.pk)

    items_qs = SaleItem.objects.filter(sale__in=sales_qs)
    if category_id:
        items_qs = items_qs.filter(product__category_id=category_id)
        sales_qs = sales_qs.filter(id__in=items_qs.values('sale_id')).distinct()

    return sales_qs, items_qs, start_date, end_date, {
        'agency': agency_id,
        'category': category_id,
    }, scope


@user_passes_test(_has_reports_access, login_url='Login')
def reports_dashboard(request):
    sales_qs, items_qs, start_date, end_date, filters, scope = _get_filtered_querysets(request)
    granularity = request.GET.get('granularity', 'daily')

    period_length = (end_date - start_date).days + 1
    prev_end = start_date - timedelta(days=1)
    prev_start = prev_end - timedelta(days=period_length - 1)

    prev_sales_qs = Sale.objects.filter(
        status='COMPLETED',
        created_at__date__gte=prev_start,
        created_at__date__lte=prev_end,
    )
    if scope is None:
        prev_sales_qs = prev_sales_qs.none()
    elif scope is not UNRESTRICTED:
        prev_sales_qs = prev_sales_qs.filter(agency=scope)
    prev_items_qs = SaleItem.objects.filter(sale__in=prev_sales_qs)

    total_sales = sales_qs.count()
    total_revenue = sales_qs.aggregate(total=Sum('total_amount'))['total'] or 0
    total_products_sold = items_qs.aggregate(total=Sum('quantity'))['total'] or 0
    avg_sale_value = round(total_revenue / total_sales, 2) if total_sales else 0
    total_customers = sales_qs.values('customer').distinct().count()

    low_stock_qs = Inventory.objects.filter(quantity__lte=F('minimum_stock'))
    if scope is not UNRESTRICTED and scope is not None:
        low_stock_qs = low_stock_qs.filter(agency=scope)
    elif scope is None:
        low_stock_qs = low_stock_qs.none()
    low_stock_count = low_stock_qs.count()

    prev_revenue = prev_sales_qs.aggregate(total=Sum('total_amount'))['total'] or 0
    prev_sales_count = prev_sales_qs.count()
    prev_products_sold = prev_items_qs.aggregate(total=Sum('quantity'))['total'] or 0
    prev_customers = prev_sales_qs.values('customer').distinct().count()

    revenue_growth = _growth(float(total_revenue), float(prev_revenue))
    sales_growth = _growth(total_sales, prev_sales_count)
    products_growth = _growth(total_products_sold, prev_products_sold)
    customers_growth = _growth(total_customers, prev_customers)

    trunc_fn = {'daily': TruncDay, 'weekly': TruncWeek, 'monthly': TruncMonth}.get(granularity, TruncDay)
    revenue_over_time = list(
        sales_qs.annotate(period=trunc_fn('created_at'))
        .values('period').annotate(revenue=Sum('total_amount')).order_by('period')
    )
    revenue_labels = [r['period'].strftime('%Y-%m-%d') for r in revenue_over_time]
    revenue_data = [float(r['revenue']) for r in revenue_over_time]

    sales_by_agency = list(
        sales_qs.values('agency__name').annotate(revenue=Sum('total_amount')).order_by('-revenue')
    )
    agency_labels = [a['agency__name'] for a in sales_by_agency]
    agency_data = [float(a['revenue']) for a in sales_by_agency]

    top_products = list(
        items_qs.values('product__name', 'product__category__name')
        .annotate(qty=Sum('quantity'), revenue=Sum('subtotal')).order_by('-qty')[:10]
    )

    context = {
        'start_date': start_date, 'end_date': end_date,
        'agencies': Agency.objects.filter(is_active=True) if scope is UNRESTRICTED else Agency.objects.none(),
        'categories': Category.objects.all(),
        'selected_agency': filters['agency'], 'selected_category': filters['category'],
        'granularity': granularity, 'is_ceo_viewing': scope is UNRESTRICTED,

        'total_sales': total_sales, 'total_revenue': total_revenue,
        'total_products_sold': total_products_sold, 'avg_sale_value': avg_sale_value,
        'total_customers': total_customers, 'low_stock_count': low_stock_count,

        'revenue_growth': revenue_growth, 'sales_growth': sales_growth,
        'products_growth': products_growth, 'customers_growth': customers_growth,

        'revenue_labels': revenue_labels, 'revenue_data': revenue_data,
        'agency_labels': agency_labels, 'agency_data': agency_data,

        'top_products': top_products, 'has_data': total_sales > 0,
    }
    return render(request, 'reports/reports.html', context)


@user_passes_test(_has_reports_access, login_url='Login')
def reports_export_csv(request):
    sales_qs, _, start_date, end_date, _, scope = _get_filtered_querysets(request)
    sales_qs = sales_qs.select_related('customer', 'agency', 'employee')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="sales_report_{start_date}_to_{end_date}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Sale Number', 'Customer', 'Agency', 'Employee', 'Payment Method', 'Payment Status', 'Amount', 'Date'])
    for sale in sales_qs:
        writer.writerow([
            sale.sale_number,
            f"{sale.customer.first_name} {sale.customer.last_name}",
            sale.agency.name,
            f"{sale.employee.first_name} {sale.employee.last_name}",
            sale.get_payment_method_display(),
            sale.get_payment_status_display(),
            sale.total_amount,
            sale.created_at.strftime('%Y-%m-%d %H:%M'),
        ])
    return response


@user_passes_test(_has_reports_access, login_url='Login')
def sales_report(request):
    sales_qs, items_qs, start_date, end_date, filters, scope = _get_filtered_querysets(request)

    payment_method = request.GET.get('payment_method')
    if payment_method:
        sales_qs = sales_qs.filter(payment_method=payment_method)
        items_qs = SaleItem.objects.filter(sale__in=sales_qs)

    total_sales = sales_qs.count()
    total_revenue = sales_qs.aggregate(total=Sum('total_amount'))['total'] or 0
    avg_order_value = round(total_revenue / total_sales, 2) if total_sales else 0
    products_sold = items_qs.aggregate(total=Sum('quantity'))['total'] or 0
    customer_count = sales_qs.values('customer').distinct().count()

    top_products = list(
        items_qs.values('product__name')
        .annotate(qty=Sum('quantity'), revenue=Sum('subtotal')).order_by('-qty')[:10]
    )
    top_customers = list(
        sales_qs.values('customer__first_name', 'customer__last_name')
        .annotate(total=Sum('total_amount'), count=Count('id')).order_by('-total')[:10]
    )
    sales_by_category = list(
        items_qs.values('product__category__name')
        .annotate(revenue=Sum('subtotal')).order_by('-revenue')
    )
    sales_by_payment = list(
        sales_qs.values('payment_method').annotate(total=Sum('total_amount')).order_by('-total')
    )

    agency_performance = []
    if scope is UNRESTRICTED:
        agency_performance = list(
            sales_qs.values('agency__name')
            .annotate(revenue=Sum('total_amount'), count=Count('id')).order_by('-revenue')
        )

    context = {
        'start_date': start_date, 'end_date': end_date,
        'agencies': Agency.objects.filter(is_active=True) if scope is UNRESTRICTED else Agency.objects.none(),
        'categories': Category.objects.all(),
        'selected_agency': filters['agency'], 'selected_category': filters['category'],
        'selected_payment_method': payment_method or '',
        'is_ceo_viewing': scope is UNRESTRICTED,

        'total_sales': total_sales, 'total_revenue': total_revenue,
        'avg_order_value': avg_order_value, 'products_sold': products_sold,
        'customer_count': customer_count,

        'top_products': top_products, 'top_customers': top_customers,
        'sales_by_category': sales_by_category, 'sales_by_payment': sales_by_payment,
        'agency_performance': agency_performance,
        'has_data': total_sales > 0,
    }
    return render(request, 'reports/sales_report.html', context)


@user_passes_test(_has_reports_access, login_url='Login')
def inventory_report(request):
    scope = get_agency_scope(request.user)
    if scope is False:
        raise PermissionDenied

    inventory_qs = Inventory.objects.select_related('product', 'product__category', 'agency')

    if scope is None:
        inventory_qs = Inventory.objects.none()
    elif scope is not UNRESTRICTED:
        inventory_qs = inventory_qs.filter(agency=scope)

    category_id = request.GET.get('category')
    if category_id:
        inventory_qs = inventory_qs.filter(product__category_id=category_id)

    agency_id = request.GET.get('agency')
    if scope is UNRESTRICTED and agency_id:
        inventory_qs = inventory_qs.filter(agency_id=agency_id)

    total_stock_quantity = inventory_qs.aggregate(total=Sum('quantity'))['total'] or 0
    low_stock_qs = inventory_qs.filter(quantity__lte=F('minimum_stock'), quantity__gt=0)
    out_of_stock_qs = inventory_qs.filter(quantity=0)

    inventory_value = sum(i.quantity * i.product.selling_price for i in inventory_qs)

    stock_by_category = list(
        inventory_qs.values('product__category__name')
        .annotate(quantity=Sum('quantity')).order_by('-quantity')
    )

    stock_by_agency = []
    if scope is UNRESTRICTED:
        stock_by_agency = list(
            inventory_qs.values('agency__name')
            .annotate(quantity=Sum('quantity')).order_by('-quantity')
        )

    movements_qs = StockMovement.objects.select_related(
        'inventory', 'inventory__product', 'inventory__agency', 'employee'
    ).order_by('-created_at')

    if scope is None:
        movements_qs = StockMovement.objects.none()
    elif scope is not UNRESTRICTED:
        movements_qs = movements_qs.filter(inventory__agency=scope)

    movement_counts = {
        'in': movements_qs.filter(movement_type='IN').count(),
        'out': movements_qs.filter(movement_type='OUT').count(),
        'transfer': movements_qs.filter(movement_type='TRANSFER').count(),
    }

    inventory_table = list(inventory_qs.order_by('product__name'))
    for item in inventory_table:
        item.line_value = item.quantity * item.product.selling_price

    context = {
        'agencies': Agency.objects.filter(is_active=True) if scope is UNRESTRICTED else Agency.objects.none(),
        'categories': Category.objects.all(),
        'selected_agency': agency_id or '',
        'selected_category': category_id or '',
        'is_ceo_viewing': scope is UNRESTRICTED,

        'total_products': inventory_qs.values('product').distinct().count(),
        'total_stock_quantity': total_stock_quantity,
        'inventory_value': inventory_value,
        'low_stock_count': low_stock_qs.count(),
        'out_of_stock_count': out_of_stock_qs.count(),

        'stock_by_category': stock_by_category,
        'stock_by_agency': stock_by_agency,

        'inventory_table': inventory_table,

        'movement_analysis_available': True,
        'movement_counts': movement_counts,
        'recent_movements': movements_qs[:15],
    }
    return render(request, 'reports/inventory_report.html', context)


@user_passes_test(_has_reports_access, login_url='Login')
def agency_report(request):
    # Stricter than the general reports gate — a Manager must NEVER see
    # cross-agency comparisons
    if not (request.user.is_superuser or Employee.objects.filter(user=request.user, role='CEO').exists()):
        raise PermissionDenied

    sort = request.GET.get('sort', 'revenue')

    agencies_data = []
    for agency in Agency.objects.filter(is_active=True):
        sales = Sale.objects.filter(agency=agency, status='COMPLETED')
        revenue = sales.aggregate(t=Sum('total_amount'))['t'] or 0
        products_sold = SaleItem.objects.filter(sale__in=sales).aggregate(t=Sum('quantity'))['t'] or 0
        current_stock = Inventory.objects.filter(agency=agency).aggregate(t=Sum('quantity'))['t'] or 0
        low_stock = Inventory.objects.filter(agency=agency, quantity__lte=F('minimum_stock')).count()

        agencies_data.append({
            'agency': agency,
            'revenue': revenue,
            'sales_count': sales.count(),
            'products_sold': products_sold,
            'clients': sales.values('customer').distinct().count(),
            'current_stock': current_stock,
            'low_stock': low_stock,
            'employees': Employee.objects.filter(agency=agency).count(),
        })

    sort_key = {
        'revenue': lambda x: x['revenue'],
        'sales': lambda x: x['sales_count'],
        'products': lambda x: x['products_sold'],
        'clients': lambda x: x['clients'],
        'stock': lambda x: x['current_stock'],
    }.get(sort, lambda x: x['revenue'])
    agencies_data.sort(key=sort_key, reverse=True)

    revenue_labels = [d['agency'].name for d in agencies_data]
    revenue_data = [float(d['revenue']) for d in agencies_data]

    return render(request, 'reports/agency_report.html', {
        'agencies_data': agencies_data,
        'sort': sort,
        'revenue_labels': revenue_labels,
        'revenue_data': revenue_data,
        'has_data': len(agencies_data) > 0,
    })


@user_passes_test(_has_reports_access, login_url='Login')
def employee_report(request):
    scope = get_agency_scope(request.user)
    if scope is False:
        raise PermissionDenied

    today = date.today()
    start_date = _parse_date(request.GET.get('start_date'), today - timedelta(days=30))
    end_date = _parse_date(request.GET.get('end_date'), today)
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    employees_qs = Employee.objects.select_related('agency').all()

    if scope is None:
        employees_qs = Employee.objects.none()
    elif scope is not UNRESTRICTED:
        employees_qs = employees_qs.filter(agency=scope)
    else:
        agency_id = request.GET.get('agency')
        if agency_id:
            employees_qs = employees_qs.filter(agency_id=agency_id)

    employees_for_filter = employees_qs

    employee_id = request.GET.get('employee')
    if employee_id:
        employees_qs = employees_qs.filter(pk=employee_id)

    performance = []
    for employee in employees_qs:
        sales = Sale.objects.filter(
            employee=employee, status='COMPLETED',
            created_at__date__gte=start_date, created_at__date__lte=end_date,
        )
        revenue = sales.aggregate(t=Sum('total_amount'))['t'] or 0
        sales_count = sales.count()
        products_sold = SaleItem.objects.filter(sale__in=sales).aggregate(t=Sum('quantity'))['t'] or 0

        if sales_count > 0:
            performance.append({
                'employee': employee,
                'sales_count': sales_count,
                'revenue': revenue,
                'products_sold': products_sold,
                'avg_sale': round(revenue / sales_count, 2),
            })

    performance.sort(key=lambda x: x['revenue'], reverse=True)

    chart_labels = [f"{p['employee'].first_name} {p['employee'].last_name}" for p in performance[:10]]
    chart_data = [float(p['revenue']) for p in performance[:10]]

    return render(request, 'reports/employee_report.html', {
        'start_date': start_date, 'end_date': end_date,
        'agencies': Agency.objects.filter(is_active=True) if scope is UNRESTRICTED else Agency.objects.none(),
        'employees_for_filter': employees_for_filter,
        'selected_agency': request.GET.get('agency', ''),
        'selected_employee': employee_id or '',
        'is_ceo_viewing': scope is UNRESTRICTED,
        'performance': performance,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'has_data': len(performance) > 0,
    })