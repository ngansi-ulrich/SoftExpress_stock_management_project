from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from accounts.models import Employee
from agencies.models import Agency
from .models import Sale, Invoice
from .forms import SaleForm, SaleItemFormSet


@login_required
def sale_list(request):
    sales = Sale.objects.select_related('customer', 'agency', 'employee').order_by('-created_at')

    context = {
        'sales': sales[:20],
        'total_sales': sales.count(),
        'completed_count': sales.filter(status='COMPLETED').count(),
        'draft_count': sales.filter(status='DRAFT').count(),
        'total_revenue': sales.filter(status='COMPLETED').aggregate(
            total=Sum('total_amount'))['total'] or 0,
    }
    return render(request, 'sales/sales.html', context)


@login_required
def sale_create(request):
    if request.method == 'POST':
        sale_form = SaleForm(request.POST)

        if sale_form.is_valid():
            try:
                employee = Employee.objects.get(user=request.user)
            except Employee.DoesNotExist:
                messages.error(
                    request,
                    "Your account isn't linked to an Employee record, so a "
                    "sale can't be attributed to you yet."
                )
                return redirect('sale_list')

            try:
                with transaction.atomic():
                    sale = sale_form.save(commit=False)
                    sale.employee = employee
                    sale.save()  # generates sale_number

                    formset = SaleItemFormSet(request.POST, instance=sale)
                    if not formset.is_valid():
                        raise ValueError("Please correct the errors in the item list below.")

                    items = formset.save(commit=False)
                    if not items and not sale.items.exists():
                        raise ValueError("Add at least one product to the sale.")

                    for item in items:
                        item.save()  # runs SaleItem's own inventory check + decrement

                    for obj in formset.deleted_objects:
                        obj.delete()

                    sale.total_amount = sale.items.aggregate(
                        total=Sum('subtotal'))['total'] or 0
                    sale.status = 'COMPLETED'
                    sale.save()

                    # Auto-generate the Invoice for this sale, same transaction.
                    # get_or_create guards against ever creating a duplicate
                    # invoice for one sale (OneToOneField also enforces this
                    # at the DB level).
                    Invoice.objects.get_or_create(sale=sale)

                messages.success(request, f"Sale {sale.sale_number} completed.")
                return redirect('sale_detail', pk=sale.pk)

            except ValueError as e:
                # transaction.atomic() rolls back the Sale row, any
                # inventory already decremented, and the Invoice if one
                # was created before the failure
                messages.error(request, str(e))
                formset = SaleItemFormSet(request.POST)
        else:
            formset = SaleItemFormSet(request.POST)
    else:
        sale_form = SaleForm()
        formset = SaleItemFormSet()

    return render(request, 'sales/sale_form.html', {
        'sale_form': sale_form,
        'formset': formset,
    })


@login_required
def sale_detail(request, pk):
    sale = get_object_or_404(
        Sale.objects.select_related('customer', 'agency', 'employee'),
        pk=pk
    )
    items = sale.items.select_related('product').all()
    return render(request, 'sales/sale_detail.html', {'sale': sale, 'items': items})


# ---------- Invoices ----------
# Invoice is a thin, auto-generated OneToOne wrapper around a completed
# Sale (see sale_create above and the Invoice model). CEO/Admin sees
# invoices from every agency — no agency filtering applied by default,
# only when the person explicitly picks one from the filter dropdown.

@login_required
def invoice_list(request):
    invoices = Invoice.objects.select_related(
        'sale', 'sale__customer', 'sale__agency', 'sale__employee'
    ).order_by('-issued_at')

    agency_id = request.GET.get('agency')
    payment_status = request.GET.get('payment_status')
    date = request.GET.get('date')
    query = request.GET.get('q')

    if agency_id:
        invoices = invoices.filter(sale__agency_id=agency_id)
    if payment_status:
        invoices = invoices.filter(sale__payment_status=payment_status)
    if date:
        invoices = invoices.filter(issued_at__date=date)
    if query:
        invoices = invoices.filter(
            invoice_number__icontains=query
        ) | invoices.filter(
            sale__customer__first_name__icontains=query
        ) | invoices.filter(
            sale__customer__last_name__icontains=query
        ) | invoices.filter(
            sale__customer__phone__icontains=query
        )

    context = {
        'invoices': invoices,
        'total_count': invoices.count(),
        'paid_count': invoices.filter(sale__payment_status='PAID').count(),
        'partial_count': invoices.filter(sale__payment_status='PARTIAL').count(),
        'pending_count': invoices.filter(sale__payment_status='PENDING').count(),
        'total_amount': invoices.aggregate(
            total=Sum('sale__total_amount'))['total'] or 0,
        'paid_amount': invoices.filter(sale__payment_status='PAID').aggregate(
            total=Sum('sale__total_amount'))['total'] or 0,
        'pending_amount': invoices.filter(
            sale__payment_status__in=['PARTIAL', 'PENDING']
        ).aggregate(total=Sum('sale__total_amount'))['total'] or 0,
        'agencies': Agency.objects.filter(is_active=True),
        'selected_agency': agency_id or '',
        'selected_payment_status': payment_status or '',
        'selected_date': date or '',
        'query': query or '',
    }
    return render(request, 'sales/invoices.html', context)


def _invoice_detail_context(invoice):
    sale = invoice.sale
    items = sale.items.select_related('product').all()
    # NOTE: Sale has no amount_paid field, only a payment_status choice
    # (PAID/PARTIAL/PENDING) — so an exact balance can only be computed
    # for the PAID (balance=0) and PENDING (balance=full total) cases.
    # For PARTIAL, the actual amount paid isn't tracked anywhere yet, so
    # we say so honestly instead of guessing a number. Add an
    # amount_paid field to Sale if you want a real partial-balance figure.
    if sale.payment_status == 'PAID':
        balance = 0
        balance_known = True
    elif sale.payment_status == 'PENDING':
        balance = sale.total_amount
        balance_known = True
    else:
        balance = None
        balance_known = False
    return {
        'invoice': invoice,
        'sale': sale,
        'items': items,
        'balance': balance,
        'balance_known': balance_known,
    }


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related('sale', 'sale__customer', 'sale__agency', 'sale__employee'),
        pk=pk
    )
    return render(request, 'sales/invoice_detail.html', _invoice_detail_context(invoice))


@login_required
def invoice_print(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related('sale', 'sale__customer', 'sale__agency', 'sale__employee'),
        pk=pk
    )
    context = _invoice_detail_context(invoice)
    context['auto_print'] = True
    return render(request, 'sales/invoice_detail.html', context)


@login_required
def invoice_pdf(request, pk):
    # PDF generation needs a rendering library that isn't confirmed
    # installed in this project yet (e.g. xhtml2pdf or WeasyPrint).
    # See the message accompanying this code for what to check/install
    # before this view can be finished.
    from django.http import HttpResponse
    return HttpResponse(
        "PDF export isn't wired up yet — see chat for what needs to be "
        "installed first.",
        status=501
    )