#coding=utf-8

import re
import logging
import os
from bson import json_util
import subprocess
import uuid
from djproxy.views import HttpProxy
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth import authenticate, login

from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes)

from biz.volume.models import Volume
from biz.volume.serializer import VolumeSerializer
from biz.firewall.models import Firewall
from biz.firewall.serializer import FirewallSerializer
from biz.idc.models import UserDataCenter, DataCenter

from biz.instance.models import Instance, Flavor
from biz.instance.serializer import InstanceSerializer, FlavorSerializer
from biz.instance.utils import instance_action
from biz.instance.settings import (INSTANCE_STATES_DICT, INSTANCE_STATE_RUNNING,
                                   INSTANCE_STATE_APPLYING, MonitorInterval)
from biz.billing.models import Order
from biz.account.utils import check_quota
from biz.account.models import Operation
from biz.workflow.models import Workflow, FlowInstance
from biz.workflow.settings import ResourceType
from biz.network.models import Network

from biz.common.decorators import require_GET, require_POST
from django.views.decorators.http import require_POST as django_POST
from cloud.instance_task import (instance_create_task,
                                instance_get_console_log,
                                instance_get, instance_get_port)

from keystoneclient.v2_0 import client
from keystoneclient.auth.identity import v2
from keystoneclient import session
from novaclient.client import Client
from biz.common.views import IsSystemUser, IsAuditUser, IsSafetyUser
from cloud.cloud_utils import get_nova_admin
import traceback
from django.contrib.auth.models import User
from biz.account.serializer import UserSerializer
from biz.account.models import UserProxy
from biz.instance.utils import flavor_create, get_ins_status
from cloud.cloud_utils import create_rc_by_instance, create_rc_by_dc
from cloud.api import nova, keystone
import time
from django.db.models import Q

LOG = logging.getLogger(__name__)
OPERATION_SUCCESS = 1
OPERATION_FAILED = 0

class InstanceList(generics.ListCreateAPIView):
    """
    Normal user instance list interface
    """
    queryset = Instance.objects.all().filter(deleted=False)
    serializer_class = InstanceSerializer
    def list(self, request):
        try:
            udc_id = request.session["UDC_ID"]
            if request.user.is_superuser:
                serializer = InstanceSerializer(queryset, many=True)
                return Response(serializer.data)
      

            UDC = UserDataCenter.objects.all().filter(user=request.user)[0]
            project_id = UDC.tenant_uuid
            queryset = self.get_queryset().filter(
                Q(user=request.user, user_data_center__pk=udc_id) | Q(tenant_uuid=project_id) |Q(assigneduser=request.user))
            serializer = InstanceSerializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            LOG.exception(e)
            return Response()

    def create(self, request, *args, **kwargs):
        raise NotImplementedError()


