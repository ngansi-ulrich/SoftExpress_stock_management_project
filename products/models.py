from django.db import models

class Category(models.Model):

    name = models.CharField(max_length=100)

    description = models.TextField(blank=True)

    def __str__(self):
        return self.name
    
class Product(models.Model):

    product_code = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
    )

    name = models.CharField(
        max_length=200
    )
    def save(self, *args, **kwargs):

        if not self.product_code:

            last_product = Product.objects.order_by('id').last()

            if last_product:
                last_id = last_product.id + 1
            else:
                last_id = 1

            self.product_code = f"PRD{last_id:04d}"

        super().save(*args, **kwargs)

    brand = models.CharField(
        max_length=100
    )

    model = models.CharField(
        max_length=100
    )

    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    description = models.TextField(
        blank=True
    )

    requires_serial_tracking = models.BooleanField(
        default=True
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name