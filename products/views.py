from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from accounts.permissions import get_agency_scope, role_required, UNRESTRICTED
from inventory.models import Inventory
from .models import Product, Category
from .forms import ProductForm, CategoryForm


# ---------- Products ----------

def _product_list_context(extra=None, user=None):
    products = Product.objects.select_related('category', 'agency').all()
    if user is not None:
        scope = get_agency_scope(user)
        if scope is None:
            products = products.none()
        elif scope is not UNRESTRICTED:
            products = products.filter(agency=scope)
    context = {
        'products': products,
        'total_products': products.count(),
        'total_categories': Category.objects.count(),
        'form': ProductForm(),
    }
    if extra:
        context.update(extra)
    return context


@login_required
def product_list(request):
    scope = get_agency_scope(request.user)
    if scope is False:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    if scope is None:
        messages.error(request, "Your account isn't assigned to an agency yet.")
    return render(request, 'products/products.html', _product_list_context(user=request.user))


@login_required
def product_detail(request, pk):
    scope = get_agency_scope(request.user)
    if scope is False:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    products = Product.objects.select_related('category', 'agency')
    if scope is not UNRESTRICTED:
        products = products.filter(agency=scope)
    product = get_object_or_404(products, pk=pk)
    inventory = Inventory.objects.filter(product=product)
    if scope is not UNRESTRICTED:
        inventory = inventory.filter(agency=scope)
    return render(request, 'products/product_detail.html', {
        'product': product,
        'inventory': inventory.select_related('agency'),
        'total_stock': sum(item.quantity for item in inventory),
    })


@role_required('CEO')
def product_create(request):
    form = ProductForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('product_list')

    if request.method == 'POST':
        context = _product_list_context({'form': form, 'show_product_modal': True}, request.user)
        return render(request, 'products/products.html', context)

    return redirect('product_list')


@role_required('CEO')
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    if form.is_valid():
        form.save()
        return redirect('product_list')
    return render(request, 'products/product_edit.html', {'form': form, 'product': product})


@role_required('CEO')
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect('product_list')


# ---------- Categories ----------

def _category_list_context(extra=None):
    categories = Category.objects.annotate(product_count=Count('product'))
    context = {
        'categories': categories,
        'total_categories': categories.count(),
        'total_products': Product.objects.count(),
        'form': CategoryForm(),
    }
    if extra:
        context.update(extra)
    return context


@role_required('CEO')
def category_list(request):
    return render(request, 'products/categories.html', _category_list_context())


@role_required('CEO')
def category_create(request):
    form = CategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('category_list')

    if request.method == 'POST':
        context = _category_list_context({'form': form, 'show_category_modal': True})
        return render(request, 'products/categories.html', context)

    return redirect('category_list')


@role_required('CEO')
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=category)
    if form.is_valid():
        form.save()
        return redirect('category_list')
    return render(request, 'products/category_edit.html', {'form': form, 'category': category})


@role_required('CEO')
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    return redirect('category_list')