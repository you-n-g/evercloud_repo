from django.contrib import admin
from django.contrib import admin

from biz.snapshot.models import Snapshot 


#class SnapshotAdmin(admin.ModelAdmin):
#    list_display = ("user", "mobile", "user_type", "balance")

admin.site.register(Snapshot)
