from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from accounts.permissions import get_agency_scope, role_required, UNRESTRICTED
from .models import Customer
from .forms import CustomerForm


@login_required
def customer_list(request):
    scope = get_agency_scope(request.user)
    if scope is False:
        raise PermissionDenied

    customers = Customer.objects.all()

    if scope is None:
        messages.error(request, "Your account isn't assigned to an agency yet.")
        customers = Customer.objects.none()
    elif scope is not UNRESTRICTED:
        customers = customers.filter(Q(agency=scope) | Q(sale__agency=scope)).distinct()

    context = {
        "customers": customers,
        "total_customers": customers.count(),
        "with_email_count": customers.exclude(email__isnull=True).exclude(email__exact="").count(),
    }

    return render(
        request,
        "customers/customers.html",
        context
    )


@login_required
def add_customer(request):
    scope = get_agency_scope(request.user)
    if scope is False or scope is None:
        raise PermissionDenied
    if request.method == "POST":

        form = CustomerForm(request.POST)

        if form.is_valid():

            customer = form.save(commit=False)
            if scope is not UNRESTRICTED:
                customer.agency = scope
            customer.save()

            return redirect(
                "customer_list"
            )

    else:

        form = CustomerForm()

    return render(
        request,
        "customers/add_customer.html",
        {
            "form": form
        }
    )


def _get_scoped_customer_or_404(request, id):
    scope = get_agency_scope(request.user)
    if scope is False:
        raise PermissionDenied
    if scope is UNRESTRICTED:
        return get_object_or_404(Customer, id=id)
    return get_object_or_404(
        Customer.objects.filter(Q(agency=scope) | Q(sale__agency=scope)).distinct(), id=id
    )


@login_required
def customer_edit(request, id):
    customer = _get_scoped_customer_or_404(request, id)

    if request.method == "POST":

        form = CustomerForm(
            request.POST,
            instance=customer
        )

        if form.is_valid():

            form.save()

            return redirect(
                'customer_list'
            )

    else:

        form = CustomerForm(
            instance=customer
        )

    return render(
        request,
        'customers/edit_customer.html',
        {
            'form': form
        }
    )


@login_required
def customer_detail(request, id):
    customer = _get_scoped_customer_or_404(request, id)
    purchases = customer.sale_set.select_related('agency', 'employee').order_by('-created_at')
    return render(request, 'customers/customer_detail.html', {
        'customer': customer,
        'purchases': purchases,
    })


@role_required('CEO', 'MANAGER')
def customer_delete(request, id):
    customer = _get_scoped_customer_or_404(request, id)
    customer.delete()

    return redirect(
        'customer_list'
    )