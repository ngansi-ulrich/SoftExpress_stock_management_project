from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from logs.models import ActivityLog
from .models import Employee
from .forms import (
    UserCreateForm,
    UserEditForm,
    SetPasswordForm,
    ChangePasswordForm,
    ProfilePictureForm,
)


def Login(request):

    print("VIEW REACHED")

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            ActivityLog.objects.create(
                user=user,
                action="LOGIN",
                description="User logged into system"
            )

            employee = getattr(user, 'employee', None)
            if user.is_superuser or (employee and employee.role == 'CEO'):
                return redirect("dashboard")
            elif employee and employee.role == 'MANAGER':
                return redirect("manager_dashboard")
            elif employee and employee.role == 'STAFF':
                return redirect("employee_dashboard")
            else:
                # authenticated but no Employee record / no role at all —
                # never fall through to the CEO dashboard by default
                messages.error(
                    request,
                    "Your account isn't fully set up yet. Contact your administrator."
                )
                logout(request)
                return redirect("Login")

        messages.error(
            request,
            "Invalid username or password"
        )

        return redirect("Login")
    return render(request, "accounts/Login.html")


def Logout(request):
    logout(request)
    return redirect("Login")


# ---------- Administration: Users ----------
# Gated to CEO/superuser only. Because non-CEO users can never reach these
# views at all (not just a hidden sidebar link), a MANAGER/STAFF account
# crafting a raw POST with role=CEO has no path to this code — the
# privilege-escalation protection the spec asks for is structural, not a
# per-field check.

def _has_admin_access(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return Employee.objects.filter(user=user, role='CEO').exists()


@user_passes_test(_has_admin_access, login_url='Login')
def user_list(request):
    users = User.objects.select_related('employee', 'employee__agency').order_by('-date_joined')

    query = request.GET.get('q')
    role = request.GET.get('role')
    agency_id = request.GET.get('agency')
    status = request.GET.get('status')

    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
    if role:
        users = users.filter(employee__role=role)
    if agency_id:
        users = users.filter(employee__agency_id=agency_id)
    if status == 'active':
        users = users.filter(is_active=True)
    elif status == 'inactive':
        users = users.filter(is_active=False)

    from agencies.models import Agency

    context = {
        'users': users,
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'inactive_users': User.objects.filter(is_active=False).count(),
        'admin_count': User.objects.filter(
            Q(is_superuser=True) | Q(employee__role='CEO')
        ).distinct().count(),
        'roles': Employee.ROLE_CHOICES,
        'agencies': Agency.objects.filter(is_active=True),
        'selected_role': role or '',
        'selected_agency': agency_id or '',
        'selected_status': status or '',
        'query': query or '',
    }
    return render(request, 'accounts/user_list.html', context)


@user_passes_test(_has_admin_access, login_url='Login')
def user_add(request):
    form = UserCreateForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                is_active=form.cleaned_data['is_active'],
            )
            Employee.objects.create(
                user=user,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone'],
                role=form.cleaned_data['role'],
                agency=form.cleaned_data['agency'],
            )
            ActivityLog.objects.create(
                user=request.user,
                action="USER_CREATED",
                description=f"Created user account for {user.username}"
            )
        messages.success(request, f"User {user.username} created successfully.")
        return redirect('user_list')

    return render(request, 'accounts/user_form.html', {'form': form, 'mode': 'add'})


@user_passes_test(_has_admin_access, login_url='Login')
def user_detail(request, pk):
    target_user = get_object_or_404(
        User.objects.select_related('employee', 'employee__agency'), pk=pk
    )
    recent_activity = ActivityLog.objects.filter(user=target_user).order_by('-created_at')[:10]
    return render(request, 'accounts/user_detail.html', {
        'target_user': target_user,
        'recent_activity': recent_activity,
    })


