import csv
import json
from datetime import date, timedelta

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum, F
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth

from sales.models import Sale, SaleItem
from agencies.models import Agency
from products.models import Category
from inventory.models import Inventory
from accounts.models import Employee


def _has_reports_access(user):
    """CEO/Admin only — normal staff can't see company-wide reports."""
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
    """Percentage change, safe against division by zero."""
    if previous == 0:
        return None  # can't express as a percentage — template shows "→ n/a"
    return round(((current - previous) / previous) * 100, 1)


def _get_filtered_querysets(request):
    """
    Shared filter logic for date range / agency / category, reused by the
    dashboard and (later) the sales report page so it isn't duplicated.
    Returns (sales_qs, items_qs, start_date, end_date, filters_dict).
    """
    today = date.today()
    start_date = _parse_date(request.GET.get('start_date'), today - timedelta(days=30))
    end_date = _parse_date(request.GET.get('end_date'), today)

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    agency_id = request.GET.get('agency') or ''
    category_id = request.GET.get('category') or ''

    sales_qs = Sale.objects.filter(
        status='COMPLETED',
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    )
    if agency_id:
        sales_qs = sales_qs.filter(agency_id=agency_id)

    items_qs = SaleItem.objects.filter(sale__in=sales_qs)
    if category_id:
        items_qs = items_qs.filter(product__category_id=category_id)
        # narrow sales to only those that actually contain a matching item,
        # computed from items_qs itself so we don't re-filter against a
        # sales_qs that's already been mutated
        sales_qs = sales_qs.filter(id__in=items_qs.values('sale_id')).distinct()

    return sales_qs, items_qs, start_date, end_date, {
        'agency': agency_id,
        'category': category_id,
    }


@user_passes_test(_has_reports_access, login_url='Login')
def reports_dashboard(request):
    sales_qs, items_qs, start_date, end_date, filters = _get_filtered_querysets(request)
    granularity = request.GET.get('granularity', 'daily')

    period_length = (end_date - start_date).days + 1
    prev_end = start_date - timedelta(days=1)
    prev_start = prev_end - timedelta(days=period_length - 1)

    prev_sales_qs = Sale.objects.filter(
        status='COMPLETED',
        created_at__date__gte=prev_start,
        created_at__date__lte=prev_end,
    )
    if filters['agency']:
        prev_sales_qs = prev_sales_qs.filter(agency_id=filters['agency'])
    prev_items_qs = SaleItem.objects.filter(sale__in=prev_sales_qs)

    # --- Summary cards ---
    total_sales = sales_qs.count()
    total_revenue = sales_qs.aggregate(total=Sum('total_amount'))['total'] or 0
    total_products_sold = items_qs.aggregate(total=Sum('quantity'))['total'] or 0
    avg_sale_value = round(total_revenue / total_sales, 2) if total_sales else 0
    total_customers = sales_qs.values('customer').distinct().count()
    # aggregated at the DB level with F(), not a Python loop over every row
    low_stock_count = Inventory.objects.filter(quantity__lte=F('minimum_stock')).count()

    # --- Previous-period comparison ---
    prev_revenue = prev_sales_qs.aggregate(total=Sum('total_amount'))['total'] or 0
    prev_sales_count = prev_sales_qs.count()
    prev_products_sold = prev_items_qs.aggregate(total=Sum('quantity'))['total'] or 0
    prev_customers = prev_sales_qs.values('customer').distinct().count()

    revenue_growth = _growth(float(total_revenue), float(prev_revenue))
    sales_growth = _growth(total_sales, prev_sales_count)
    products_growth = _growth(total_products_sold, prev_products_sold)
    customers_growth = _growth(total_customers, prev_customers)

    # --- Revenue over time chart ---
    trunc_fn = {'daily': TruncDay, 'weekly': TruncWeek, 'monthly': TruncMonth}.get(granularity, TruncDay)
    revenue_over_time = list(
        sales_qs.annotate(period=trunc_fn('created_at'))
        .values('period')
        .annotate(revenue=Sum('total_amount'))
        .order_by('period')
    )
    revenue_labels = [r['period'].strftime('%Y-%m-%d') for r in revenue_over_time]
    revenue_data = [float(r['revenue']) for r in revenue_over_time]

    # --- Sales by agency chart (dynamic — whatever agencies exist) ---
    sales_by_agency = list(
        sales_qs.values('agency__name')
        .annotate(revenue=Sum('total_amount'))
        .order_by('-revenue')
    )
    agency_labels = [a['agency__name'] for a in sales_by_agency]
    agency_data = [float(a['revenue']) for a in sales_by_agency]

    # --- Top selling products ---
    top_products = list(
        items_qs.values('product__name', 'product__category__name')
        .annotate(qty=Sum('quantity'), revenue=Sum('subtotal'))
        .order_by('-qty')[:10]
    )

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'agencies': Agency.objects.filter(is_active=True),
        'categories': Category.objects.all(),
        'selected_agency': filters['agency'],
        'selected_category': filters['category'],
        'granularity': granularity,

        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'total_products_sold': total_products_sold,
        'avg_sale_value': avg_sale_value,
        'total_customers': total_customers,
        'low_stock_count': low_stock_count,

        'revenue_growth': revenue_growth,
        'sales_growth': sales_growth,
        'products_growth': products_growth,
        'customers_growth': customers_growth,

        'revenue_labels': revenue_labels,
        'revenue_data': revenue_data,
        'agency_labels': agency_labels,
        'agency_data': agency_data,

        'top_products': top_products,
        'has_data': total_sales > 0,
    }
    return render(request, 'reports/reports.html', context)


@user_passes_test(_has_reports_access, login_url='Login')
def reports_export_csv(request):
    """Exports the currently-filtered sales — respects the same GET filters
    as the dashboard, so what you see is what you export."""
    sales_qs, _, start_date, end_date, _ = _get_filtered_querysets(request)
    sales_qs = sales_qs.select_related('customer', 'agency', 'employee')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="sales_report_{start_date}_to_{end_date}.csv"'
    )

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


# ---------- Stub pages for the other 4 reports ----------
# Real views (not JS mockups), just minimal until built out properly in a
# follow-up — this keeps sidebar/cross-navigation from 404ing in the
# meantime. Each will reuse _get_filtered_querysets once implemented.

@user_passes_test(_has_reports_access, login_url='Login')
def sales_report(request):
    return render(request, 'reports/coming_soon.html', {'report_name': 'Sales Report'})


@user_passes_test(_has_reports_access, login_url='Login')
def inventory_report(request):
    return render(request, 'reports/coming_soon.html', {'report_name': 'Inventory Report'})


@user_passes_test(_has_reports_access, login_url='Login')
def agency_report(request):
    return render(request, 'reports/coming_soon.html', {'report_name': 'Agency Performance Report'})


@user_passes_test(_has_reports_access, login_url='Login')
def employee_report(request):
    return render(request, 'reports/coming_soon.html', {'report_name': 'Employee Performance Report'})