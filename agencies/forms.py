from django import forms
from .models import Agency

class AgencyForm(forms.ModelForm):
    class Meta:
        model = Agency
        fields = ['name', 'city', 'address', 'phone', 'email', 'manager', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ex: Douala Main Branch'}),
            'city': forms.TextInput(attrs={'placeholder': 'Ex: Douala'}),
            'address': forms.TextInput(attrs={'placeholder': 'Ex: Boulevard de la Liberté'}),
            'phone': forms.TextInput(attrs={'placeholder': '+237 6xx xxx xxx'}),
            'email': forms.EmailInput(attrs={'placeholder': 'contact@agency.com'}),
            'manager': forms.Select(),
        }