from django.db import models
from django.conf import settings

class Agency(models.Model):
    name = models.CharField(max_length=150, unique=True)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_agencies'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Agencies"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.city})"