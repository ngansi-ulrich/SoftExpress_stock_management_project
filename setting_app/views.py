import django
from django.conf import settings as django_settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from logs.models import ActivityLog
from accounts.models import Employee
from .models import SystemSettings, NotificationPreference
from .forms import GeneralSettingsForm, NotificationPreferenceForm


def _has_admin_access(user):
    """Same rule as the Users module — CEO/superuser only. Used to gate
    the company-wide tabs (General/Security/System), not Appearance or
    Notifications, which are personal to whoever is logged in."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return Employee.objects.filter(user=user, role='CEO').exists()


@login_required
def settings_view(request):
    tab = request.GET.get('tab', 'general')
    is_admin = _has_admin_access(request.user)

    if tab in ('general', 'security', 'system') and not is_admin:
        messages.error(request, "You don't have permission to view that settings section.")
        tab = 'notifications'

    context = {
        'active_tab': tab,
        'is_admin': is_admin,
    }

    if tab == 'general':
        context['general_form'] = GeneralSettingsForm(instance=SystemSettings.get_solo())

    elif tab == 'notifications':
        context['notification_form'] = NotificationPreferenceForm(
            instance=NotificationPreference.get_for_user(request.user)
        )

    elif tab == 'security':
        recent_logins = ActivityLog.objects.filter(
            action='LOGIN'
        ).select_related('user').order_by('-created_at')[:10]
        context['recent_logins'] = recent_logins
        context['session_age_days'] = django_settings.SESSION_COOKIE_AGE // 86400

    elif tab == 'system':
        db_engine = django_settings.DATABASES.get('default', {}).get('ENGINE', 'unknown')
        context['system_info'] = {
            'app_name': 'SoftExpress ERP',
            'app_version': '1.0.0',  # matches the version shown in footer.html
            'django_version': django.get_version(),
            'database_engine': db_engine.split('.')[-1],
            'environment': 'Development' if django_settings.DEBUG else 'Production',
        }

    return render(request, 'setting_app/settings.html', context)


@login_required
def settings_save_general(request):
    if not _has_admin_access(request.user):
        messages.error(request, "You don't have permission to change company settings.")
        return redirect('settings_view')

    if request.method == 'POST':
        instance = SystemSettings.get_solo()
        form = GeneralSettingsForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            ActivityLog.objects.create(
                user=request.user,
                action="SETTINGS_UPDATED",
                description="Updated general company settings"
            )
            messages.success(request, "Settings saved successfully.")
        else:
            messages.error(request, "Please correct the errors below.")

    return redirect(f"{reverse('settings_view')}?tab=general")


@login_required
def settings_save_notifications(request):
    if request.method == 'POST':
        instance = NotificationPreference.get_for_user(request.user)
        form = NotificationPreferenceForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Notification preferences saved.")
        else:
            messages.error(request, "Please correct the errors below.")

    return redirect(f"{reverse('settings_view')}?tab=notifications")