class InstanceDetail(generics.RetrieveAPIView):
    """
    Get current instance detail 
    """
    queryset = Instance.objects.all().filter(deleted=False)
    serializer_class = InstanceSerializer

    def get(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
            if obj and obj.user == request.user:
                serializer = InstanceSerializer(obj)
                return Response(serializer.data)
            else:
                raise
        except Exception as e:
            LOG.exception(e)
            return Response(status=status.HTTP_404_NOT_FOUND)


class FlavorList(generics.ListCreateAPIView):
    """
    List all the flavors.Attention: These may not sync with openstack
    """
    queryset = Flavor.objects.all()
    serializer_class = FlavorSerializer

    def list(self, request):
        serializer = self.serializer_class(self.get_queryset(), many=True)
        return Response(serializer.data)


class FlavorDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    List the detailed info of one flavor
    """
    queryset = Flavor.objects.all()
    serializer_class = FlavorSerializer


def get_nova_admin(request):
    """
    Nova admin client 
    param: auth_url
    param: username
    param: password
    param: admin tenant name
    """
    # make v2 auth
    auth = v2.Password(auth_url=settings.AUTH_URL,
			username = settings.ADMIN_NAME,
			password = settings.ADMIN_PASS,
			tenant_name = settings.ADMIN_TENANT_NAME)
    # sess 
    sess = session.Session(auth=auth)
    # novaclient version is 2 currently
    novaClient = Client(settings.NOVA_VERSION, session = sess)
    return novaClient

@api_view(["POST"])
def create_flavor(request):
    """
    Create a new flavor.

    This flavor is synced with openstack 
    """
    try:
        serializer = FlavorSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
	    LOG.debug("************ CREATE FLAVOR ***************")
	    novaadmin = get_nova_admin(request)
	    mem = request.data.get("memory")
	    name = request.data.get("name")
	    cpu = request.data.get("cpu")
	    disk = request.data.get("disk")
            # Sync flavor creation with novaadmin
	    flavor = novaadmin.flavors.create(name = name , ram = mem, vcpus = cpu, disk = disk)
	    flavorid = flavor.id
	    try:
	    	serializer.save(flavorid = flavor.id)
	    except:
		traceback.print_exc()
	    LOG.debug(Flavor.objects.all().filter(flavorid = flavor.id))
	    
            return Response({'success': True, "msg": _('Flavor is created successfully!')},
                            status=status.HTTP_201_CREATED)
        else:
            return Response({"success": False, "msg": _('Flavor data is not valid!'),
                             'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        LOG.error("Failed to create flavor, msg:[%s]" % e)
        return Response({"success": False, "msg": _('Failed to create flavor for unknown reason.')})


@api_view(["POST"])
def update_flavor(request):
    """
    Update flavor info with requested param
    param: vcpu
    param: mem
    param: sys_disk
    param: name
    """
    try:
        flavor = Flavor.objects.get(pk=request.data['id'])
        serializer = FlavorSerializer(instance=flavor, data=request.data, context={"request": request})

        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, "msg": _('Flavor is updated successfully!')},
                            status=status.HTTP_201_CREATED)
        else:
            return Response({"success": False, "msg": _('Flavor data is not valid!'),
                             'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        LOG.error("Failed to create flavor, msg:[%s]" % e)
        return Response({"success": False, "msg": _('Failed to update flavor for unknown reason.')})


@api_view(["POST"])
def delete_flavors(request):
    """
    Delete flavor from db
    """
    ids = request.data.getlist('ids[]')
    LOG.info("*** ids are ***" + str(ids))
    Flavor.objects.filter(pk__in=ids).delete()
    return Response({'success': True, "msg": _('Flavors have been deleted!')}, status=status.HTTP_201_CREATED)


@check_quota(["instance", "vcpu", "memory"])
@api_view(["POST"])
def instance_create_view(request):
    """
    Instance create with param
    param: instance
    param: pay_type
    param: pay_num
    param: network_id
    param: name
    param: vcpu
    param: mem
    param: sys_disk
    """
    count = request.DATA.get("instance", u"1")
    try:
        count = int(count)
    except:
        count = 1

    user_id = request.user.id
    LOG.debug("** user_id is ***" + str(user_id))
    user_data_center = UserDataCenter.objects.filter(user__id=request.user.id)[0]
    LOG.info("*** user_data_center ***" + str(user_data_center))
    user_tenant_uuid = user_data_center.tenant_uuid
    LOG.debug("*** user_tenant_uuid is ***" + str(user_tenant_uuid))

    pay_type = request.data['pay_type']
    pay_num = int(request.data['pay_num'])

    # Instance batch creation limit
    if count > settings.BATCH_INSTANCE:
        return Response({"OPERATION_STATUS": OPERATION_FAILED},
                    status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    # Check if user has network_id
    network_id = request.DATA.get("network_id", u"0")
    try:
        network = Network.objects.get(pk=network_id)
    except Network.DoesNotExist:
        pass
    else:
        # VLAN mode: we do not have to add router to network.
        if settings.VLAN_ENABLED == False:
            if not network.router:
                msg = _("Your selected network has not linked to any router.")
                return Response({"OPERATION_STATUS": OPERATION_FAILED,
                               "msg": msg}, status=status.HTTP_409_CONFLICT)


    has_error, msg = False, None
    # Create multi instances
    for i in range(count):
        serializer = InstanceSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            name = request.DATA.get("name", "Server")
            if i > 0:
                # For multi instances.instance name generated format
                name = "%s-%04d" % (name, i)
            ins = serializer.save(name=name)

            # Operaion logic
            Operation.log(ins, obj_name=ins.name, action="launch", result=1)
            # Workflow logic
            workflow = Workflow.get_default(ResourceType.INSTANCE)

            # TODO: workflow
            if settings.SITE_CONFIG['WORKFLOW_ENABLED'] and workflow:
                ins.status = INSTANCE_STATE_APPLYING
                ins.save()

                FlowInstance.create(ins, request.user, workflow, request.DATA['password'])
                msg = _("Your application for instance \"%(instance_name)s\" is successful, "
                        "please waiting for approval result!") % {'instance_name': ins.name}
            else:
                # Delivery the request to celery
                instance_create_task.delay(ins, password=request.DATA["password"],user_tenant_uuid=user_tenant_uuid)
                Order.for_instance(ins, pay_type=pay_type, pay_num=pay_num)
                msg = _("Your instance is created, please wait for instance booting.")
        else:
            has_error = True
            break

    if has_error: 
        return Response({"OPERATION_STATUS": OPERATION_FAILED},
                        status=status.HTTP_400_BAD_REQUEST) 
    else:
        return Response({"OPERATION_STATUS": OPERATION_SUCCESS,
                          "msg": msg}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def is_name_unique(request):
    """
    Check instance name is unique or not
    """
    name = request.query_params['name']
    return Response(not Instance.objects.filter(name = name, deleted = False).exists())

@api_view(["POST"])
def instance_resize(request):
    """
    Resize instance with requested param

    param: id
    param: vcpu
    param: socket
    param: core
    param: sys_disk
    param: socket
    param: memory
    """
    ins = Instance.objects.get(id = request.data['id'])
    LOG.info(request.data)
    if ins.sys_disk > int(request.data['sys_disk']):
        return Response({"success":False, "msg":"Disk too smal.Please enter a bigger disk size."})
    if int(request.data['vcpu']) == ins.cpu and int(request.data['core']) == ins.core and int(request.data['socket']) == ins.socket and int(request.data['memory']) == ins.memory and int(request.data['sys_disk']) == ins.sys_disk:
	return Response({"success":False, "msg": "No change!"})
    org_cpu = ins.cpu
    org_core = ins.core
    org_socket = ins.socket
    org_memory = ins.memory
    org_sys_disk = ins.sys_disk
    ins.cpu = request.data['vcpu']
    ins.core = request.data['core']
    ins.socket = request.data['socket']
    ins.memory = request.data['memory']
    ins.sys_disk = request.data['sys_disk']
    ins.save()
    rc = create_rc_by_instance(ins)
    try:
        new_flavor = flavor_create(ins)
        # Get server info
	instance = nova.server_get(rc, ins.uuid)
	nova.server_resize(rc, ins.uuid, new_flavor)
        # Set instance status
	ins.status = 14
	ins.save()
    except Exception as e:
        ins.cpu = org_cpu
        ins.core = org_core
        ins.socket = org_socket
        ins.memory = org_memory
        ins.sys_disk = org_sys_disk
        ins.save()
        return Response({"success":False, "msg":str(e)})
    return Response({"success":True})

@api_view(["POST"])
def instance_verify_resize(request):
    """
    Verify instance resize action
    """
    ins = Instance.objects.get(id = request.data['id'])
    rc = create_rc_by_instance(ins)
    try:
	LOG.debug(request.data['action'])
	instance = nova.server_get(rc, ins.uuid)
	if request.data['action'] == 'confirm':
	    nova.server_confirm_resize(rc, ins.uuid)	
	elif request.data['action'] == 'revert':
	    nova.server_revert_resize(rc, ins.uuid)
	else:
	    return Response({"success":False, "msg":"Wrong action!!!"})
	time.sleep(3)
	instance = nova.server_get(rc, ins.uuid)
	ins.status = get_ins_status(instance)
        # Check instance status
	if ins.status == 99:
	    LOG.debug("--------------- WAIT --------------------")
	    ins.status = 11
	    return Response({"success":False, "msg":"Verify timeout!"})
        flavor = nova.flavor_get(rc, instance.flavor['id'])
        LOG.info(flavor.vcpus)
        LOG.info(flavor.ram)
        # Get flavor extras
        extra = nova.flavor_get_extras(rc, flavor.id, True)
        core = extra['hw:cpu_cores']
        socket = extra['hw:cpu_sockets']
        LOG.info(core)
        LOG.info(socket)

	ins.cpu = flavor.vcpus
	ins.memory = flavor.ram
	ins.core = core
	ins.socket = socket
	ins.status = get_ins_status(instance)
	ins.save()
	return Response({"success":True, "msg":"Verify resize!"})
    except:
	traceback.print_exc()
	return Response({"success":False, "msg":"Fail to verify resize!"})


@api_view(["POST"])
def instance_assignedusers(request):
    """
    Get instance assigned 
    """
    ins = Instance.objects.all().filter(uuid = request.data['uuid'], deleted = False)[0]
    try:
        user = ins.assigneduser
        assignuser = []
        assignuser.append(user)
        LOG.info(assignuser)
        serializer = UserSerializer(assignuser, many = True)
    except Exception as e:
       LOG.info("*** error is ***" + str(e))
       traceback.print_exc()
    return Response(serializer.data)

@api_view(["POST"])
def instance_unassignedusers(request):
    """
    Undo the instance assignment
    """
    ins = Instance.objects.all().filter(uuid = request.data['uuid'], deleted = False)[0]
    users = User.objects.all()
    # Get member users
    member_users = []
    for user in users:
        system = False
        security = False
        audit = False
        if user.last_name == "system":
            system = True
            break
        if user.last_name == "audit":
            audit = True
            break
        if user.last_name == "security":
            security = True
            break
        if not system and not security and not audit and not user.is_superuser:
            member_users.append(user)
    LOG.info(member_users)
    serializer = UserSerializer(member_users, many=True)
    return Response(serializer.data)

def assign_ins(request):
    try:    
        check_user = User.objects.get(id = request.data["assign"])
	ins = Instance.objects.get(id = request.data["id"], deleted = False)
        ins.assigneduser = check_user
        ins.save()
    except:
        pass
def unassign_ins(request):
    try:
        check_user = User.objects.get(id = request.data["unassign"])
        ins = Instance.objects.get(id = request.data["id"], deleted = False)
        ins.assigneduser = None
        ins.save()
    except:
        pass

@api_view(["POST"])
def instance_assign_instance(request):
    """
    Assing the instance to user
    """
    LOG.info(request.data)
    assign_ins(request)
    unassign_ins(request)
    return Response({'success': True, "msg": _('User have been assigned!')})


@api_view(["POST"])
def instance_action_view(request, pk):
    """
    Instance action view
    """
    instance_id, action = request.data['instance'], request.data['action']
    LOG.info(" action is " + str(request.data['action']))
    data = instance_action(request.user, instance_id, action)
    return Response(data)


@api_view(["GET"])
def instance_status_view(request):
    return Response(INSTANCE_STATES_DICT)


@api_view(["GET"])
def instance_search_view(request):
    """
    Search instance by user id
    """
    user_id = request.query_params.get('uid', None)
    LOG.info("*** user_id is ***" + str(user_id))
    LOG.info("*** user_id is ***" + str(request.query_params))
    if not user_id:
        LOG.debug(" user_id is none")
        UDC = UserDataCenter.objects.all().filter(user=request.user)[0]
        project_id = UDC.tenant_uuid
        instance_set = Instance.objects.filter(Q(deleted=False, user=request.user, status=INSTANCE_STATE_RUNNING,
            user_data_center=request.session["UDC_ID"]) | Q(tenant_uuid=project_id))
    else:
        LOG.debug("user id is not none")
        instance_set = Instance.objects.filter(deleted=False, assigneduser_id=user_id)

    serializer = InstanceSerializer(instance_set, many=True)
    return Response(serializer.data)

### TODO: remove below two API for qos


def qos_get_instance_detail(instance):
    instance_data = InstanceSerializer(instance).data

    try:
        server = instance_get(instance)
        instance_data['host'] = getattr(server, 'OS-EXT-SRV-ATTR:host', None)
        instance_data['instance_name'] = getattr(server,
                                'OS-EXT-SRV-ATTR:instance_name', None)
    except Exception as e:
        LOG.error("Obtain host fail,msg: %s" % e)
    try:
        ports = instance_get_port(instance)
        if ports:
            instance_data['port'] = ports[0].port_id
        else:
            instance_data['port'] = False
    except Exception as e:
        LOG.error("Obtain instance port fail,msg: %s" % e)

    try:
        from biz.floating.models import Floating
        floating = Floating.get_instance_ip(instance.id)
        if floating:
            instance_data["bandwidth"] = floating.bandwidth
        else:
            instance_data["bandwidth"] = settings.DEFAULT_BANDWIDTH
    except Exception as e:
        LOG.error("Obtain instance bandwidth fail,msg: %s" % e)

    return instance_data


@require_GET
@authentication_classes([])
@permission_classes([])
def instance_detail_view_via_uuid_or_ip(request, uuid_or_ip):
    """
    List instance detailed info by uuid or ip
    """
    instance_uuid = -1
    try:
        instance_uuid = uuid.UUID(uuid_or_ip) 
    except:
        pass

    try:
        if uuid_or_ip.count(".") == 3:
            from biz.floating.models import Floating
            floatings = Floating.objects.filter(ip=uuid_or_ip,
                                        deleted=False)
            if floatings.exists():
                if floatings[0].resource_type == "INSTANCE":
                    instance_uuid = Instance.objects.get(
                             pk=floatings[0].resource).uuid
    except:
        pass

    try:
        instance = Instance.objects.get(uuid=instance_uuid)
    except Instance.DoesNotExist:
        return Response({}, status=status.HTTP_404_NOT_FOUND)

    return Response(qos_get_instance_detail(instance))


@api_view(["GET"])
def instance_detail_view(request, pk):
    """
    Display instance details by tab
    Detailed info are instance_detail and instance_log 
    """
    tag = request.GET.get("tag", 'instance_detail')
    try:
        #instance = Instance.objects.get(pk=pk, user=request.user)
        instance = Instance.objects.get(pk=pk)
    except Exception as e:
        LOG.error("Get instance error, msg:%s" % e)
        return Response({"OPERATION_STATUS": 0, "MSG": "Instance no exist"}, status=status.HTTP_200_OK)

    if "instance_detail" == tag:
        return _get_instance_detail(instance)
    elif 'instance_log' == tag:
        log_data = instance_get_console_log(instance)
        return Response(log_data)


def _get_instance_detail(instance):
    """
    Actually do getting instance detail
    """

    instance_data = InstanceSerializer(instance).data

    try:
        # Get instance info from openstack
        server = instance_get(instance)
        # Get compute node instance running on
        instance_data['host'] = getattr(server, 'OS-EXT-SRV-ATTR:host', None)
        instance_data['instance_name'] = getattr(server,
                                'OS-EXT-SRV-ATTR:instance_name', None)
        instance_data['fault'] = getattr(server, 'fault', None)

    except Exception as e:
        LOG.error("Obtain host fail,msg: %s" % e)

    try:
        firewall = Firewall.objects.get(pk=instance.firewall_group.id)
        firewall_data = FirewallSerializer(firewall).data
        instance_data['firewall'] = firewall_data
    except Exception as e:
        LOG.exception("Obtain firewall fail, msg:%s" % e)

    # 挂载的所有硬盘
    volume_set = Volume.objects.filter(instance=instance, deleted=False)
    volume_data = VolumeSerializer(volume_set, many=True).data
    instance_data['volume_list'] = volume_data

    return Response(instance_data)

#update by dongdong
@api_view(["GET"])
def vdi_view(request):
    """
    This is the vdi interface for contact with foldex
    """
    LOG.debug("****** i am vdi view with method get ********")

    #queryset = Instance.objects.all().filter(deleted=False, user_id=request.user.id)
    queryset = Instance.objects.all().filter(deleted=False, assigneduser_id=request.user.id)
    LOG.info("queryset is" + str(queryset))
    json_value = {}
    count = 0 
    method = "responseUserCheck"
    retvalue = "0"
    vminfo = []
    for q in queryset:
        LOG.info("****** q is *****" + str(q))
        novaAdmin = get_nova_admin(request)
        LOG.debug(str(q.uuid))
        if not q.uuid:
            continue
        try:
            # Get instance info from openstack admin
            server = novaAdmin.servers.get(q.uuid)
        except:
            continue
        server_dict = server.to_dict()
        server_host = server_dict['OS-EXT-SRV-ATTR:host']
        LOG.info("servier_dict" + str(server_dict))
        LOG.info("******* server_status is *******" + str(server_host))
        server_status = server_dict['status']
        LOG.info("******* server_status is *******" + str(server_status))
        if server_status == "ERROR":
            continue
        # Filter the compute hostname
        host_ip = settings.COMPUTE_HOSTS[server_host]
        LOG.info("host ip is" + str(host_ip))
        # virsh remote connection
        cmd="virsh -c qemu+tcp://" + host_ip + "/system vncdisplay " + q.uuid
        LOG.info("cmd=" + cmd)
        # Get instance vnc port by sys command
        p = subprocess.Popen("virsh -c qemu+tcp://" + host_ip + "/system vncdisplay " + q.uuid, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        port = None
        for line in p.stdout.readlines():
            port = line
            break
        LOG.info("host_ip=" + host_ip)
        LOG.info("port=" + str(port))
        if "error" in str(port):
            public_ip = ''
            if settings.FLAT:
                public_ip = q.private_ip
            else:
                public_ip = q.public_ip
            vminfo.append({"vm_uuid": q.uuid, "vm_public_ip": public_ip, "vm_serverip": host_ip, "vm_status": server_status, "vnc_port": "no port", "vm_internalid": str(q.id), "policy_device": str(q.policy), "device_id": str(q.device_id), "vm_name": q.name})
            count = count + 1
            continue
        # Get spice port by vnc port
        split_port = port.split(":")
        port_1 = split_port[1]
        port_2 = port_1.split("\\")
        port_3 = port_2[0]
        vnc_port = 5900 + int(port_3)
        public_ip = ''
        if settings.FLAT:
            public_ip = q.private_ip
        else:
            public_ip = q.public_ip
        LOG.info("*** public_ip is ****" + str(public_ip))
        vminfo.append({"vm_uuid": q.uuid, "vm_public_ip": public_ip, "vm_serverip": host_ip, "vm_status": server_status, "vnc_port": vnc_port, "vm_internalid": str(q.id), "policy_device": str(q.policy), "device_id": str(q.device_id), "vm_name": q.name})
        LOG.info("*** count is ***" + str(count))
        count = count + 1
    LOG.info("count done")
    # Return value
    json_value = {"method": method, "retvalue": retvalue, "vmnum": count, "vminfo": vminfo}
    LOG.info(str(json_value))
    if not json_value:
        LOG.info("auth")
        json_value = {"retval": 1, "message": "auth success"}
    LOG.info(" before return") 
    return Response(json_value)

@api_view(["POST"])
def instance_action_view(request, pk):
    """
    Instance action view
    """
    instance_id, action = request.data['instance'], request.data['action']
    LOG.debug("instance id is" + str(instance_id))
    LOG.debug("action is" + str(action))
    data = instance_action(request.user, instance_id, action)
    return Response(data)

@api_view(["GET"])
def instance_action_vdi_view(request):
    """
    VDI Action view.
    Method is get
    """
    instance_id = request.GET.get('instance')
    action = request.GET.get('action')
    #instance_id, action = request.data['instance'], request.data['action']
    LOG.info("instance id is" + str(instance_id))
    LOG.info("action is" + str(action))
    data = instance_action(request.user, instance_id, action)
    return Response(data)


@require_GET
def monitor_settings(request):
    ## TODO: Monitor settings
    LOG.info("------------ MONITOR FOR INSTANCE DETAIL! -------------------")
    monitor_config = settings.MONITOR_CONFIG.copy()
    monitor_config['intervals'] = MonitorInterval.\
        filter_options(monitor_config['intervals'])

    monitor_config.pop('base_url')

    return Response(monitor_config)


class MonitorProxy(HttpProxy):
    ## TODO: Monitor settings
    base_url = settings.MONITOR_CONFIG['base_url']

    forbidden_pattern = re.compile(r"elasticsearch/.kibana/visualization/")

    def proxy(self):
        url = self.kwargs.get('url', '')

        if self.forbidden_pattern.search(url):
            return HttpResponse('', status=status.HTTP_403_FORBIDDEN)

        return super(MonitorProxy, self).proxy()

@csrf_exempt
@api_view(["GET"])
def new_vdi_test(request):
    ## Test scripts should remvoe from this file
    LOG.info("start to get data")
    method = request.GET.get("method")
    retval = 0 
    if method == "requestCheckUser":
        LOG.info("** method is ***" + str(method))
        username = request.GET.get("username")
        password = request.GET.get("password")
        LOG.info("*** username is ***" + str(username))
        LOG.info("*** user password is ***" + str(password))
        user = authenticate(username=username, password=password)
        if user is not None:
            # the password verified for the user
            if user.is_active:
                login(request, user)
                LOG.info("*** user is active")
                retval = 1
            else:
                retval = -1
                LOG.info("*** user is not active")
        else:
            retval = -2
            LOG.info("*** auth failed ***")

 
    response_value = {"status": retval}
    LOG.info("*** start to return ***")
    username = "klkl"
    password = "ydd1121NN"
    user = authenticate(username=username, password=password)
    login(request, user)

    LOG.info("*** user is ***" + str(request.user))
    if user.is_authenticated:
        LOG.info("user is authenticated")
    queryset = Instance.objects.all().filter(deleted=False, user_id=request.user.id)
    json_value = {}
    for q in queryset:
        LOG.info("******")
        novaAdmin = get_nova_admin(request)
        LOG.info("******")
        if not q.uuid:
            continue
        server = novaAdmin.servers.get(q.uuid)
        LOG.info("******")
        server_dict = server.to_dict()
        LOG.info("******")
        server_host = server_dict['OS-EXT-SRV-ATTR:host']
        server_status = server_dict['status']
        LOG.info("******* server_status is *******" + str(server_status))
        if server_status == "ERROR":
            continue
        host_ip = settings.COMPUTE_HOSTS[server_host]
        LOG.info("host ip is" + str(host_ip))
        cmd="virsh -c qemu+tcp://" + host_ip + "/system vncdisplay " + q.uuid
        LOG.info("cmd=" + cmd)
        p = subprocess.Popen("virsh -c qemu+tcp://" + host_ip + "/system vncdisplay " + q.uuid, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        port = None
        for line in p.stdout.readlines():
            port = line
            break
        LOG.info("host_ip=" + host_ip)
        LOG.info("port=" + str(port))
        if "error" in str(port):
            json_value[str(q.id)] = {"vm_uuid": q.uuid, "vm_private_ip": q.private_ip, "vm_public_ip": q.public_ip, "vm_host": host_ip, "vm_status": server_status, "policy_device": str(q.policy), "vnc_port": "no port", "vm_internalid": str(q.id), "vm_name": q.name}

            continue
        split_port = port.split(":")
        port_1 = split_port[1]
        port_2 = port_1.split("\\")
        port_3 = port_2[0]
        vnc_port = 5900 + int(port_3)
        json_value[str(q.id)] = {"vm_uuid": q.uuid, "vm_private_ip": q.private_ip, "vm_public_ip": q.public_ip, "vm_host": host_ip, "vm_status": server_status, "policy_device": str(q.policy), "vnc_port": vnc_port, "vm_internalid": str(q.id), "vm_name": q.name}
    LOG.info("*** json_value ***" + str(json_value))
    return json_util.loads(json_value)

def user_is_not_active(request):
    return Response({"status": "-1", "message": "failed"})

def user_auth_failed(request):
    return Response({"status": "-1", "message": "failed"})

def new_vdi(request):
    ## TODO: remvoe this function to tests
    LOG.info("start to get data")
    method = request.GET.get("method")
    retval = 0
    if method == "requestCheckUser":
        LOG.info("** method is ***" + str(method))
        username = request.GET.get("username")
        password = request.GET.get("password")
        LOG.info("*** username is ***" + str(username))
        LOG.info("*** user password is ***" + str(password))
        user = authenticate(username=username, password=password)
        if user is not None:
            # the password verified for the user
            if user.is_active:
                login(request, user)
                LOG.info("*** user is active")
                retval = 1
            else:
                retval = -1
                LOG.info("*** user is not active")
        else:
            retval = -2
            LOG.info("*** auth failed ***")
    if retval == 1:
        json_value = vdi_view(request)
    if retval == -1:
        json_value = user_is_not_active(request)
    if retval == -2:
        json_value = user_auth_failed(request)
    return json_value

monitor_proxy = login_required(csrf_exempt(MonitorProxy.as_view()))


# get instance security class changing status
@require_GET
def instance_sec_status(request):
    ins_id = request.query_params.get("vm")
    try:
        ins = Instance.objects.get(id=ins_id)
        return Response({'status': ins.security_cls})
    except Exception, e:
        LOG.info("Instance sec status error: %s" % e)
        return Response({'success': False})


def batch_create(request, user_id):
    ## Normal user batch delete interface
    LOG.info("** user_id is ***" + str(user_id))
    user_data_center = UserDataCenter.objects.filter(user__id=request.user.id)[0]
    LOG.info("*** user_data_center ***" + str(user_data_center))
    user_tenant_uuid = user_data_center.tenant_uuid
    LOG.info("*** user_tenant_uuid is ***" + str(user_tenant_uuid))

    pay_type = request.data['pay_type']
    pay_num = int(request.data['pay_num'])


    network_id = request.DATA.get("network_id", u"0")
    try:
        network = Network.objects.get(pk=network_id)
    except Network.DoesNotExist:
        pass
    else:
        # VLAN mode: we do not have to add router to network.
        if settings.VLAN_ENABLED == False:
            if not network.router:
                msg = _("Your selected network has not linked to any router.")
                return Response({"OPERATION_STATUS": OPERATION_FAILED,
                               "msg": msg}, status=status.HTTP_409_CONFLICT)
    has_error, msg = False, None
    user = User.objects.all().get(id = user_id)
    username = user.username
    serializer = InstanceSerializer(data=request.data, context={"request": request})
    if serializer.is_valid():
        name = request.DATA.get("name", "Server")
        name = "%s-%s" % (name, username)
        #name = "%s-%04d" % (name, i)
        LOG.info(name)
        ins = serializer.save(name=name, assigneduser=user)
        Operation.log(ins, obj_name=ins.name, action="launch", result=1)
        workflow = Workflow.get_default(ResourceType.INSTANCE)
        instance_create_task.delay(ins, password=request.DATA["password"],user_tenant_uuid=user_tenant_uuid)
        Order.for_instance(ins, pay_type=pay_type, pay_num=pay_num)
         
        #msg = _("Your instance is created, please wait for instance booting.")
    else:
        has_error = True
    if has_error: 
        return {'name':name, 'user':user_id, 'status':'failed'}
    else:
        return {'name':name, 'user':user_id, 'status':'succeed'}


@check_quota(["instance", "vcpu", "memory"])
@api_view(["POST"])
def instance_batch_create_view(request):
    ## Normal user batch creaet view
    LOG.info(request.data)
    user_ids = request.data.getlist('user_ids[]')
    LOG.info(user_ids)
    LOG.info(len(user_ids))
    if len(user_ids) > settings.BATCH_INSTANCE:
        return Response({"OPERATION_STATUS": OPERATION_FAILED},
                    status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    response = ''
    error_flag = False
    for user_id in user_ids:
        result = batch_create(request, user_id)
        result_str = result['name'] + ' id:' + str(result['user']) + ' create ' + result['status'] + '. '
        response = response + result_str
        if result['status'] == 'failed':
            error_flag = True
    LOG.info(response)
    LOG.info(error_flag)
    if error_flag:
        return Response({'success':False, "msg":response})
    return Response({"OPERATION_STATUS":1, "msg":response})


@require_GET
def instance_action_status(request):
     vm_name = request.query_params.get("vm")
     LOG.info("*** vm_name is ***" + str(vm_name))
     instance = Instance.objects.filter(name=vm_name,deleted=0)[0]
     return Response({"msg": instance.status_reason, "status": instance.status})
