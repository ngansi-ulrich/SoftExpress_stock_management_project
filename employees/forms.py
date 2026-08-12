from django import forms
from accounts.models import Employee
from agencies.models import Agency


class EmployeeForm(forms.ModelForm):

    class Meta:
        model = Employee

        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'role',
            'agency'
        ]

        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Jean'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Mballa'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'employee@softexpress.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+237 6xx xxx xxx'
            }),
            'role': forms.Select(attrs={
                'class': 'form-select'
            }),
            'agency': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # only let active agencies be assigned
        self.fields['agency'].queryset = Agency.objects.filter(is_active=True)
        self.fields['agency'].empty_label = "Select agency"