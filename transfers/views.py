from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q
from agencies.models import Agency
from accounts.models import Employee
from accounts.permissions import get_agency_scope, get_employee, role_required, UNRESTRICTED
from inventory.models import Inventory
from stock_movements.models import StockMovement
from .models import Transfer
from .forms import TransferForm


def _involves_agency(scope):
    return Q(source_agency=scope) | Q(destination_agency=scope)


def _empty_list_context():
    return {
        'transfers': Transfer.objects.none(), 'pending_count': 0,
        'approved_count': 0, 'products_moved': 0, 'agencies_connected': 0,
    }


def _transfer_list_context(request, extra=None):
    scope = get_agency_scope(request.user)
    if scope is False:
        raise PermissionDenied

    transfers = Transfer.objects.select_related(
        'source_agency', 'destination_agency', 'product', 'requested_by'
    ).order_by('-created_at')

    if scope is None:
        context = _empty_list_context()
        context['form'] = TransferForm()
        context['no_agency'] = True
    elif scope is not UNRESTRICTED:
        transfers = transfers.filter(_involves_agency(scope))
        context = {
            'transfers': transfers[:10],
            'pending_count': transfers.filter(status='PENDING').count(),
            'approved_count': transfers.filter(status='APPROVED').count(),
            'products_moved': transfers.filter(status='APPROVED').aggregate(
                total=Sum('quantity'))['total'] or 0,
            'agencies_connected': 1 if scope.is_active else 0,
            'form': TransferForm(),
        }
    else:
        context = {
            'transfers': transfers[:10],
            'pending_count': transfers.filter(status='PENDING').count(),
            'approved_count': transfers.filter(status='APPROVED').count(),
            'products_moved': transfers.filter(status='APPROVED').aggregate(
                total=Sum('quantity'))['total'] or 0,
            'agencies_connected': Agency.objects.filter(is_active=True).count(),
            'form': TransferForm(),
        }

    if extra:
        context.update(extra)
    return context, scope


@role_required('CEO', 'MANAGER')
def transfer_list(request):
    context, _ = _transfer_list_context(request)
    return render(request, 'transfers/transfers.html', context)


@role_required('CEO', 'MANAGER')
def transfer_create(request):
    scope = get_agency_scope(request.user)
    if scope is False:
        raise PermissionDenied
    if scope is None:
        messages.error(request, "Your account isn't assigned to an agency yet.")
        return redirect('transfer_list')

    form = TransferForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        employee = get_employee(request.user)
        if employee is None:
            messages.error(
                request,
                "Your account isn't linked to an Employee record, so a "
                "transfer can't be attributed to you yet."
            )
            return redirect('transfer_list')

        source = form.cleaned_data['source_agency']
        destination = form.cleaned_data['destination_agency']

        if scope is not UNRESTRICTED and scope not in (source, destination):
            messages.error(
                request,
                f"You can only create transfers involving {scope.name} — "
                f"either as the source or the destination."
            )
            return render(request, 'transfers/transfers.html', {
                **_transfer_list_context(request)[0],
                'form': form,
                'show_transfer_modal': True,
            })

        transfer = form.save(commit=False)
        transfer.requested_by = employee
        transfer.save()
        messages.success(request, f"Transfer {transfer.transfer_number} created — awaiting approval.")
        return redirect('transfer_list')

    if request.method == 'POST':
        context, _ = _transfer_list_context(request, {'form': form, 'show_transfer_modal': True})
        return render(request, 'transfers/transfers.html', context)

    return redirect('transfer_list')


@role_required('CEO', 'MANAGER')
def transfer_detail(request, pk):
    scope = get_agency_scope(request.user)
    if scope is False:
        raise PermissionDenied

    qs = Transfer.objects.select_related('source_agency', 'destination_agency', 'product', 'requested_by')
    if scope is UNRESTRICTED:
        transfer = get_object_or_404(qs, pk=pk)
    else:
        transfer = get_object_or_404(qs.filter(_involves_agency(scope)), pk=pk)

    return render(request, 'transfers/transfer_detail.html', {'transfer': transfer})


def _get_scoped_transfer_for_action(request, pk):
    scope = get_agency_scope(request.user)
    if scope is False:
        raise PermissionDenied
    if scope is UNRESTRICTED:
        return get_object_or_404(Transfer, pk=pk)
    return get_object_or_404(Transfer.objects.filter(_involves_agency(scope)), pk=pk)


@role_required('CEO', 'MANAGER')
def transfer_approve(request, pk):
    transfer = _get_scoped_transfer_for_action(request, pk)

    if transfer.status != 'PENDING':
        messages.error(request, f"Transfer {transfer.transfer_number} has already been {transfer.get_status_display().lower()}.")
        return redirect('transfer_detail', pk=pk)

    try:
        with transaction.atomic():
            try:
                source_inventory = Inventory.objects.select_for_update().get(
                    agency=transfer.source_agency, product=transfer.product
                )
            except Inventory.DoesNotExist:
                raise ValueError(
                    f"{transfer.source_agency.name} has no recorded stock of "
                    f"{transfer.product.name} to transfer."
                )

            if source_inventory.quantity < transfer.quantity:
                raise ValueError(
                    f"Insufficient stock at {transfer.source_agency.name}: "
                    f"available {source_inventory.quantity}, requested {transfer.quantity}."
                )

            source_inventory.quantity -= transfer.quantity
            source_inventory.save()

            destination_inventory, _ = Inventory.objects.get_or_create(
                agency=transfer.destination_agency, product=transfer.product
            )
            destination_inventory.quantity += transfer.quantity
            destination_inventory.save()

            performer = get_employee(request.user)

            StockMovement.objects.create(
                inventory=source_inventory,
                movement_type='TRANSFER',
                quantity=transfer.quantity,
                employee=performer,
            )
            StockMovement.objects.create(
                inventory=destination_inventory,
                movement_type='TRANSFER',
                quantity=transfer.quantity,
                employee=performer,
            )

            transfer.status = 'APPROVED'
            transfer.save()

        messages.success(
            request,
            f"Transfer {transfer.transfer_number} approved — stock moved from "
            f"{transfer.source_agency.name} to {transfer.destination_agency.name}."
        )
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('transfer_detail', pk=pk)


@role_required('CEO', 'MANAGER')
def transfer_reject(request, pk):
    transfer = _get_scoped_transfer_for_action(request, pk)

    if transfer.status != 'PENDING':
        messages.error(request, f"Transfer {transfer.transfer_number} has already been {transfer.get_status_display().lower()}.")
        return redirect('transfer_detail', pk=pk)

    transfer.status = 'REJECTED'
    transfer.save()
    messages.success(request, f"Transfer {transfer.transfer_number} rejected. No stock was moved.")
    return redirect('transfer_detail', pk=pk)


@role_required('CEO', 'MANAGER')
def transfer_history(request):
    scope = get_agency_scope(request.user)
    if scope is False:
        raise PermissionDenied

    transfers = Transfer.objects.select_related(
        'source_agency', 'destination_agency', 'product', 'requested_by'
    ).order_by('-created_at')

    if scope is None:
        transfers = Transfer.objects.none()
    elif scope is not UNRESTRICTED:
        transfers = transfers.filter(_involves_agency(scope))

    status = request.GET.get('status')
    if status:
        transfers = transfers.filter(status=status)

    return render(request, 'transfers/transfer_history.html', {
        'transfers': transfers,
        'selected_status': status or '',
    })