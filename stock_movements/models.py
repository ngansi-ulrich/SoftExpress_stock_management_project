from django.db import models
from inventory.models import Inventory
from accounts.models import Employee

class StockMovement(models.Model):

    MOVEMENT_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('TRANSFER', 'Transfer'),
    ]

    inventory = models.ForeignKey(
        Inventory,
        on_delete=models.CASCADE
    )

    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPES
    )

    quantity = models.PositiveIntegerField()

    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.movement_type} - {self.quantity}"
