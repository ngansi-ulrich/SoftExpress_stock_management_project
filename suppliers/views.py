from django.shortcuts import render, get_object_or_404, redirect
from .models import Supplier
from .forms import SupplierForm


def supplier_list(request):

    suppliers = Supplier.objects.all()

    context = {
        "suppliers": suppliers,
        "total_suppliers": suppliers.count(),
        "active_suppliers": suppliers.filter(is_active=True).count(),
    }

    return render(
        request,
        "suppliers/suppliers.html",
        context
    )


def add_supplier(request):

    if request.method == "POST":

        form = SupplierForm(request.POST)

        if form.is_valid():

            form.save()

            return redirect(
                "supplier_list"
            )

    else:

        form = SupplierForm()

    return render(
        request,
        "suppliers/add_supplier.html",
        {
            "form": form
        }
    )


def supplier_edit(request, id):

    supplier = get_object_or_404(
        Supplier,
        id=id
    )

    if request.method == "POST":

        form = SupplierForm(
            request.POST,
            instance=supplier
        )

        if form.is_valid():

            form.save()

            return redirect(
                'supplier_list'
            )

    else:

        form = SupplierForm(
            instance=supplier
        )

    return render(
        request,
        'suppliers/edit_supplier.html',
        {
            'form': form
        }
    )


def supplier_delete(request, id):

    supplier = get_object_or_404(
        Supplier,
        id=id
    )

    supplier.delete()

    return redirect(
        'supplier_list'
    )