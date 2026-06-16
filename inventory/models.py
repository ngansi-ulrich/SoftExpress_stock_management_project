from django.db import models
from agencies.models import Agency
from products.models import Product

class Inventory(models.Model):

    agency = models.ForeignKey(
        Agency,
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    quantity = models.PositiveIntegerField(
        default=0
    )

    minimum_stock = models.PositiveIntegerField(
        default=5
    )

    last_updated = models.DateTimeField(
        auto_now=True
    )
    @property
    def is_low_stock(self):
        return self.quantity <= self.minimum_stock

    def __str__(self):
        return f"{self.agency} - {self.product}"