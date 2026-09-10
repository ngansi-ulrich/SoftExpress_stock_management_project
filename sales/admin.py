from django.contrib import admin
from .models import Sale, SaleItem, Invoice

admin.site.register(Sale)
admin.site.register(SaleItem)
admin.site.register(Invoice)