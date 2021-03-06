from django.db import models
from django.utils.translation import ugettext_lazy as _


# Create your models here.

class Role(models.Model):
    #user = models.ForeignKey(User)
    #udc = models.ForeignKey('idc.UserDataCenter')

    rolename = models.CharField(_("Role"), max_length=15, null=False)
    datacenter = models.IntegerField(_("Result"), default=0, null=False)
    deleted = models.BooleanField(_("Deleted"), default=False)
    create_date = models.DateTimeField(_("Create Date"), auto_now_add=True)
