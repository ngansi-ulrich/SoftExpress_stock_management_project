from django.db import models
from agencies.models import Agency
from django.contrib.auth.models import User


class Employee(models.Model):

    user = models.OneToOneField(
    User,
    on_delete=models.CASCADE,
    null=True,
    blank=True)
    
    ROLE_CHOICES = [
        ('CEO', 'CEO'),
        ('MANAGER', 'Manager'),
        ('STAFF', 'Staff'),
    ]

    employee_id = models.CharField(max_length=20, unique=True, blank=True)

    first_name = models.CharField(max_length=100)

    last_name = models.CharField(max_length=100)

    email = models.EmailField(unique=True)

    phone = models.CharField(max_length=20)

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    agency = models.ForeignKey(
        Agency,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    def save(self, *args, **kwargs):

        if not self.employee_id:

            last_employee = Employee.objects.order_by('id').last()

            if last_employee:
                last_id = last_employee.id + 1
            else:
                last_id = 1

            self.employee_id = f"EMP{last_id:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee_id} - {self.first_name} {self.last_name}"