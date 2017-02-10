#-*-coding-utf-8-*-

import logging

from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.db.utils import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from biz.account.models import Contract, UserProxy
from biz.idc.models import DataCenter
from biz.idc.serializer import DataCenter, DataCenterSerializer
from biz.instance.models import Instance, Flavor
from biz.image.models import Image
from cloud.cloud_utils import create_rc_by_dc
from cloud.tasks import hypervisor_stats_task
from cloud.api import keystone
from biz.idc.models import UserDataCenter
from django.conf import settings
import traceback
import datetime

LOG = logging.getLogger(__name__)


@api_view(["GET"])
def summary(request):
    LOG.info('-------------------- this is for admin UDC -------------------')
    try:
        user = User.objects.filter(username=request.user)[0]
        if user.is_superuser:
            dc = DataCenter.get_default()
            rc = create_rc_by_dc(dc)
            if not UserDataCenter.objects.filter(data_center=dc, user=user).exists():
                initcloud_tenant = "initcloud_" + user.username
                LOG.info(initcloud_tenant)
                tenant = keystone.tenant_create(rc, name=initcloud_tenant)
                LOG.info("--------- create tenant for superuser ---------")
                LOG.info(tenant)
                users = keystone.user_list(rc)
                for admin_user in users:
                    if admin_user.name == settings.ADMIN_NAME:
                        keystone.user_update_tenant(rc, admin_user, tenant)
                        for role in keystone.role_list(rc):
                            if role.name == 'admin':
                                role_id = role.id
                                keystone.add_tenant_user_role(rc, user=admin_user, role=role_id, project=tenant)
                #tenants = keystone.keystoneclient(rc).tenants.list()
                #for tenant in tenants:
                #    if tenant.name == settings.ADMIN_TENANT_NAME:
                #	admin_tenant_id = tenant.id
                #	admin_tenant_name = tenant.name
                #	LOG.info(tenant.name)
                #	LOG.info(tenant.id)
                admin_UDC = UserDataCenter.objects.create(data_center=dc,user=user,tenant_name=tenant.name,tenant_uuid = tenant.id,keystone_user=settings.ADMIN_NAME,keystone_password=settings.ADMIN_PASS)
                Contract.objects.create(user=user,udc=admin_UDC,name=user.username,customer=user.username,start_date=datetime.datetime.now(),end_date=datetime.datetime.now(),deleted=False)	
            #if not Contract.objects.filter(user=user).exists():
                #admin_UDC = UserDataCenter.objects.filter(data_center=dc, user=user)[0]
                #Contract.objects.create(user=user,udc=admin_UDC,name=user.username,customer=user.username,start_date=datetime.datetime.now(),end_date=datetime.datetime.now(),deleted=False)	
    except:
        traceback.print_exc()
    return Response({"user_num": User.objects.filter(is_superuser=False).count(),
                     "instance_num": Instance.objects.filter(deleted=False).count(),
                     "flavor_num": Flavor.objects.count(),
                     "data_center_num": DataCenter.objects.count(),
                     "contract_num": Contract.objects.filter(deleted=False).count(),
                     "image_num": Image.objects.count()})


@api_view(["POST"])
def init_data_center(request):

    params = {'name': request.data['name']}

    for key in ('host', 'project', 'user', 'password', 'auth_url', 'ext_net'):
        params[key] = request.data[key]

    try:
        data_center = DataCenter.objects.create(**params)
    except IntegrityError:
        return Response({'success': False,
                        "msg": _('The host IP is used by other Data Center, Please check your host IP.')},
                        status=status.HTTP_200_OK)
    except Exception as e:
        LOG.error("Failed to create data center, msg:[%s]" % e)
        return Response({'success': False,
                        "msg": _("Unknown Error happened when creating data center!"),
                        "resouce": "data_center"},
                        status=status.HTTP_200_OK)
    else:
        return Response({
            "success": True,
            'data': DataCenterSerializer(data_center).data,
            "msg": _("Data center is initialized successfully!")
        })


@api_view(['POST'])
def init_flavors(request):

    data = request.data
    names = data.getlist('names[]')
    cpus = data.getlist('cpus[]')
    memories = data.getlist('memories[]')
    prices = data.getlist('prices[]')

    try:
        for i in range(len(names)):
            Flavor.objects.create(name=names[i], cpu=cpus[i],
                                  memory=memories[i], price=prices[i])
    except Exception as e:
        LOG.error("Failed to create flavors, msg:[%s]" % e)
        return Response({'success': False,
                        "msg": _("Unknown Error happened when creating flavors!")},
                        status=status.HTTP_200_OK)
    else:
        return Response({"success": True, "msg": _("Flavors are initialized successfully!")})


@api_view(['POST'])
def init_images(request):

    data = request.data

    names = data.getlist('names[]')
    login_names = data.getlist('login_names[]')
    uuids = data.getlist('uuids[]')
    os_types = data.getlist('os_types[]')
    disk_sizes = data.getlist('disk_sizes[]')

    data_center = DataCenter.get_default()

    try:
        for i in range(len(names)):
            Image.objects.create(name=names[i], login_name=login_names[i],
                                 uuid=uuids[i], os_type=os_types[i],
                                 data_center=data_center,
                                 disk_size=disk_sizes[i])
    except Exception as e:
        LOG.exception("Failed to create images")
        return Response({'success': False,
                         "msg": _("Unknown Error happened when creating images!")},
                        status=status.HTTP_200_OK)
    else:
        return Response({"success": True,
                         "msg": _("Images are initialized successfully!")})


@api_view(['GET'])
def hypervisor_stats(request):

    user = request.user
    user_ = UserProxy.objects.get(pk=user.pk)
    
    if request.user.is_superuser or user_.is_system_user or user_.is_safety_user or user_.is_audit_user:
        data_center = DataCenter.get_default()
        stats = hypervisor_stats_task(data_center)
        if stats: 
            result = {
                "vcpus": stats.vcpus,
                "vcpus_used": stats.vcpus_used,
                "memory_mb": stats.memory_mb,
                "memory_mb_used": stats.memory_mb_used,
                "local_gb": stats.local_gb,
                "local_gb_used": stats.local_gb_used,
            } 
            return Response({"success": True, "stats": result})
        else:
            return Response({"success": False,
                             "msg": _("Hypervisor status is none.")})
    else:
        return Response({
            "success": False,
            "msg": _("Only super user can view the hypervisor status.")})
