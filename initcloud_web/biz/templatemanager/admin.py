from django.contrib import admin
from django.contrib import admin

from biz.templatemanager.models import Templatemanager 


#class TemplatemanagerAdmin(admin.ModelAdmin):
#    list_display = ("user", "mobile", "user_type", "balance")

admin.site.register(Templatemanager)
