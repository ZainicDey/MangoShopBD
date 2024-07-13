from django.contrib import admin
from . import models

admin.site.register(models.Mango)
admin.site.register(models.Seller)
admin.site.register(models.Order)