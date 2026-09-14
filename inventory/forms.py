from django import forms
from agencies.models import Agency
from products.models import Product
from accounts.models import Employee

ADJUSTMENT_TYPES = [
    ('add', 'Add Stock'),
    ('remove', 'Remove Stock'),
    ('correction', 'Correction'),
]


class StockAdjustmentForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    agency = forms.ModelChoiceField(
        queryset=Agency.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    adjustment_type = forms.ChoiceField(
        choices=ADJUSTMENT_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter quantity'})
    )
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Example: New supplier delivery'
        })
    )
    reference = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PO-2026-001'})
    )
    performed_by = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].empty_label = "Select product"
        self.fields['agency'].empty_label = "Select agency"
        self.fields['performed_by'].empty_label = "Select employee"