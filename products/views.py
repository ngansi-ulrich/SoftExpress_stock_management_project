from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from .models import Product, Category
from .forms import ProductForm, CategoryForm


# ---------- Products ----------

def _product_list_context(extra=None):
    products = Product.objects.select_related('category', 'agency').all()
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
    return render(request, 'products/products.html', _product_list_context())


@login_required
def product_create(request):
    form = ProductForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('product_list')

    if request.method == 'POST':
        context = _product_list_context({'form': form, 'show_product_modal': True})
        return render(request, 'products/products.html', context)

    return redirect('product_list')


@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    if form.is_valid():
        form.save()
        return redirect('product_list')
    return render(request, 'products/product_edit.html', {'form': form, 'product': product})


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect('product_list')


@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'products/product_detail.html', {'product': product})


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


@login_required
def category_list(request):
    return render(request, 'products/categories.html', _category_list_context())


@login_required
def category_create(request):
    form = CategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('category_list')

    if request.method == 'POST':
        context = _category_list_context({'form': form, 'show_category_modal': True})
        return render(request, 'products/categories.html', context)

    return redirect('category_list')


@login_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=category)
    if form.is_valid():
        form.save()
        return redirect('category_list')
    return render(request, 'products/category_edit.html', {'form': form, 'category': category})


@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    return redirect('category_list')
