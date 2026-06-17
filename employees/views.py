from django.shortcuts import render
from django.shortcuts import get_object_or_404
from agencies.models import Agency
from accounts.models import Employee
from .forms import EmployeeForm
from django.shortcuts import redirect


def employee_list(request):

    employees = Employee.objects.all()

    context = {
        "employees": employees,
        "douala_count": Employee.objects.filter(
            agency__name__icontains="Douala"
        ).count(),

        "yaounde_count": Employee.objects.filter(
            agency__name__icontains="Yaounde"
        ).count(),

        "bafoussam_count": Employee.objects.filter(
            agency__name__icontains="Bafoussam"
        ).count(),
    }

    return render(
        request,
        "employees/employees.html",
        context
    )
    
def add_employee(request):

    if request.method == "POST":

        form = EmployeeForm(request.POST)

        if form.is_valid():

            form.save()

            return redirect(
                "employee_list"
            )

    else:

        form = EmployeeForm()

    return render(
        request,
        "employees/employees.html",
        {
            "form": form
        }
    )
    
def employee_edit(request, id):

    employee = get_object_or_404(
        Employee,
        id=id
    )

    if request.method == "POST":

        form = EmployeeForm(
            request.POST,
            instance=employee
        )

        if form.is_valid():

            form.save()

            return redirect(
                'employee_list'
            )

    else:

        form = EmployeeForm(
            instance=employee
        )

    return render(
        request,
        'employees/employees.html',
        {
            'form': form
        }
    )
    
def employee_delete(request, id):

    employee = get_object_or_404(
        Employee,
        id=id
    )

    employee.delete()

    return redirect(
        'employee_list'
    )