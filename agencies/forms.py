from django import forms
from .models import Agency


class AgencyForm(forms.ModelForm):
    class Meta:
        model = Agency
        fields = ['name', 'city', 'address', 'phone', 'email', 'manager', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Douala Main Branch'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Douala'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Boulevard de la Liberté'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+237 6xx xxx xxx'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@agency.com'
            }),
            'manager': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.Select(
                choices=[(True, 'Active'), (False, 'Inactive')],
                attrs={'class': 'form-select'}
            ),
        }