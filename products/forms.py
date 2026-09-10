from django import forms
from .models import Product, Category


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Example: Laptops'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe this category'
            }),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        # product_code is auto-generated in Product.save(), never user-entered
        fields = [
            'name', 'category', 'brand', 'model',
            'selling_price', 'agency', 'requires_serial_tracking',
            'description',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: HP EliteBook 840 G8'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'brand': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: HP'
            }),
            'model': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 840 G8'
            }),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'agency': forms.Select(attrs={'class': 'form-select'}),
            'requires_serial_tracking': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe this product'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['agency'].empty_label = "Select agency"
