from django import forms
from .models import Supplier


class SupplierForm(forms.ModelForm):

    class Meta:
        model = Supplier

        fields = [
            'name',
            'contact_person',
            'phone',
            'email',
            'city',
            'address',
            'is_active',
        ]

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Tech Supplier Ltd'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Jean Mballa'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+237 6xx xxx xxx'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@supplier.com'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Douala'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Boulevard de la Liberté'
            }),
            'is_active': forms.Select(
                choices=[(True, 'Active'), (False, 'Inactive')],
                attrs={'class': 'form-select'}
            ),
        }