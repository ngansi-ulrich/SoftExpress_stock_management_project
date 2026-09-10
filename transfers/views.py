from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from agencies.models import Agency
from accounts.models import Employee
from .models import Transfer
from .forms import TransferForm


def _transfer_list_context(extra=None):
    transfers = Transfer.objects.select_related(
        'source_agency', 'destination_agency', 'product', 'requested_by'
    ).order_by('-created_at')

    context = {
        'transfers': transfers[:10],  # recent only, on the dashboard-style list
        'pending_count': transfers.filter(status='PENDING').count(),
        'approved_count': transfers.filter(status='APPROVED').count(),
        'products_moved': transfers.filter(status='APPROVED').aggregate(
            total=Sum('quantity'))['total'] or 0,
        'agencies_connected': Agency.objects.filter(is_active=True).count(),
        'form': TransferForm(),
    }
    if extra:
        context.update(extra)
    return context


@login_required
def transfer_list(request):
    return render(request, 'transfers/transfers.html', _transfer_list_context())


@login_required
def transfer_create(request):
    form = TransferForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            messages.error(
                request,
                "Your account isn't linked to an Employee record, so a "
                "transfer can't be attributed to you yet."
            )
            return redirect('transfer_list')

        transfer = form.save(commit=False)
        transfer.requested_by = employee
        transfer.save()
        messages.success(request, f"Transfer {transfer.transfer_number} created.")
        return redirect('transfer_list')

    if request.method == 'POST':
        context = _transfer_list_context({'form': form, 'show_transfer_modal': True})
        return render(request, 'transfers/transfers.html', context)

    return redirect('transfer_list')


@login_required
def transfer_detail(request, pk):
    transfer = get_object_or_404(
        Transfer.objects.select_related(
            'source_agency', 'destination_agency', 'product', 'requested_by'
        ),
        pk=pk
    )
    return render(request, 'transfers/transfer_detail.html', {'transfer': transfer})


@login_required
def transfer_approve(request, pk):
    transfer = get_object_or_404(Transfer, pk=pk)
    transfer.status = 'APPROVED'
    transfer.save()
    messages.success(request, f"Transfer {transfer.transfer_number} approved.")
    return redirect('transfer_detail', pk=pk)


@login_required
def transfer_reject(request, pk):
    transfer = get_object_or_404(Transfer, pk=pk)
    transfer.status = 'REJECTED'
    transfer.save()
    messages.success(request, f"Transfer {transfer.transfer_number} rejected.")
    return redirect('transfer_detail', pk=pk)


@login_required
def transfer_history(request):
    transfers = Transfer.objects.select_related(
        'source_agency', 'destination_agency', 'product', 'requested_by'
    ).order_by('-created_at')

    status = request.GET.get('status')
    if status:
        transfers = transfers.filter(status=status)

    context = {
        'transfers': transfers,
        'selected_status': status or '',
    }
    return render(request, 'transfers/transfer_history.html', context)