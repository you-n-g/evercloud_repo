from django.db import models
from django.utils.translation import ugettext_lazy as _



class Templatemanager(models.Model):
    user = models.ForeignKey("auth.User")
    deleted = models.BooleanField(_("Deleted"), default=False)
    create_date = models.DateTimeField(_("Create Date"), auto_now_add=True)
    template_name = models.CharField(_("Template_Name"), max_length=60, null=False)
    template_uuid = models.CharField(_("Template_uuid"), max_length=60, null=False)
    template_baseuuid = models.CharField(_("Template_baseuuid"), max_length=60, null=False)
    template_serverip = models.CharField(_("Template_serverip"), max_length=60, null=True)
    template_port = models.CharField(_("Template_port"), max_length=60, null=True)
    template_state = models.CharField(_("Template_state"), max_length=60, null=True)
    template_refcount = models.CharField(_("Template_refcount"), max_length=60, null=True)
    template_vmcount = models.CharField(_("Template_vmcount"), max_length=60, null=True)
    template_vcpu = models.CharField(_("Template_vcpu"), max_length=60, null=True)
    template_memory = models.CharField(_("Template_memoy"), max_length=60, null=True)
    template_disksize = models.CharField(_("Template_Disksize"), max_length=60, null=True)
    template_mac = models.CharField(_("Template_Mac"), max_length=60, null=True)
    template_operatestate = models.CharField(_("Template_OperateState"), max_length=60, null=True)
    template_protocol = models.CharField(_("Template_Protocol"), max_length=60, null=True)
    template_ostype = models.CharField(_("Template_Ostype"), max_length=60, null=True)
    template_softwarelist = models.CharField(_("Template_Softwarelist"), max_length=60, null=True)
    template_other = models.CharField(_("Template_Other"), max_length=60, null=True)
    template_flag = models.CharField(_("Template_Flag"), max_length=60, null=True)
    template_public = models.CharField(_("Template_Public"), max_length=60, null=True)
    template_iso = models.CharField(_("Template_ISO"), max_length=60, null=True)


    """
    @classmethod
    def log(cls, obj, obj_name, action, result=1, udc=None, user=None):

        try:
            Templatemanager.objects.create(
                resource=obj.__class__.__name__,
                resource_id=obj.id,
                resource_name=obj_name,
                action=action,
                result=result
            )
        except Exception as e:
            pass
    """
