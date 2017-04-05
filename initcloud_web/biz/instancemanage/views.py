#-*-coding-utf-8-*-

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
    queryset = Instance.objects.all().filter(deleted=False)
    serializer_class = InstanceSerializer

    def list(self, request):
        try:
	    # filter instances which assigned to users
            udc_id = request.session["UDC_ID"]
            if request.user.is_superuser:
                serializer = InstanceSerializer(self.queryset, many=True)
                return Response(serializer.data)

            """
            system = False
            security = False
            audit = False
            member = False
            UDC = UserDataCenter.objects.get(pk=udc_id)
            LOG.info(UDC)
            LOG.info("4")
            keystone_user_id = UDC.keystone_user_id
            LOG.info("4")
            tenant_uuid = UDC.tenant_uuid
            LOG.info("4")
            rc = create_rc_by_dc(DataCenter.objects.all()[0])
            LOG.info("4")
            user_roles = keystone.roles_for_user(rc, keystone_user_id, tenant_uuid)
            LOG.info("4")
            for user_role in user_roles:
                LOG.info("5")
                LOG.info(user_role.name)
                if user_role.name == "system":
                    LOG.info("5")
                    system = True
                    break
                if user_role.name == "security":
                    security = True
                    break
                if user_role.name == "audit":
                    audit = True
                    break

                if not system and not security and not audit:
                    member = True
            if system or security or audit:
                LOG.info("*** system user ***" + str(system))
                serializer = InstanceSerializer(self.queryset, many=True)
                return Response(serializer.data)
            """
            serializer = InstanceSerializer(self.queryset, many=True)
            return Response(serializer.data)
	    queryset = self.get_queryset().filter(user = request.user)
            serializer = self.serializer_class(queryset, many=True)
            #serializer = self.serializer_class(self.get_queryset(), many=True)
            LOG.info("********* serializer.data is ********" + str(serializer.data))
            return Response(serializer.data)
        except Exception as e:
            LOG.exception(e)
            return Response()

    def create(self, request, *args, **kwargs):
        raise NotImplementedError()

class InstancemanageDevicePolicy(generics.ListCreateAPIView):

    def list(self, request):
        LOG.info("dddddddddd")
        try:
            devicepolicy = settings.DEVICEPOLICY
            LOG.info("dddddddddd")
            return Response(devicepolicy)
        except Exception as e:
            LOG.exception(e)
            return Response()

    def create(self, request, *args, **kwargs):
        raise NotImplementedError()




@require_POST
def create_instancemanage(request):

    try:
        serializer = InstancemanageSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, "msg": _('Instancemanage is created successfully!')},
                            status=status.HTTP_201_CREATED)
        else:
            return Response({"success": False, "msg": _('Instancemanage data is not valid!'),
                             'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:

        LOG.error("Failed to create flavor, msg:[%s]" % e)
        return Response({"success": False, "msg": _('Failed to create instancemanage for unknown reason.')})



@api_view(["POST"])
def delete_instancemanages(request):
    LOG.info(" **** I am delete_instancemanages ****")
    ids = request.data.getlist('ids[]')
    ins_set = Instancemanage.objects.filter(pk__in=ids)
    for ins in ins_set:
	if Instance.objects.filter(uuid = ins.uuid).len > 1:
	    return Response({'success': False, "msg": _('Instance is assigned, please unassigned first!')})
	else:
    	    Instancemanage.objects.filter(pk__in=ids).delete()
    	    return Response({'success': True, "msg": _('Instancemanages have been deleted!')}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def update_instancemanage(request):
    try:

        pk = request.data['id']
        LOG.info("---- instancemanage pk is --------" + str(pk))

        instancemanage = Instancemanage.objects.get(pk=pk)
        LOG.info("ddddddddddddd")
        LOG.info("request.data is" + str(request.data))
        instancemanage.instancemanagename = request.data['instancemanagename']

        LOG.info("dddddddddddd")
        instancemanage.save()
        #Operation.log(instancemanage, instancemanage.name, 'update', udc=instancemanage.udc,
        #              user=request.user)

        return Response(
            {'success': True, "msg": _('Instancemanage is updated successfully!')},
            status=status.HTTP_201_CREATED)

    except Exception as e:
        LOG.error("Failed to update instancemanage, msg:[%s]" % e)
        return Response({"success": False, "msg": _(
            'Failed to update instancemanage for unknown reason.')})


@require_GET
def is_instancemanagename_unique(request):
    instancemanagename = request.GET['instancemanagename']
    LOG.info("instancemanagename is" + str(instancemanagename))
    return Response(not Instancemanage.objects.filter(instancemanagename=instancemanagename).exists())

@require_POST
def devicepolicyupdate(request):
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
    return Response({"success": True, "msg": _(
           'Sucess.')})

@require_POST
def devicepolicyundo(request):
    LOG.info("*** request.data is ***"  + str(request.data))
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
    LOG.info("aaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    LOG.info(request.data)
    LOG.info(request.data.getlist('ids[]'))
    for ID in request.data.getlist('ids[]'):
        instance_id = str(ID)
        instance = Instance.objects.get(pk=instance_id)
        instance_id = instance.uuid
        try:
            delete_user_instance_network(request, instance_id)
        except:
            pass
        try:
            LOG.info("resource is" + str(instance.id))
            #floating = Floating.objects.filter(resource=instance.id)[0]
            floating = Floating.objects.filter(resource=instance.id)
            LOG.info(" floating is " + str(floating))
            if floating:
                LOG.info("********")
                floating[0].resource = None
                LOG.info("********")
                floating[0].save()
                LOG.info("********")
        except:
            return Response({"success": False, "msg": _(
                  'failed.')})
        instance.deleted = True
        instance.save()
    return Response({"success": True, "msg": _(
               'Sucess.')})
@require_POST
def delete_instance(request):
    LOG.info("*** request.data is ***"  + str(request.data))
    instance_id = None
    for key, value in request.data.items():
        instance_id = value
    LOG.info("********** instance_id  is **********" + str(instance_id))
    instance = Instance.objects.get(pk=instance_id)
    instance_id = instance.uuid
    LOG.info("********** instance_id  is **********" + str(instance_id))
    try:
        delete_user_instance_network(request, instance_id)
    except:
        pass
    try:
        LOG.info("resource is" + str(instance.id))
        #floating = Floating.objects.filter(resource=instance.id)[0]
        floating = Floating.objects.filter(resource=instance.id)
        if floating:
            LOG.info("********")
            floating.resource = None
            LOG.info("********")
            floating.save()
            LOG.info("********")
    except:
        return Response({"success": False, "msg": _(
              'failed.')})
    instance.deleted = True
    instance.save()
    return Response({"success": True, "msg": _(
           'Sucess.')})
