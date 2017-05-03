# -*- coding:utf8 -*-

# Author Yang

from datetime import datetime
import logging
import requests

from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import check_password

from biz.account.settings import QUOTA_ITEM, NotificationLevel
from biz.account.models import Operation
from biz.instance.models import Instance, Flavor
from biz.instance.serializer import InstanceSerializer, FlavorSerializer
from biz.instance.utils import instance_action
from biz.instance.settings import (INSTANCE_STATES_DICT, INSTANCE_STATE_RUNNING,
                                   INSTANCE_STATE_APPLYING, MonitorInterval)
from biz.instancemanage.utils import * 
from biz.floating.models import Floating
from biz.idc.models import DataCenter, UserDataCenter
from biz.common.pagination import PagePagination
from biz.common.decorators import require_POST, require_GET
from biz.common.utils import retrieve_params, fail
from biz.workflow.models import Step
from cloud.api import keystone
from cloud.cloud_utils import create_rc_by_dc
from cloud.tasks import (link_user_to_dc_task, send_notifications, delete_user_instance_network, 
                         send_notifications_by_data_center)
from frontend.forms import CloudUserCreateFormWithoutCapatcha

LOG = logging.getLogger(__name__)


class InstancemanageList(generics.ListCreateAPIView):
    """
    Get all the instances
    """
    queryset = Instance.objects.all().filter(deleted=False)
    serializer_class = InstanceSerializer

    def list(self, request):
        try:
	    # filter instances which assigned to users
            udc_id = request.session["UDC_ID"]
            if request.user.is_superuser:
                serializer = InstanceSerializer(self.queryset, many=True)
                return Response(serializer.data)

            serializer = InstanceSerializer(self.queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            LOG.exception(e)
            return Response()

    def create(self, request, *args, **kwargs):
        raise NotImplementedError()

class InstancemanageDevicePolicy(generics.ListCreateAPIView):
    """
    Get instance allowed policy choices
    """

    def list(self, request, pk):
        LOG.debug("**** get policy choice from settings ****")
        try:
            # Get devicepolicy from configuration file
            devicepolicy = settings.DEVICEPOLICY
            # Determine current instance's assigned role
            for d in devicepolicy:
                instance = Instance.objects.get(pk=int(pk))
                if instance.policy:
                    d['checked'] = True
                else:
                    d['checked'] = False
            return Response(devicepolicy)
        except Exception as e:
            LOG.exception(e)
            return Response()

    def create(self, request, *args, **kwargs):
        raise NotImplementedError()




@require_GET
def is_instancemanagename_unique(request):
    """
    Check if instance's name is unqiue
    """
    instancemanagename = request.GET['instancemanagename']
    LOG.debug("instancemanagename is" + str(instancemanagename))
    return Response(not Instancemanage.objects.filter(instancemanagename=instancemanagename).exists())

@require_POST
def devicepolicyupdate(request):
    """
    Update instance policy and device_id
    param:  role
    param: device_id
    param: instance_id
    """

    policies = {
        "usb": 0
    }
    LOG.info("*** request.data is ***"  + str(request.data))
    role = request.data['role']
    instance_id = request.data['id']
    role_str = str(role)
    role_list = role_str.split(",")
    device_id = request.data['device_id']
    LOG.info("********** role_list is **********" + str(role_list))
    LOG.info("********** instance_id  is **********" + str(instance_id))
    instance = Instance.objects.get(pk=instance_id)
    instance_uuid = instance.uuid
    refered_instance = Instance.objects.filter(uuid=instance_uuid)
    for role in policies:
        LOG.info("*** role is ****" + str(role))
        for ins in refered_instance:
            if role in role_list:
                ins.policy |= 1 << policies[role] 
            else:
                ins.policy &= 0 << policies[role]
    for ins in refered_instance:
        ins.device_id = device_id
        ins.save()
    d = { 'vm_id': instance.uuid, 'storage': instance.policy, 'devices': device_id }
    LOG.info(">>>>>>> request update policy: {}".format(d)) 
    res = requests.post('{}/policy'.format(settings.MGR_HTTP_ADDR), json=d, timeout=5)
    LOG.info(">>>>>>> response: {}".format(res))
    try:
        operation = Operation(user=request.user, udc_id=request.session['UDC_ID'], resource='虚拟机', resource_id=1, resource_name='权限',action="usbrole", result=1)
        operation.save()
    except Exception as e:
        LOG.info(str(e))
    return Response({"success": True, "msg": _(
           'Sucess.')})

@require_POST
def devicepolicyundo(request):
    """
    Undo policy
    """
    LOG.debug("*** request.data is ***"  + str(request.data))
    instance_id = None
    for key, value in request.data.items():
        instance_id = value
    LOG.info("********** instance_id  is **********" + str(instance_id))
    instance = Instance.objects.get(pk=instance_id)
    instance.policy = 0 
    instance.save()
    return Response({"success": True, "msg": _(
           'Sucess.')})

@require_POST
def batch_delete(request):
    """
    Batch delete actions for instance
    """
    LOG.debug(request.data)
    LOG.info(request.data.getlist('ids[]'))
    for ID in request.data.getlist('ids[]'):
        instance_id = str(ID)
        instance = Instance.objects.get(pk=instance_id)
        instance_id = instance.uuid
        # Sync action to openstack 
        try:
            delete_user_instance_network(request, instance_id)
        except:
            pass
        # Release floating ip
        try:
            LOG.debug("resource is" + str(instance.id))
            #floating = Floating.objects.filter(resource=instance.id)[0]
            floating = Floating.objects.filter(resource=instance.id)
            LOG.info(" floating is " + str(floating))
            if floating:
                floating[0].resource = None
                floating[0].save()
        except:
            return Response({"success": False, "msg": _(
                  'failed.')})
        instance.deleted = True
        instance.save()
    return Response({"success": True, "msg": _(
               'Sucess.')})


@require_POST
def instance_action_status(request):
     vm_name = request.query_params.get("vm")
     LOG.info("*** vm_name is ***" + str(vm_name))
     instance = Instance.objects.filter(name=vm_name,deleted=0)[0]
     return Response({"msg": instance.status_reason, "status": instance.status})

@require_POST
def delete_instance(request):
    """
    Delete instance
    """
    LOG.debug("*** request.data is ***"  + str(request.data))
    instance_id = None
    for key, value in request.data.items():
        instance_id = value
    LOG.info("********** instance_id  is **********" + str(instance_id))
    instance = Instance.objects.get(pk=instance_id)
    instance_id = instance.uuid
    LOG.info("********** instance_id  is **********" + str(instance_id))
    # Sync action to openstack
    try:
        delete_user_instance_network(request, instance_id)
    except:
        pass
    try:
        LOG.info("resource is" + str(instance.id))
        #floating = Floating.objects.filter(resource=instance.id)[0]
        floating = Floating.objects.filter(resource=instance.id)
        if floating:
            floating.resource = None
            floating.save()
    except:
        return Response({"success": False, "msg": _(
              'failed.')})
    instance.deleted = True
    instance.save()
    return Response({"success": True, "msg": _(
           'Sucess.')})
