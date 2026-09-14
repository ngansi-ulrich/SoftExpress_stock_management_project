from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.db.models import Q
from inventory.models import Inventory
from products.models import Product
from customers.models import Customer
from accounts.models import Employee
from accounts.permissions import get_agency_scope, get_employee, role_required, is_staff_role, is_ceo, UNRESTRICTED
from agencies.models import Agency
from .models import Sale, Invoice
from .forms import SaleForm, SaleItemFormSet


@role_required('CEO', 'MANAGER', 'STAFF')
def sale_list(request):
    scope = get_agency_scope(request.user)
    if scope is False:
        raise PermissionDenied
    if scope is None:
        messages.error(request, "Your account isn't assigned to an agency yet.")
        return render(request, 'sales/sales.html', {
            'sales': Sale.objects.none(), 'total_sales': 0, 'completed_count': 0,
            'draft_count': 0, 'total_revenue': 0,
        })

    sales = Sale.objects.select_related('customer', 'agency', 'employee').order_by('-created_at')
    if scope is not UNRESTRICTED:
        sales = sales.filter(agency=scope)
    if is_staff_role(request.user):
        sales = sales.filter(employee=get_employee(request.user))

    context = {
        'sales': sales[:20],
        'total_sales': sales.count(),
        'completed_count': sales.filter(status='COMPLETED').count(),
        'draft_count': sales.filter(status='DRAFT').count(),
        'total_revenue': sales.filter(status='COMPLETED').aggregate(
            total=Sum('total_amount'))['total'] or 0,
    }
    return render(request, 'sales/sales.html', context)


@role_required('CEO', 'MANAGER', 'STAFF')
def sale_create(request):
    scope = get_agency_scope(request.user)
    if scope is False:
        raise PermissionDenied
    if scope is None:
        messages.error(request, "Your account isn't assigned to an agency yet — sales aren't possible.")
        return redirect('sale_list')

    customers = Customer.objects.all()
    products = Product.objects.all()
    if scope is not UNRESTRICTED:
        customers = customers.filter(Q(agency=scope) | Q(sale__agency=scope)).distinct()
        products = products.filter(inventory__agency=scope).distinct()
    sale_form = SaleForm(request.POST or None, customer_queryset=customers)

    if scope is not UNRESTRICTED:
        # same double-protection pattern as Inventory/Employees: disabled
        # field ignores tampered POST data, AND the view overrides
        # cleaned_data explicitly below — neither depends on the other
        sale_form.fields['agency'].queryset = sale_form.fields['agency'].queryset.filter(pk=scope.pk)
        sale_form.fields['agency'].initial = scope
        sale_form.fields['agency'].disabled = True

    if request.method == 'POST':
        if sale_form.is_valid():
            employee = get_employee(request.user)
            if employee is None:
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
                    if scope is not UNRESTRICTED:
                        sale.agency = scope  # never trust cleaned_data here for non-CEO
                    sale.save()  # generates sale_number

                    formset = SaleItemFormSet(
                        request.POST,
                        instance=sale,
                        form_kwargs={'product_queryset': products}
                    )
                    if not formset.is_valid():
                        raise ValueError("Please correct the errors in the item list below.")

                    items = formset.save(commit=False)
                    if not items and not sale.items.exists():
                        raise ValueError("Add at least one product to the sale.")

                    for item in items:
                        if is_staff_role(request.user):
                            item.unit_price = item.product.selling_price
                        inventory = Inventory.objects.select_for_update().filter(
                            agency=sale.agency,
                            product=item.product,
                        ).first()
                        if inventory is None or item.quantity > inventory.quantity:
                            available = inventory.quantity if inventory else 0
                            raise ValueError(
                                f"Insufficient stock for {item.product.name}. Available: {available}"
                            )
                        item.save()  # runs SaleItem's own inventory check + decrement,
                        # scoped correctly for free since sale.agency is now forced above

                    for obj in formset.deleted_objects:
                        obj.delete()

                    sale.total_amount = sale.items.aggregate(
                        total=Sum('subtotal'))['total'] or 0
                    sale.status = 'COMPLETED'
                    sale.save()

                    Invoice.objects.get_or_create(sale=sale)

                messages.success(request, f"Sale {sale.sale_number} completed.")
                return redirect('sale_detail', pk=sale.pk)

            except ValueError as e:
                messages.error(request, str(e))
                formset = SaleItemFormSet(request.POST)
        else:
                formset = SaleItemFormSet(
                    request.POST,
                    form_kwargs={'product_queryset': products}
                )
    else:
        formset = SaleItemFormSet(form_kwargs={'product_queryset': products})

    return render(request, 'sales/sale_form.html', {
        'sale_form': sale_form,
        'formset': formset,
    })


