from django.db import models

from agencies.models import Agency
from products.models import Product
from accounts.models import Employee


class Transfer(models.Model):

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    transfer_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    source_agency = models.ForeignKey(
        Agency,
        on_delete=models.PROTECT,
        related_name='outgoing_transfers'
    )

    destination_agency = models.ForeignKey(
        Agency,
        on_delete=models.PROTECT,
        related_name='incoming_transfers'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT
    )

    quantity = models.PositiveIntegerField()

    requested_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.transfer_number