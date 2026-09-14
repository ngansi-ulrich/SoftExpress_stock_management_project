from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db.models import Count
from accounts.models import Employee
from accounts.permissions import get_agency_scope, is_ceo, role_required, UNRESTRICTED
from agencies.models import Agency
from .forms import EmployeeForm


@role_required('CEO', 'MANAGER')
def employee_list(request):

    scope = get_agency_scope(request.user)
    if scope is False:
        raise PermissionDenied

    if scope is None:
        # authenticated Manager/Staff with no agency assigned — never
        # fall back to showing everyone's employees
        messages.error(request, "Your account isn't assigned to an agency yet.")
        return render(request, 'employees/employees.html', {
            'employees': Employee.objects.none(),
            'douala_count': 0, 'yaounde_count': 0, 'bafoussam_count': 0,
        })

    employees = Employee.objects.select_related('agency').all()
    if scope is not UNRESTRICTED:
        employees = employees.filter(agency=scope)

    # Real per-agency breakdown instead of hardcoded city-name filters —
    # works for however many agencies actually exist, not just 3 fixed ones
    agency_breakdown = (
        Agency.objects.filter(is_active=True)
        .annotate(employee_count=Count('employee'))
    )

    context = {
        "employees": employees,
        "agency_breakdown": agency_breakdown,
        "total_employees": employees.count(),
        "is_ceo_viewing": is_ceo(request.user),
    }

    return render(
        request,
        "employees/employees.html",
        context
    )


@role_required('CEO', 'MANAGER')
def add_employee(request):
    scope = get_agency_scope(request.user)
    if scope is False:
        raise PermissionDenied

    if request.method == "POST":

        form = EmployeeForm(request.POST)

        if form.is_valid():
            employee = form.save(commit=False)

            # A Manager can only ever create employees for their OWN
            # agency — the agency is forced server-side, never trusted
            # from POST data, regardless of what the form submitted
            if scope is not UNRESTRICTED:
                employee.agency = scope

            employee.save()

            return redirect(
                "employee_list"
            )

    else:

        form = EmployeeForm()
        # Managers don't get to pick an agency at all — there's only one
        # valid choice, so don't even present the option
        if scope is not UNRESTRICTED:
            form.fields['agency'].queryset = form.fields['agency'].queryset.filter(pk=scope.pk)
            form.fields['agency'].initial = scope
            form.fields['agency'].disabled = True

    return render(
        request,
        "employees/add_employee.html",
        {
            "form": form
        }
    )


@role_required('CEO', 'MANAGER')
def employee_edit(request, id):
    scope = get_agency_scope(request.user)
    if scope is False:
        raise PermissionDenied

    # Fetch scoped to the requester's agency directly in the query —
    # this is what actually stops URL manipulation (/employees/edit/7/
    # for an employee in another agency raises 404, not a data leak)
    if scope is UNRESTRICTED:
        employee = get_object_or_404(Employee, id=id)
    else:
        employee = get_object_or_404(Employee, id=id, agency=scope)

    if request.method == "POST":

        form = EmployeeForm(
            request.POST,
            instance=employee
        )

        if form.is_valid():
            updated = form.save(commit=False)
            if scope is not UNRESTRICTED:
                updated.agency = scope  # can't be moved out of the manager's agency
            updated.save()

            return redirect(
                'employee_list'
            )

    else:

        form = EmployeeForm(
            instance=employee
        )
        if scope is not UNRESTRICTED:
            form.fields['agency'].queryset = form.fields['agency'].queryset.filter(pk=scope.pk)
            form.fields['agency'].disabled = True

    return render(
        request,
        'employees/edit_employee.html',
        {
            'form': form
        }
    )


@role_required('CEO', 'MANAGER')
def employee_delete(request, id):
    scope = get_agency_scope(request.user)
    if scope is False:
        raise PermissionDenied

    if scope is UNRESTRICTED:
        employee = get_object_or_404(Employee, id=id)
    else:
        employee = get_object_or_404(Employee, id=id, agency=scope)

    employee.delete()

    return redirect(
        'employee_list'
    )