from django.db import models
from django.contrib.auth.models import User


class SystemSettings(models.Model):
    """
    Singleton-style model — only one row is ever expected to exist.
    Use SystemSettings.get_solo() rather than .objects.first() so callers
    don't have to think about the singleton pattern.
    """

    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('fr', 'Français'),
    ]

    company_name = models.CharField(max_length=150, default='SoftExpress')
    company_email = models.EmailField(blank=True)
    company_phone = models.CharField(max_length=20, blank=True)
    company_address = models.CharField(max_length=255, blank=True)
    company_logo = models.ImageField(upload_to='company/', null=True, blank=True)

    default_language = models.CharField(
        max_length=5, choices=LANGUAGE_CHOICES, default='en'
    )
    timezone = models.CharField(max_length=50, default='Africa/Douala')

    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1  # enforce singleton
        super().save(*args, **kwargs)

    def __str__(self):
        return self.company_name


class NotificationPreference(models.Model):
    """
    Per-user notification toggles. NOTE: these genuinely persist, but
    there is no email/SMS/push delivery system in the project yet to
    actually act on them — this only controls what *would* be sent once
    such a system exists.
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='notification_preference'
    )

    low_stock_alerts = models.BooleanField(default=True)
    new_sale_notifications = models.BooleanField(default=True)
    transfer_notifications = models.BooleanField(default=True)
    system_notifications = models.BooleanField(default=True)
    account_notifications = models.BooleanField(default=True)

    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_for_user(cls, user):
        obj, _ = cls.objects.get_or_create(user=user)
        return obj

    def __str__(self):
        return f"Notification preferences for {self.user.username}"