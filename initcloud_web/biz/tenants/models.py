from django.db import models
from django.utils.translation import ugettext_lazy as _

class Tenant_user(models.Model):
    #user = models.ForeignKey(User)
    #udc = models.ForeignKey('idc.UserDataCenter')

    tenant_id = models.CharField(_("id"), max_length=36, null=True)
    #datacenter = models.IntegerField(_("Result"), default=0, null=False)
    user_uuid = models.CharField(_("user_id"), max_length=36, null=True)
    user_id = models.CharField(_("user_id"), max_length=36, null=True)
    default_tenant_id = models.CharField(_("default_tenant_id"), max_length=36, null=True)
    tenant_name = models.CharField(_("Tenant Name"), max_length=15, null=True)
    create_date = models.DateTimeField(_("Create Date"), auto_now_add=True)


class Tenants(models.Model):
    #user = models.ForeignKey(User)
    #udc = models.ForeignKey('idc.UserDataCenter')

    name = models.CharField(_("Name"), max_length=15, null=False)
    description = models.CharField(_("Description"), max_length=15, null=False)
    tenant_id = models.CharField(_("id"), max_length=36, null=True)
    #datacenter = models.IntegerField(_("Result"), default=0, null=False)
    deleted = models.BooleanField(_("Deleted"), default=False)
    create_date = models.DateTimeField(_("Create Date"), auto_now_add=True)

    @classmethod
    def log(cls, obj, obj_name, action, result=1, udc=None, user=None):

        try:
            Tenants.objects.create(
                resource=obj.__class__.__name__,
                resource_id=obj.id,
                resource_name=obj_name,
                action=action,
                result=result
            )
        except Exception as e:
            pass
