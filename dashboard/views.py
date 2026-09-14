from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, F, Q
from django.utils import timezone

from products.models import Product
from customers.models import Customer
from accounts.models import Employee
from agencies.models import Agency
from logs.models import ActivityLog
from inventory.models import Inventory
from sales.models import Sale, SaleItem
from transfers.models import Transfer
from accounts.permissions import get_employee, is_ceo, get_agency_scope, UNRESTRICTED


@login_required
def dashboard(request):
    if not is_ceo(request.user):
        if get_employee(request.user) and get_employee(request.user).role == 'STAFF':
            return redirect('employee_dashboard')
        return redirect('manager_dashboard')

    context = {
        "total_agencies": Agency.objects.count(),
        "total_products": Product.objects.count(),
        "total_customers": Customer.objects.count(),
        "total_employees": Employee.objects.count(),

        "recent_activities": ActivityLog.objects.select_related("user").order_by("-created_at")[:10],

        "stock_by_agency": Agency.objects.all()
    }

    return render(request, "dashboard/dashboard.html", context)


@login_required
def manager_dashboard(request):
    # CEOs land here if they follow a Manager link — send them to their
    # own dashboard instead of showing them a single-agency view
    if is_ceo(request.user):
        return redirect('dashboard')

    employee = get_employee(request.user)
    if employee is None or employee.role != 'MANAGER':
        raise PermissionDenied

    agency = employee.agency

    if agency is None:
        # Never fall back to showing global/unscoped data here
        return render(request, 'dashboard/manager_dashboard.html', {
            'employee': employee,
            'no_agency': True,
        })

    today = timezone.localdate()
    month_start = today.replace(day=1)

    sales_today = Sale.objects.filter(agency=agency, status='COMPLETED', created_at__date=today)
    sales_month = Sale.objects.filter(agency=agency, status='COMPLETED', created_at__date__gte=month_start)

    inventory = Inventory.objects.filter(agency=agency).select_related('product', 'product__category')

    pending_transfers = Transfer.objects.filter(
        Q(source_agency=agency) | Q(destination_agency=agency),
        status='PENDING'
    ).count()

    top_products = (
        SaleItem.objects.filter(sale__agency=agency, sale__status='COMPLETED')
        .values('product__name')
        .annotate(qty=Sum('quantity'))
        .order_by('-qty')[:5]
    )

    context = {
        'employee': employee,
        'agency': agency,
        'no_agency': False,

        'todays_sales_count': sales_today.count(),
        'todays_revenue': sales_today.aggregate(total=Sum('total_amount'))['total'] or 0,
        'monthly_revenue': sales_month.aggregate(total=Sum('total_amount'))['total'] or 0,

        'current_stock': inventory.aggregate(total=Sum('quantity'))['total'] or 0,
        'low_stock_count': inventory.filter(quantity__lte=F('minimum_stock'), quantity__gt=0).count(),
        'out_of_stock_count': inventory.filter(quantity=0).count(),
        'low_stock_items': inventory.filter(quantity__lte=F('minimum_stock'))[:5],

        'total_customers': Sale.objects.filter(agency=agency).values('customer').distinct().count(),
        'pending_transfers': pending_transfers,

        'recent_sales': Sale.objects.filter(agency=agency).select_related('customer').order_by('-created_at')[:5],
        'top_products': top_products,
    }
    return render(request, 'dashboard/manager_dashboard.html', context)


@login_required
def notifications_view(request):
    """
    Live-computed alert feed, NOT a persisted notification log — there's
    no email/SMS/push delivery system in this project (see the
    NotificationPreference model in setting_app, which stores real
    toggle preferences but has nothing to act on them yet). Rather than
    fake a notification history, this queries current real state
    (low stock, pending transfers) fresh on every page load. Nothing
    here is "sent" to anyone; it's just surfaced when viewed.
    """
    from django.core.exceptions import PermissionDenied

    scope = get_agency_scope(request.user)
    if scope is False:
        raise PermissionDenied

    if scope is None:
        return render(request, 'dashboard/notifications.html', {
            'no_agency': True,
        })

    inventory_qs = Inventory.objects.select_related('product', 'agency')
    transfer_qs = Transfer.objects.select_related('source_agency', 'destination_agency', 'product')

    if scope is not UNRESTRICTED:
        inventory_qs = inventory_qs.filter(agency=scope)
        transfer_qs = transfer_qs.filter(Q(source_agency=scope) | Q(destination_agency=scope))

    out_of_stock = inventory_qs.filter(quantity=0)
    low_stock = inventory_qs.filter(quantity__gt=0, quantity__lte=F('minimum_stock'))
    pending_transfers = transfer_qs.filter(status='PENDING')

    context = {
        'no_agency': False,
        'out_of_stock': out_of_stock,
        'low_stock': low_stock,
        'pending_transfers': pending_transfers,
        'total_alerts': out_of_stock.count() + low_stock.count() + pending_transfers.count(),
    }
    return render(request, 'dashboard/notifications.html', context)