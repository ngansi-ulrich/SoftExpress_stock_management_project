from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from .models import Agency
from .forms import AgencyForm

@login_required
def agency_list(request):
    agencies = Agency.objects.annotate(employee_count=Count('employee')).all()
    active_agencies_count = agencies.filter(is_active=True).count()
    
    # Simple aggregations
    context = {
        'agencies': agencies,
        'active_agencies_count': active_agencies_count,
        'total_employees': sum(a.employee_count for a in agencies),
    }
    return render(request, 'agency_list.html', context)

@login_required
def agency_create(request):
    form = AgencyForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('agency_list')
    return render(request, 'agency_form.html', {'form': form})

@login_required
def agency_update(request, pk):
    agency = get_object_or_404(Agency, pk=pk)
    form = AgencyForm(request.POST or None, instance=agency)
    if form.is_valid():
        form.save()
        return redirect('agency_list')
    return render(request, 'agency_form.html', {'form': form})

@login_required
def agency_delete(request, pk):
    agency = get_object_or_404(Agency, pk=pk)
    agency.delete()
    return redirect('agency_list')