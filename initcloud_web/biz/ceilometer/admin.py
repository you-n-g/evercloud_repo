from django.contrib import admin
from django.contrib import admin

from biz.ceilometer.models import Ceilometer 


#class CeilometerAdmin(admin.ModelAdmin):
#    list_display = ("user", "mobile", "user_type", "balance")

admin.site.register(Ceilometer)
