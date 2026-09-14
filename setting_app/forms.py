from django import forms
from .models import SystemSettings, NotificationPreference


class GeneralSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = [
            'company_name', 'company_email', 'company_phone',
            'company_address', 'company_logo', 'default_language', 'timezone',
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'company_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'company_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'company_logo': forms.FileInput(attrs={'class': 'form-control'}),
            'default_language': forms.Select(attrs={'class': 'form-select'}),
            'timezone': forms.TextInput(attrs={'class': 'form-control'}),
        }


class NotificationPreferenceForm(forms.ModelForm):
    class Meta:
        model = NotificationPreference
        fields = [
            'low_stock_alerts', 'new_sale_notifications',
            'transfer_notifications', 'system_notifications',
            'account_notifications',
        ]
        widgets = {
            field: forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'})
            for field in fields
        }