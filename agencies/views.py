from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from accounts.models import Employee
from .models import Agency
from .forms import AgencyForm


def _agency_list_context(extra=None):
    agencies = Agency.objects.annotate(employee_count=Count('employee')).all()
    active_agencies_count = agencies.filter(is_active=True).count()

    context = {
        'agencies': agencies,
        'active_agencies_count': active_agencies_count,
        'total_employees': sum(a.employee_count for a in agencies),
        'form': AgencyForm(),
    }
    if extra:
        context.update(extra)
    return context


@login_required
def agency_list(request):
    return render(request, 'agencies/agencies.html', _agency_list_context())


@login_required
def agency_create(request):
    form = AgencyForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('agency_list')

    if request.method == 'POST':
        # invalid submission: re-render the full list page with the
        # modal forced open and errors shown, instead of a bare fragment
        context = _agency_list_context({'form': form, 'show_agency_modal': True})
        return render(request, 'agencies/agencies.html', context)

    return redirect('agency_list')


@login_required
def agency_update(request, pk):
    agency = get_object_or_404(Agency, pk=pk)
    form = AgencyForm(request.POST or None, instance=agency)
    if form.is_valid():
        form.save()
        return redirect('agency_list')
    return render(request, 'agencies/agency_edit.html', {'form': form, 'agency': agency})


@login_required
def agency_delete(request, pk):
    agency = get_object_or_404(Agency, pk=pk)
    agency.delete()
    return redirect('agency_list')


@login_required
def agency_detail(request, pk):
    agency = get_object_or_404(
        Agency.objects.annotate(employee_count=Count('employee')),
        pk=pk
    )
    employees = Employee.objects.filter(agency=agency)

    context = {
        'agency': agency,
        'employees': employees,
    }
    return render(request, 'agencies/agency_detail.html', context)