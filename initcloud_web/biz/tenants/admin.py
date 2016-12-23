from django.contrib import admin
from django.contrib import admin

from biz.tenants.models import Tenants 


class TenantsAdmin(admin.ModelAdmin):
    list_display = ("name", "description")

admin.site.register(Tenants)
