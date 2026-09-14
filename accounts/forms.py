from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from agencies.models import Agency
from .models import Employee


class UserCreateForm(forms.Form):
    """
    Creates a User + its linked Employee together in one form, since
    role/agency/phone only exist on Employee — a User with no Employee
    would have no meaningful permissions anywhere in this app.
    """
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(choices=Employee.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    agency = forms.ModelChoiceField(
        queryset=Agency.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_active = forms.BooleanField(
        required=False, initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['agency'].empty_label = "No agency assigned"

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError("That username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if Employee.objects.filter(email=email).exists():
            raise ValidationError("A user with that email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        confirm = cleaned.get('confirm_password')
        if password and confirm and password != confirm:
            self.add_error('confirm_password', "Passwords don't match.")
        if password:
            try:
                validate_password(password)
            except ValidationError as e:
                self.add_error('password', e)
        return cleaned


class UserEditForm(forms.Form):
    """
    Deliberately excludes username (kept immutable to avoid login/identity
    confusion) and password (handled by the separate reset-password action).
    """
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(choices=Employee.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    agency = forms.ModelChoiceField(
        queryset=Agency.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_active = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        self.employee_id = kwargs.pop('employee_id', None)
        super().__init__(*args, **kwargs)
        self.fields['agency'].empty_label = "No agency assigned"

    def clean_email(self):
        email = self.cleaned_data['email']
        qs = Employee.objects.filter(email=email)
        if self.employee_id:
            qs = qs.exclude(pk=self.employee_id)
        if qs.exists():
            raise ValidationError("Another user already uses that email.")
        return email


class SetPasswordForm(forms.Form):
    """Admin-direct password set — no email token flow, since EMAIL_BACKEND
    isn't confirmed to actually send mail in this environment."""
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned = super().clean()
        new = cleaned.get('new_password')
        confirm = cleaned.get('confirm_password')
        if new and confirm and new != confirm:
            self.add_error('confirm_password', "Passwords don't match.")
        if new:
            try:
                validate_password(new)
            except ValidationError as e:
                self.add_error('new_password', e)
        return cleaned


class ChangePasswordForm(forms.Form):
    """Self-service — any logged-in user changing their own password,
    as opposed to SetPasswordForm which is the CEO setting someone
    else's password from the Users admin page."""
    current_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current = self.cleaned_data['current_password']
        if not self.user.check_password(current):
            raise forms.ValidationError("Your current password is incorrect.")
        return current

    def clean(self):
        cleaned = super().clean()
        new = cleaned.get('new_password')
        confirm = cleaned.get('confirm_password')
        if new and confirm and new != confirm:
            self.add_error('confirm_password', "Passwords don't match.")
        if new:
            from django.contrib.auth.password_validation import validate_password
            from django.core.exceptions import ValidationError
            try:
                validate_password(new, user=self.user)
            except ValidationError as e:
                self.add_error('new_password', e)
        return cleaned