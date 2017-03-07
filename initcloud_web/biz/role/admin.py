from django.contrib import admin

# Register your models here.

from django.contrib import admin
from biz.role.models import Role 


class RoleAdmin(admin.ModelAdmin):
    list_display = ("rolename", "datacenter", "deleted", "create_date")

admin.site.register(Role, RoleAdmin)
