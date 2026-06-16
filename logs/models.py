from django.db import models
from django.contrib.auth.models import User


class ActivityLog(models.Model):

    ACTIONS = (
        ('LOGIN', 'Login'),
        ('SALE', 'Sale'),
        ('PRODUCT', 'Product Added'),
        ('TRANSFER', 'Stock Transfer'),
        ('CUSTOMER', 'Customer Added'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    action = models.CharField(
        max_length=20,
        choices=ACTIONS
    )

    description = models.CharField(
        max_length=255
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.action}"