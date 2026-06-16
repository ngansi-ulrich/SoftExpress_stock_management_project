from django.db import models

class Customer(models.Model):

    customer_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    first_name = models.CharField(
        max_length=100
    )

    last_name = models.CharField(
        max_length=100
    )

    phone = models.CharField(
        max_length=20,
        unique=True,
    )

    email = models.EmailField(
        blank=True,
        null=True
    )

    address = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def save(self, *args, **kwargs):

        if not self.customer_id:

            last_customer = Customer.objects.order_by('id').last()

            if last_customer:
                next_id = last_customer.id + 1
            else:
                next_id = 1

            self.customer_id = f"CUS{next_id:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer_id} - {self.first_name} {self.last_name}"