@role_required('CEO', 'MANAGER', 'STAFF')
def sale_detail(request, pk):
    scope = get_agency_scope(request.user)
    if scope is False:
        raise PermissionDenied

    qs = Sale.objects.select_related('customer', 'agency', 'employee')
    if scope is UNRESTRICTED:
        sale = get_object_or_404(qs, pk=pk)
    else:
        # scoped directly in the query — a manipulated URL for another
        # agency's sale returns 404, not a data leak
        sale = get_object_or_404(qs, pk=pk, agency=scope)
    if is_staff_role(request.user) and sale.employee_id != get_employee(request.user).pk:
        raise PermissionDenied

    items = sale.items.select_related('product').all()
    return render(request, 'sales/sale_detail.html', {'sale': sale, 'items': items})


# ---------- Invoices ----------

@role_required('CEO', 'MANAGER', 'STAFF')
def invoice_list(request):
    scope = get_agency_scope(request.user)
    if scope is False:
        raise PermissionDenied
    if scope is None:
        messages.error(request, "Your account isn't assigned to an agency yet.")
        return render(request, 'sales/invoices.html', {
            'invoices': Invoice.objects.none(), 'total_count': 0, 'paid_count': 0,
            'partial_count': 0, 'pending_count': 0, 'total_amount': 0,
            'paid_amount': 0, 'pending_amount': 0, 'agencies': Agency.objects.none(),
            'selected_agency': '', 'selected_payment_status': '', 'selected_date': '', 'query': '',
        })

    invoices = Invoice.objects.select_related(
        'sale', 'sale__customer', 'sale__agency', 'sale__employee'
    ).order_by('-issued_at')

    if scope is not UNRESTRICTED:
        # Manager's agency filter is forced — the agency GET param is
        # simply ignored for non-CEO rather than trusted
        invoices = invoices.filter(sale__agency=scope)
        agency_id = None
    if is_staff_role(request.user):
        invoices = invoices.filter(sale__employee=get_employee(request.user))
    else:
        agency_id = request.GET.get('agency')
        if agency_id:
            invoices = invoices.filter(sale__agency_id=agency_id)

    payment_status = request.GET.get('payment_status')
    date = request.GET.get('date')
    query = request.GET.get('q')

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
        'total_amount': invoices.aggregate(total=Sum('sale__total_amount'))['total'] or 0,
        'paid_amount': invoices.filter(sale__payment_status='PAID').aggregate(
            total=Sum('sale__total_amount'))['total'] or 0,
        'pending_amount': invoices.filter(
            sale__payment_status__in=['PARTIAL', 'PENDING']
        ).aggregate(total=Sum('sale__total_amount'))['total'] or 0,
        'agencies': Agency.objects.filter(is_active=True) if scope is UNRESTRICTED else Agency.objects.none(),
        'selected_agency': agency_id or '',
        'selected_payment_status': payment_status or '',
        'selected_date': date or '',
        'query': query or '',
    }
    return render(request, 'sales/invoices.html', context)


def _get_scoped_invoice_or_404(request, pk):
    scope = get_agency_scope(request.user)
    if scope is False:
        raise PermissionDenied
    qs = Invoice.objects.select_related('sale', 'sale__customer', 'sale__agency', 'sale__employee')
    if scope is UNRESTRICTED:
        invoice = get_object_or_404(qs, pk=pk)
    else:
        invoice = get_object_or_404(qs, pk=pk, sale__agency=scope)
    if is_staff_role(request.user) and invoice.sale.employee_id != get_employee(request.user).pk:
        raise PermissionDenied
    return invoice


def _invoice_detail_context(invoice):
    sale = invoice.sale
    items = sale.items.select_related('product').all()
    if sale.payment_status == 'PAID':
        balance, balance_known = 0, True
    elif sale.payment_status == 'PENDING':
        balance, balance_known = sale.total_amount, True
    else:
        balance, balance_known = None, False
    return {
        'invoice': invoice, 'sale': sale, 'items': items,
        'balance': balance, 'balance_known': balance_known,
    }


@login_required
def invoice_detail(request, pk):
    invoice = _get_scoped_invoice_or_404(request, pk)
    return render(request, 'sales/invoice_detail.html', _invoice_detail_context(invoice))


@login_required
def invoice_print(request, pk):
    invoice = _get_scoped_invoice_or_404(request, pk)
    context = _invoice_detail_context(invoice)
    context['auto_print'] = True
    return render(request, 'sales/invoice_detail.html', context)


@login_required
def invoice_pdf(request, pk):
    invoice = _get_scoped_invoice_or_404(request, pk)
    context = _invoice_detail_context(invoice)

    from django.template.loader import render_to_string
    from django.http import HttpResponse
    from xhtml2pdf import pisa
    from io import BytesIO

    html = render_to_string('sales/invoice_pdf.html', context)
    result = BytesIO()
    pdf = pisa.CreatePDF(html, dest=result)

    if pdf.err:
        return HttpResponse('There was an error generating the PDF.', status=500)

    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.pdf"'
    return response