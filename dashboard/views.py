from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from products.models import Product
from customers.models import Customer
from accounts.models import Employee
from agencies.models import Agency
from logs.models import ActivityLog


@login_required
def dashboard(request):

    context = {
        "total_agencies": Agency.objects.count(),
        "total_products": Product.objects.count(),
        "total_customers": Customer.objects.count(),
        "total_employees": Employee.objects.count(),

        "recent_activities": ActivityLog.objects.select_related("user").order_by("-created_at")[:10],

        "stock_by_agency": Agency.objects.all()
    }

    return render(request, "dashboard/dashboard.html", context)