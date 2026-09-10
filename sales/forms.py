from django import forms
from django.forms import inlineformset_factory
from .models import Sale, SaleItem


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        # employee is set from the logged-in user in the view, not exposed here;
        # status/total_amount/sale_number are set automatically on save
        fields = ['customer', 'agency', 'payment_method', 'payment_status']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'agency': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].empty_label = "Select customer"
        self.fields['agency'].empty_label = "Select agency"


class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        # subtotal is computed automatically in SaleItem.save()
        fields = ['product', 'quantity', 'unit_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].empty_label = "Select product"
        self.fields['quantity'].required = False
        self.fields['unit_price'].required = False


SaleItemFormSet = inlineformset_factory(
    Sale,
    SaleItem,
    form=SaleItemForm,
    extra=3,
    can_delete=True,
)