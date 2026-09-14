from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db import transaction
from django.db.models import F
from accounts.permissions import get_agency_scope, get_employee, UNRESTRICTED
from accounts.permissions import role_required
from stock_movements.models import StockMovement
from .models import Inventory
from .forms import StockAdjustmentForm


@login_required
def inventory_list(request):
    """
    Display inventory according to the user's agency scope.

    CEO/Admin:
        Can see inventory across all agencies.

    Manager/Staff:
        Can only see inventory belonging to their assigned agency.
    """
    scope = get_agency_scope(request.user)

    if scope is False:
        raise PermissionDenied

    if scope is None:
        messages.error(
            request,
            "Your account isn't assigned to an agency yet."
        )

        return render(
            request,
            'inventory/inventory_list.html',
            {
                'inventory': Inventory.objects.none(),
                'inventory_items': Inventory.objects.none(),
            }
        )

    if scope is UNRESTRICTED:
        inventory_items = (
            Inventory.objects
            .select_related('product', 'agency')
            .all()
        )
    else:
        inventory_items = (
            Inventory.objects
            .select_related('product', 'agency')
            .filter(agency=scope)
        )

    inventory_items = inventory_items.order_by('product__name')

    return render(
        request,
        'inventory/inventory_list.html',
        {
            'inventory': inventory_items,
            'inventory_items': inventory_items,
        }
    )


@login_required
def stock_alerts(request):
    """
    Display low-stock products.

    CEO/Admin:
        Can see low-stock items across all agencies.

    Manager/Staff:
        Can only see low-stock items from their assigned agency.
    """
    scope = get_agency_scope(request.user)

    if scope is False:
        raise PermissionDenied

    if scope is None:
        messages.error(
            request,
            "Your account isn't assigned to an agency yet."
        )

        return render(
            request,
            'inventory/stock_alerts.html',
            {
                'alerts': Inventory.objects.none(),
                'low_stock_items': Inventory.objects.none(),
            }
        )

    inventory_items = Inventory.objects.filter(
        quantity__lte=F('minimum_stock'))

    # Apply agency-level security.
    if scope is not UNRESTRICTED:
        inventory_items = inventory_items.filter(
            agency=scope
        )

    inventory_items = (
        inventory_items
        .select_related('product', 'agency')
        .order_by('quantity', 'product__name')
    )

    return render(
        request,
        'inventory/stock_alerts.html',
        {
            'alerts': inventory_items,
            'low_stock_items': inventory_items,
        }
    )


@role_required('CEO', 'MANAGER')
def stock_adjustment(request):
    scope = get_agency_scope(request.user)

    if scope is False:
        raise PermissionDenied

    if scope is None:
        messages.error(
            request,
            "Your account isn't assigned to an agency yet — adjustments aren't possible."
        )
        return redirect('inventory_list')

    form = StockAdjustmentForm(request.POST or None)

    if scope is not UNRESTRICTED:
        form.fields['agency'].queryset = (
            form.fields['agency']
            .queryset
            .filter(pk=scope.pk)
        )
        form.fields['agency'].initial = scope
        form.fields['agency'].disabled = True

    if request.method == 'POST' and form.is_valid():

        product = form.cleaned_data['product']

        agency = (
            scope
            if scope is not UNRESTRICTED
            else form.cleaned_data['agency']
        )

        adjustment_type = form.cleaned_data['adjustment_type']
        quantity = form.cleaned_data['quantity']

        # PATCHED: wrapped in a transaction with row locking.
        #
        # - transaction.atomic() ties the Inventory save and the
        #   StockMovement create together — if the movement log fails
        #   to write, the quantity change rolls back too, so the two
        #   can never drift out of sync.
        # - select_for_update() locks the Inventory row (once it
        #   exists) for the duration of the transaction, so two
        #   concurrent adjustments to the same product+agency can't
        #   both read the same "before" value and have one silently
        #   overwrite the other.
        with transaction.atomic():
            inventory, created = Inventory.objects.get_or_create(
                product=product,
                agency=agency
            )
            if not created:
                # get_or_create() already inserted+committed the row
                # in this transaction if it was just created, so a
                # fresh locked read is only needed for the pre-existing
                # case — locking a row you just created yourself in
                # the same transaction is a no-op anyway, but this
                # avoids an unnecessary extra query on first-time rows.
                inventory = Inventory.objects.select_for_update().get(
                    pk=inventory.pk
                )

            before = inventory.quantity

            if adjustment_type == 'add':
                inventory.quantity += quantity

            elif adjustment_type == 'remove':
                inventory.quantity = max(
                    0,
                    inventory.quantity - quantity
                )

            elif adjustment_type == 'correction':
                inventory.quantity = quantity

            inventory.save()

            # Calculate the real stock movement.
            delta = inventory.quantity - before

            if delta == 0:
                movement_type = None
            elif delta > 0:
                movement_type = 'IN'
            else:
                movement_type = 'OUT'

            if movement_type:
                StockMovement.objects.create(
                    inventory=inventory,
                    movement_type=movement_type,
                    quantity=abs(delta),
                    employee=get_employee(request.user),
                )

        messages.success(
            request,
            "Stock adjustment saved."
        )

        return redirect('inventory_list')

    return render(
        request,
        'inventory/stock_adjustment.html',
        {'form': form}
    )