@user_passes_test(_has_admin_access, login_url='Login')
def user_edit(request, pk):
    target_user = get_object_or_404(User.objects.select_related('employee'), pk=pk)
    employee = getattr(target_user, 'employee', None)

    initial = {}
    if employee:
        initial = {
            'first_name': employee.first_name,
            'last_name': employee.last_name,
            'email': employee.email,
            'phone': employee.phone,
            'role': employee.role,
            'agency': employee.agency,
            'is_active': target_user.is_active,
        }

    form = UserEditForm(
        request.POST or None,
        initial=initial,
        employee_id=employee.pk if employee else None,
    )

    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            target_user.first_name = form.cleaned_data['first_name']
            target_user.last_name = form.cleaned_data['last_name']
            target_user.email = form.cleaned_data['email']
            target_user.is_active = form.cleaned_data['is_active']
            target_user.save()

            if employee:
                employee.first_name = form.cleaned_data['first_name']
                employee.last_name = form.cleaned_data['last_name']
                employee.email = form.cleaned_data['email']
                employee.phone = form.cleaned_data['phone']
                employee.role = form.cleaned_data['role']
                employee.agency = form.cleaned_data['agency']
                employee.save()
            else:
                # user existed with no linked Employee (e.g. a bare
                # superuser) — create one now so role/agency take effect
                Employee.objects.create(
                    user=target_user,
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    email=form.cleaned_data['email'],
                    phone=form.cleaned_data['phone'],
                    role=form.cleaned_data['role'],
                    agency=form.cleaned_data['agency'],
                )

            ActivityLog.objects.create(
                user=request.user,
                action="USER_UPDATED",
                description=f"Updated user account for {target_user.username}"
            )
        messages.success(request, f"User {target_user.username} updated.")
        return redirect('user_detail', pk=target_user.pk)

    return render(request, 'accounts/user_form.html', {
        'form': form, 'mode': 'edit', 'target_user': target_user,
    })


@user_passes_test(_has_admin_access, login_url='Login')
def user_toggle_active(request, pk):
    if request.method != 'POST':
        return redirect('user_detail', pk=pk)

    target_user = get_object_or_404(User, pk=pk)
    target_user.is_active = not target_user.is_active
    target_user.save()

    action = "USER_ACTIVATED" if target_user.is_active else "USER_DEACTIVATED"
    ActivityLog.objects.create(
        user=request.user,
        action=action,
        description=f"{'Activated' if target_user.is_active else 'Deactivated'} {target_user.username}"
    )
    messages.success(
        request,
        f"{target_user.username} is now {'active' if target_user.is_active else 'inactive'}."
    )
    return redirect('user_detail', pk=pk)


@user_passes_test(_has_admin_access, login_url='Login')
def user_reset_password(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    form = SetPasswordForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        target_user.set_password(form.cleaned_data['new_password'])
        target_user.save()
        ActivityLog.objects.create(
            user=request.user,
            action="PASSWORD_RESET",
            description=f"Password reset for {target_user.username} by admin"
        )
        messages.success(request, f"Password updated for {target_user.username}.")
        return redirect('user_detail', pk=pk)

    return render(request, 'accounts/user_reset_password.html', {
        'form': form, 'target_user': target_user,
    })


@login_required
def change_password(request):
    """Self-service password change for whoever is logged in — distinct
    from user_reset_password, which is the CEO setting someone else's
    password from the Users admin page."""
    form = ChangePasswordForm(request.POST or None, user=request.user)

    if request.method == 'POST' and form.is_valid():
        request.user.set_password(form.cleaned_data['new_password'])
        request.user.save()
        # keeps the user logged in after changing their own password —
        # without this, Django invalidates the session on password change
        update_session_auth_hash(request, request.user)

        ActivityLog.objects.create(
            user=request.user,
            action="PASSWORD_CHANGED",
            description="User changed their own password"
        )
        messages.success(request, "Your password has been updated.")
        return redirect('settings_view')

    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def profile_view(request):
    """Read-only self view. Role/agency changes are deliberately NOT
    editable here — those go through the CEO-only Users module
    (user_edit), never through a self-service page."""
    from .permissions import get_employee
    employee = get_employee(request.user)
    if employee is None and request.user.is_superuser:
        email = request.user.email or f'{request.user.username}@local.invalid'
        if Employee.objects.filter(email=email).exists():
            email = f'{request.user.username}+{request.user.pk}@local.invalid'
        employee = Employee.objects.create(
            user=request.user,
            first_name=request.user.first_name or request.user.username,
            last_name=request.user.last_name or 'Administrator',
            email=email,
            phone='',
            role='CEO',
        )
    form = ProfilePictureForm(
        data=request.POST or None,
        files=request.FILES or None,
        instance=employee,
    )

    if request.method == 'POST':
        if employee is None:
            messages.error(request, "Your account has no linked employee record.")
        elif form.is_valid():
            old_picture = employee.profile_picture.name if employee.profile_picture else None
            updated_employee = form.save(commit=False)
            if form.cleaned_data.get('remove_picture'):
                updated_employee.profile_picture = None
            updated_employee.save()
            new_picture = updated_employee.profile_picture.name if updated_employee.profile_picture else None
            if old_picture and old_picture != new_picture:
                updated_employee.profile_picture.storage.delete(old_picture)
            messages.success(request, "Your profile picture was updated.")
            return redirect('profile_view')

    return render(request, 'accounts/profile.html', {
        'employee': employee,
        'picture_form': form,
    })