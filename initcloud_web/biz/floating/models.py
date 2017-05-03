#coding=utf-8

import logging

from django.db import models
from django.utils.translation import ugettext_lazy as _

from biz.account.models import Notification
from biz.floating.settings import (FLOATING_STATUS, FLOATING_AVAILABLE,
                                   RESOURCE_TYPE, FLOATING_REJECTED,
                                   FLOATING_ALLOCATE, FLOATING_ERROR,
                                   RESOURCE_INSTANCE, RESOURCE_LOADBALANCER,
                                   CANNOT_BILL_STATES)

LOG = logging.getLogger(__name__)


class Floating(models.Model):

    id = models.AutoField(primary_key=True) 
    ip = models.CharField(_("Public IP"), max_length=255, blank=True, null=True)
    uuid = models.CharField('Floating uuid', null=True, blank=True, max_length=128)
    fixed_ip = models.CharField('Fixed IP', null=True, blank=True, max_length=128)
    port_id = models.CharField('Port uuid', null=True, blank=True, max_length=128)
    status = models.IntegerField(_("Status"), choices=FLOATING_STATUS, 
                                default=FLOATING_AVAILABLE)
    bandwidth = models.IntegerField(_("Bandwidth MB"), default=2)
    instance = models.ForeignKey('instance.Instance', null=True, blank=True, default=None)

    resource = models.IntegerField(_("Resource"), null=True, blank=True, default=None)
    resource_type = models.CharField(_("Resource type"), null=True,
                blank=True, choices=RESOURCE_TYPE, max_length=40)

    status_reason = models.CharField(_("Status Reason"), max_length=255, blank=True, null=True)
    user = models.ForeignKey('auth.User')
    user_data_center = models.ForeignKey('idc.UserDataCenter')
    create_date = models.DateTimeField(_("Create Date"), auto_now_add=True)
    delete_date = models.DateTimeField(_("Delete Date"), null=True, blank=True)
    deleted = models.BooleanField(_("Deleted"), default=False)

    class Meta:
        db_table = "floating"
        ordering = ['-create_date']
        verbose_name = _('Floating')
        verbose_name_plural = _('Floating')

    @property
    def resource_info(self):
        resource_dict = dict(RESOURCE_TYPE)
        try:
            if resource_dict[self.resource_type] == RESOURCE_INSTANCE:
                from biz.instance.models import Instance
                from biz.instance.serializer import InstanceSerializer
                instance = Instance.objects.get(pk=self.resource, user=self.user)
                return {"id": instance.id, "name": instance.name, "resource_type": self.resource_type}
            elif resource_dict[self.resource_type] == RESOURCE_LOADBALANCER:
                from biz.lbaas.models import BalancerPool
                from biz.lbaas.serializer import BalancerPoolSerializer
                pool = BalancerPool.objects.get(pk=self.resource, user=self.user)
                return {"id": pool.id, "name": pool.name, "resource_type": self.resource_type}
        except Exception as e:
            return {}

    @property
    def workflow_info(self):
        ## TODO: Chargesystem logic
        return _("Floating IP: %d Mbps") % (self.bandwidth,)

    @classmethod
    def get_instance_ip(cls, instance_id):
        """
        Get instance fip
        """
        floating = None
        try:
            floating = cls.objects.get(resource_type=RESOURCE_INSTANCE,
                                       resource=instance_id,
                                       deleted=False)
        except Floating.DoesNotExist:
            pass
        except Floating.MultipleObjectsReturned:
            LOG.error("There is multiple floating binded to instance: %s",
                      instance_id)

        return floating

    @classmethod
    def get_lbaas_ip(cls, resource_id):
        ## TODO: lbaas logic

        floating = None
        try:
            floating = cls.objects.get(resource_type=RESOURCE_LOADBALANCER,
                                       resource=resource_id,
                                       deleted=False)
        except Floating.DoesNotExist:
            pass
        except Floating.MultipleObjectsReturned:
            LOG.error("There is multiple floating associated with lbaas: %s",
                      resource_id)

        return floating

    def workflow_approve_callback(self, flow_instance):
        from cloud.tasks import allocate_floating_task

        try:
            allocate_floating_task.delay(self)

            self.status = FLOATING_ALLOCATE
            self.save()

            content = title = _('Your application for %(bandwidth)d Mbps floating IP is approved! ') \
                % {'bandwidth': self.bandwidth}
            Notification.info(flow_instance.owner, title, content, is_auto=True)
        except:

            self.status = FLOATING_ERROR
            self.save()

            title = _('Error happened to your application for floating IP')

            content = _('Your application for %(bandwidth)d Mbps floating ip is approved, '
                        'but an error happened when creating it.') % {'bandwidth': self.bandwidth}

            Notification.error(flow_instance.owner, title, content, is_auto=True)

    def workflow_reject_callback(self, flow_instance):

        self.status = FLOATING_REJECTED
        self.save()

        content = title = _('Your application for %(bandwidth)d floating IP is rejected! ') \
            % {'bandwidth': self.bandwidth}
        Notification.error(flow_instance.owner, title, content, is_auto=True)

    def unbind_resource(self):
        from biz.instance.models import Instance
        from biz.lbaas.models import BalancerPool, BalancerVIP

        if self.resource_type == 'INSTANCE':
            ins = Instance.objects.get(pk=self.resource)
            ins.public_ip = None
            ins.save()
        elif self.resource_type == 'LOADBALANCER':
            pool = BalancerPool.objects.get(pk=self.resource)
            if pool.vip is not None:
                vip = BalancerVIP.objects.get(pk=pool.vip.id)
                vip.public_address = None
                vip.save()

        self.resource = None
        self.resource_type = None
        self.status = FLOATING_AVAILABLE
        self.fixed_ip = None
        self.port_id = None
        self.save()

    def can_bill(self):
        """

        Determided by deleted or status
        """
        return not (self.deleted or self.status in CANNOT_BILL_STATES)

    def __unicode__(self):
        return u"<Floating ID:%s FIP:%s>" % (self.id, self.ip)
