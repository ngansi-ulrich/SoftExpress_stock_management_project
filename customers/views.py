from django.shortcuts import render, get_object_or_404, redirect
from .models import Customer
from .forms import CustomerForm


def customer_list(request):

    customers = Customer.objects.all()

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


def add_customer(request):

    if request.method == "POST":

        form = CustomerForm(request.POST)

        if form.is_valid():

            form.save()

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


def customer_edit(request, id):

    customer = get_object_or_404(
        Customer,
        id=id
    )

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


def customer_delete(request, id):

    customer = get_object_or_404(
        Customer,
        id=id
    )

    customer.delete()

    return redirect(
        'customer_list'
    )