from django.db import models
from customers.models import Customer
from inventory.models import Inventory
from agencies.models import Agency
from accounts.models import Employee
from products.models import Product


class Sale(models.Model):

    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('MOMO', 'Mobile Money'),
        ('BANK', 'Bank Transfer'),
        ('CARD', 'Card'),
    ]

    PAYMENT_STATUS = [
        ('PAID', 'Paid'),
        ('PARTIAL', 'Partial'),
        ('PENDING', 'Pending'),
    ]

    STATUS_CHOICES = [
    ('DRAFT', 'Draft'),
    ('COMPLETED', 'Completed'),
    ]
    status = models.CharField(
    max_length=20,
    choices=STATUS_CHOICES,
    default='DRAFT'
    )
    sale_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT
    )

    agency = models.ForeignKey(
        Agency,
        on_delete=models.PROTECT
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='PAID'
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def save(self, *args, **kwargs):

        if not self.sale_number:

            last_sale = Sale.objects.order_by('id').last()

            if last_sale:
                next_id = last_sale.id + 1
            else:
                next_id = 1

            self.sale_number = f"SAL{next_id:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.sale_number


class SaleItem(models.Model):

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT
    )

    quantity = models.PositiveIntegerField()

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    def save(self, *args, **kwargs):

        inventory = Inventory.objects.get(
            agency=self.sale.agency,
            product=self.product
        )

        if self.quantity > inventory.quantity:

            raise ValueError(
                f"Insufficient stock. Available: {inventory.quantity}"
            )

        self.subtotal = self.quantity * self.unit_price

        inventory.quantity -= self.quantity

        inventory.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name}"


class Invoice(models.Model):
    """
    A financial/document record generated from a completed Sale.
    Deliberately minimal: no InvoiceItem model, no duplicated
    payment_status/payment_method/customer/agency fields — those all
    live on Sale already and are accessed via invoice.sale.* to avoid
    two sources of truth. See invoice_list/invoice_detail views.
    """

    invoice_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    sale = models.OneToOneField(
        Sale,
        on_delete=models.CASCADE,
        related_name='invoice'
    )

    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-issued_at']

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            last = Invoice.objects.order_by('id').last()
            next_id = (last.id + 1) if last else 1
            self.invoice_number = f"INV-{next_id:06d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.invoice_number