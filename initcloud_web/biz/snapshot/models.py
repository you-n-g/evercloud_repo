from django.db import models
from django.utils.translation import ugettext_lazy as _



class Snapshot(models.Model):
    #user = models.ForeignKey('auth.User')
    #udc = models.ForeignKey('idc.UserDataCenter')
   
    id = models.AutoField(primary_key=True)
    snapshotname = models.CharField(_("Role"), max_length=15, null=False)
    datacenter = models.IntegerField(_("Result"), default=0, null=False)
    deleted = models.BooleanField(_("Deleted"), default=False)
    create_date = models.DateTimeField(_("Create Date"), auto_now_add=True)
    snapshot_id = models.CharField(_("Snap_id"), max_length=255, null=False, default='')
    snapshot_name = models.CharField(_("Snap_name"), max_length=255, null=False, default='')
    snapshot_type = models.CharField(_("Type"), max_length=255, null=False, default='')
    volume_id = models.CharField(_("Volume"), max_length=255, null=False, default='')


    class Meta:
        db_table = "snapshot"
        ordering = ['-create_date']
        verbose_name = _("Snapshot")
        verbose_name_plural = _("Snapshot")

    """
    @classmethod
    def log(cls, obj, obj_name, action, result=1, udc=None, user=None):

        try:
            Snapshot.objects.create(
                resource=obj.__class__.__name__,
                resource_id=obj.id,
                resource_name=obj_name,
                action=action,
                result=result
            )
        except Exception as e:
            pass
    """
