from django.shortcuts import render, redirect, get_object_or_404
from .models import Agency

def agency_list(request):
    agencies = Agency.objects.all()
    return render(request, 'agencies/agencies.html', {'agencies': agencies})

def add_agency(request):
    if request.method == 'POST':
        # Use your Django Form class here for better validation
        Agency.objects.create(
            name=request.POST.get('name'),
            city=request.POST.get('city'),
            address=request.POST.get('address'),
            phone=request.POST.get('phone')
        )
        return redirect('agency_list')
    return redirect('agency_list')

def edit_agency(request, id):
    agency = get_object_or_404(Agency, id=id)
    if request.method == 'POST':
        agency.name = request.POST.get('name')
        agency.city = request.POST.get('city')
        agency.address = request.POST.get('address')
        agency.phone = request.POST.get('phone')
        agency.save()
        return redirect('agency_list')
    return render(request, 'edit_agency.html', {'agency': agency})

def delete_agency(request, id):
    agency = get_object_or_404(Agency, id=id)
    if request.method == 'POST':
        agency.delete()
    return redirect('agency_list')