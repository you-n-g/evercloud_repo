# -*- coding:utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _


from biz.network.models import Network
from biz.instance.settings import (INSTANCE_STATE_WAITING,
                                   INSTANCE_STATE_RUNNING,
                                   INSTANCE_STATES,
                                   INSTANCE_STATE_REJECTED,
                                   INSTANCE_STATE_ERROR,
                                   INSTANCE_STATE_DELETE,
                                   INSTANCE_STATE_DELETING,
                                   CANNOT_BILL_STATES)

from biz.firewall.models import Firewall
from biz.floating.models import Floating
from biz.account.models import Notification

LINUX_IMAGE = 2
WINDOWS_IMAGE = 1
IMAGE_TYPE = (
    (LINUX_IMAGE, _("Linux Image")),
    (WINDOWS_IMAGE, _("Windows Image")),
)


class Instance(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(_('Instance Name'), null=False, blank=False, max_length=128)
    status = models.IntegerField(_("Status"), choices=INSTANCE_STATES, 
                                default=INSTANCE_STATE_WAITING)
    create_date = models.DateTimeField(_("Create Date"), auto_now_add=True)
    terminate_date = models.DateTimeField(_("Terminate Date"), auto_now_add=True)
    cpu = models.IntegerField(_("Cpu Cores"))
    policy = models.IntegerField(_("Policy"), null=False, default=0)
    device_id = models.TextField(_("Enabled Devices"), null=True, blank=True)
    memory = models.IntegerField(_("Memory"))
    sys_disk = models.FloatField(_("System Disk"), null=False, blank=True)
    
    flavor_id = models.CharField(_("OS FlavorID"), null=True, max_length=36)

    image = models.ForeignKey("image.Image", db_column="image_id", null=True, blank=True)
    network_id = models.IntegerField(_("Network"), null=False, blank=False, default=0)
    
    user = models.ForeignKey('auth.User')
    user_data_center = models.ForeignKey('idc.UserDataCenter')
    
    uuid = models.CharField('instance uuid', null=True, blank=True, max_length=128)
    tenant_uuid = models.CharField('tenant uuid', null=True, blank=True, max_length=128)
    private_ip = models.CharField(_("Private IP"), max_length=255, blank=True, null=True)
    public_ip = models.CharField(_("Public IP"), max_length=255, blank=True, null=True)

    deleted = models.BooleanField(_("Deleted"), default=False)
    
    firewall_group = models.ForeignKey("firewall.Firewall", null=True)
    
    core = models.IntegerField(_("Cores"), default=1)
    socket = models.IntegerField(_("Sockets"), default=1)
    
    MIMI = 0
    JIMI = 1
    SECURITY_CLS = (
        (MIMI, u"秘密"),
        (JIMI, u"机密"),
    )
    security_cls = models.IntegerField(u"密级",  choices=SECURITY_CLS, 
                                default=MIMI)

    class Meta:
        db_table = "instance"
        ordering = ['-create_date']
        verbose_name = _("Instance")
        verbose_name_plural = _("Instance")

    @property
    def volumes_info(self):
        result = []
        for volume in self.volume_set.all():
            result.append({"id": volume.id,
                            "name": volume.name,
                            "size": volume.size})
        return result

    @property
    def network(self):
        try:
            network = Network.objects.get(pk=self.network_id) 
        except Network.DoesNotExist:
            network = None
        
        return network
        
    @property
    def floating_ip(self):
        floating = Floating.get_instance_ip(self.id)
        return floating.ip if floating else None

    @property
    def workflow_info(self):
        return  _("Instance: %(name)s / %(cpu)s "
                  "CPU/ %(memory)s MB/ %(sys_disk)d GB") \
            % {'name': self.name, 'cpu': self.cpu,
               'memory': self.memory, 'sys_disk': self.sys_disk}

    @property
    def is_running(self):
        return self.status == INSTANCE_STATE_RUNNING

    def __unicode__(self):
        return u"<Instance: ID:%s Name:%s>" % (
                    self.id, self.name) 

    def set_default_firewall(self):
        firewall_set = Firewall.objects.filter(
                            is_default=True, user=self.user,
                            user_data_center=self.user_data_center,
                            deleted=False)
        if firewall_set.exists():
            self.firewall_group = firewall_set[0]
            self.save()

    def workflow_approve_callback(self, flow_instance):
        from cloud.instance_task import instance_create_task

        try:
            instance_create_task.delay(self, password=flow_instance.extra_data)

            self.status = INSTANCE_STATE_WAITING
            self.save()

            content = title = _('Your application for instance "%(instance_name)s" is approved! ') \
                % {'instance_name': self.name}
            Notification.info(flow_instance.owner, title, content, is_auto=True)
        except:

            self.status = INSTANCE_STATE_ERROR
            self.save()

            title = _('Error happened to your application for %(instance_name)s') \
                % {'instance_name': self.name}

            content = _('Your application for instance "%(instance_name)s" is approved, '
                        'but an error happened when creating instance.') % {'instance_name': self.name}

            Notification.error(flow_instance.owner, title, content, is_auto=True)

    def workflow_reject_callback(self, flow_instance):

        self.status = INSTANCE_STATE_REJECTED
        self.save()

        content = title = _('Your application for instance "%(instance_name)s" is rejected! ') \
            % {'instance_name': self.name}
        Notification.error(flow_instance.owner, title, content, is_auto=True)

    def can_bill(self):
        return not (self.deleted or self.status in CANNOT_BILL_STATES)


class Flavor(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(_('Name'), null=False, blank=False, max_length=128)
    cpu = models.IntegerField(_("Cpu Cores"))
    memory = models.IntegerField(_("Memory MB"))
    price = models.FloatField(_("Price"))
    create_date = models.DateTimeField(_("Create Date"), auto_now_add=True)
    flavorid = models.CharField(_('FlavorId'), null=False, blank=False, max_length=128, default = None)
    disk = models.IntegerField(_("Disk"), default = 10)
    

    def __unicode__(self):
        return u"<Flavor: ID:%s Name:%s C:%s M:%s>" % (self.id, self.name,
                        self.cpu, self.memory) 

    class Meta:
        db_table = "flavor"
        ordering = ['cpu']
        verbose_name = _("Flavor")
        verbose_name_plural = _("Flavor")
