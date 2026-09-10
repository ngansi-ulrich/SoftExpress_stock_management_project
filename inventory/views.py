from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from products.models import Product
from .models import Inventory
from .form import StockAdjustmentForm


@login_required
def inventory_list(request):
    inventories = Inventory.objects.select_related('product', 'product__category', 'agency').all()

    total_quantity = sum(i.quantity for i in inventories)
    inventory_value = sum(i.quantity * i.product.selling_price for i in inventories)
    low_stock_count = sum(1 for i in inventories if i.is_low_stock)

    context = {
        'inventories': inventories,
        'total_products': Product.objects.count(),
        'total_quantity': total_quantity,
        'inventory_value': inventory_value,
        'low_stock_count': low_stock_count,
        'low_stock_items': [i for i in inventories if i.is_low_stock][:5],
    }
    return render(request, 'inventory/inventory.html', context)


@login_required
def stock_alerts(request):
    inventories = Inventory.objects.select_related('product', 'product__category', 'agency').all()

    low_items = [i for i in inventories if i.is_low_stock]
    # "critical" = at or below half of minimum stock (or zero); the rest of
    # the low-stock items are just "low"
    critical_items = [i for i in low_items if i.quantity == 0 or i.quantity <= i.minimum_stock // 2]
    warning_items = [i for i in low_items if i not in critical_items]
    normal_count = inventories.count() - len(low_items)

    context = {
        'critical_items': critical_items,
        'warning_items': warning_items,
        'normal_count': normal_count,
    }
    return render(request, 'inventory/stock_alerts.html', context)


@login_required
def stock_adjustment(request):
    form = StockAdjustmentForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        product = form.cleaned_data['product']
        agency = form.cleaned_data['agency']
        adjustment_type = form.cleaned_data['adjustment_type']
        quantity = form.cleaned_data['quantity']

        inventory, _ = Inventory.objects.get_or_create(product=product, agency=agency)

        if adjustment_type == 'add':
            inventory.quantity += quantity
        elif adjustment_type == 'remove':
            inventory.quantity = max(0, inventory.quantity - quantity)
        elif adjustment_type == 'correction':
            inventory.quantity = quantity

        inventory.save()

        # TODO: log this adjustment once stock_movements.models.StockMovement
        # is wired in (reason/reference/performed_by are collected above but
        # currently go nowhere — see stock_movements app)

        messages.success(request, "Stock adjustment saved.")
        return redirect('inventory_list')

    return render(request, 'inventory/stock_adjustment.html', {'form': form})