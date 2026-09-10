from django import forms
from .models import Transfer


class TransferForm(forms.ModelForm):
    class Meta:
        model = Transfer
        # requested_by is set automatically from the logged-in user in the
        # view, not exposed as a field — status defaults to PENDING
        fields = ['source_agency', 'destination_agency', 'product', 'quantity']
        widgets = {
            'source_agency': forms.Select(attrs={'class': 'form-select'}),
            'destination_agency': forms.Select(attrs={'class': 'form-select'}),
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter quantity'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['source_agency'].empty_label = "Select source agency"
        self.fields['destination_agency'].empty_label = "Select destination agency"
        self.fields['product'].empty_label = "Select product"

    def clean(self):
        cleaned = super().clean()
        source = cleaned.get('source_agency')
        destination = cleaned.get('destination_agency')
        if source and destination and source == destination:
            raise forms.ValidationError("Source and destination agency can't be the same.")
        return cleaned