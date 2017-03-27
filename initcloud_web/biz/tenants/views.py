# -*- coding:utf8 -*-

# Author Yang

import datetime
import logging

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
from biz.tenants.models import Tenants, Tenant_user 
from biz.tenants.serializer import TenantsSerializer
from biz.tenants.utils import * 
from biz.account.models import Contract
from biz.idc.models import DataCenter, UserDataCenter
from biz.common.pagination import PagePagination
from biz.common.decorators import require_POST, require_GET
from biz.common.utils import retrieve_params, fail
from cloud.api import keystone
from cloud.cloud_utils import create_rc_by_dc
from biz.workflow.models import Step
from cloud.tasks import (link_user_to_dc_task, send_notifications, keystone_list_users, user_delete,
                         send_notifications_by_data_center, project_create, project_delete, add_user_tenants)
from cloud.network_task import edit_default_security_group
from frontend.forms import CloudUserCreateFormWithoutCapatcha

LOG = logging.getLogger(__name__)


class TenantsList(generics.ListAPIView):
    LOG.info("--------- I am tenants list in TenantsList ----------")
    def list(self, request):

        datacenter = DataCenter.get_default()
        LOG.info("****** signup get method ********")
        rc = create_rc_by_dc(datacenter)
        tenants = keystone.keystoneclient(rc).tenants.list()
        tenants_id = [] 
        for tenant in tenants:
            if str(tenant.name) not in ["demo", "services"]:
                tenants_id.append({'id': tenant.id, 'name': tenant.name, 'description': tenant.description})
        LOG.info("********* tenants_id is **************" + str(tenants_id))
        return Response(tenants_id)


class manageusers(generics.ListAPIView):

    def list(self, request, tenant_id):
        tenant_id = tenant_id
        tenant_users = UserDataCenter.objects.filter(tenant_uuid=tenant_id)
        #LOG.info("*** tenant_id is ***" + str(tenant_id)) 
        #datacenter = DataCenter.get_default()
        #rc = create_rc_by_dc(datacenter)
        #tenant_users = keystone.keystoneclient(rc).tenants.list_users(tenant_id)
        #LOG.info(" tenant_users " + str(tenant_users))
        users = []
        for user in tenant_users:
            LOG.info("user is " + str(user.user_id))
            user_ = User.objects.get(pk=user.user_id)
            LOG.info(" user_ is " + str(user_))
            enabled = None
            if user_.is_active:
                enabled = "激活"
            else:
                enabled = "未激活"
            users.append({'id': user.user_id, 'username': user_.username, 'email':user_.email, 'enabled': enabled , 'tenant_id': tenant_id})
        LOG.info("*** response users are ****" + str(users))
        return Response(users)


@require_POST
def create_tenants(request):


    try:

        tenant_name = request.data.get('name')
        tenant_description = request.data.get('description')
        LOG.info("*********** start to create role in openstack  role name is ***********" + str(tenant_name))
        created_project = project_create(request, tenant_name, tenant_description)
        LOG.info("************* create project is **********" + str(created_project))
    except:
        return Response({"success": False, "msg": _('Tenants data is not valid!'),
                          'errors': serializer.errors},
                         status=status.HTTP_400_BAD_REQUEST)
        return False

    try:
        serializer = Tenants(name=tenant_name, description=tenant_description, tenant_id=created_project)
  
        serializer.save()
        return Response({'success': True, "msg": _('Tenants is created successfully!')},
                         status=status.HTTP_201_CREATED)
    except Exception as e:

        LOG.error("Failed to create flavor, msg:[%s]" % e)
        return Response({"success": False, "msg": _('Failed to create tenants for unknown reason.')})


@api_view(["POST"])
def add_tenant_users(request):
    LOG.info(" request data is" + str(request.data))
    tenant_id = request.data['tenant_id']
    LOG.info("tenant_id is" + str(tenant_id))
    user_ids = request.data['users']
    LOG.info("tenant_id is" + str(user_ids))
    user_ids_split = user_ids.split(',')

    datacenter = DataCenter.get_default()
    LOG.info("****** signup get method ********")
    rc = create_rc_by_dc(datacenter)
    tenant = keystone.keystoneclient(rc).tenants.get(tenant_id)
    LOG.info("*** tenant is ***" + str(tenant))
    tenant_name = tenant.name

    ops_add = False
    try:
    
        for ID in user_ids_split:
            ID_split = ID.split('/')
            user_uuid = ID_split[0]
            user_id = ID_split[1]
            LOG.info(" ID is " + str(ID))
            add_user_tenants(request, tenant_id, user_uuid)
            #user_tenant = Tenant_user(user_id=user_id, user_uuid=user_uuid, tenant_id=tenant_id, tenant_name=tenant_name)
            #user_tenant.save()
            ex_udc = UserDataCenter.objects.filter(user_id=user_id)[0]
            LOG.info("**** ex_udc is ****" + str(ex_udc))
            pwd = ex_udc.keystone_password 
            LOG.info(pwd)
            keystone_user = ex_udc.keystone_user
            LOG.info(keystone_user)
            user = User.objects.get(pk=user_id)
            LOG.info(user)
            if UserDataCenter.objects.filter(user=user, tenant_name=tenant_name):
                return Response({'success': False, "msg": _('User has not been added!')}, status=status.HTTP_201_CREATED) 
            udc = UserDataCenter.objects.create(
                data_center=datacenter,
                user=user,
                tenant_name=tenant_name,
                tenant_uuid=tenant_id,
                keystone_user=keystone_user,
                keystone_user_id=user_uuid,
                keystone_password=pwd,
            )

            try:
                edit_default_security_group(user, udc)
                LOG.info("done with sc")
            except:
                LOG.exception("Failed to edit default security group for user[%s] in "
                         "data center[%s]", user.username, datacenter.name)

            Contract.objects.create(
            user=user,
            udc=udc,
            name=user.username,
            customer=user.username,
            start_date=datetime.datetime.now(),
            end_date=datetime.datetime.now(),
            deleted=False
            )
            LOG.info("done with contract")

    except:
        return Response({'success': False, "msg": _('User has been added!')}, status=status.HTTP_201_CREATED) 

    return Response({'success': True, "msg": _('User has been added!')}, status=status.HTTP_201_CREATED)



@api_view(["POST"])
def delete_tenants(request):
    ids = request.data.getlist('ids[]')
    LOG.info("ids are" + str(ids))
    for ID in ids:
        LOG.info(" ID is " + str(ID))
        deleted_project = project_delete(request, ID)
        Tenants.objects.filter(tenant_id=ID).delete()
    #Tenants.objects.filter(pk__in=ids).delete()
    return Response({'success': True, "msg": _('Tenants have been deleted!')}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def delete_users(request):
    LOG.info(" request data is " + str(request.data))
    ids = request.data.getlist('ids[]')
    LOG.info("ids are" + str(ids))
    tenant_id = request.data['tenant_id']
    LOG.info(' tenant_id is ' + str(tenant_id))
    for ID in ids:
        LOG.info(" ID is " + str(ID))
        deleted_user = user_delete(request, tenant_id, ID)
    return Response({'success': True, "msg": _('Users have been deleted from this tenant!')}, status=status.HTTP_201_CREATED)


class list_users(generics.ListAPIView):
    def list(self, request):
        LOG.info("*** start to list users ***")
        users_cloud = User.objects.filter(is_staff=False)
        LOG.info("*** users cloud are ***" + str(users_cloud))

        users = keystone_list_users(request)
        data = []
        for cloud_user in users_cloud:
            for user in users:
                if not cloud_user.is_staff and cloud_user.username == user.username:
                    LOG.info(" user is " + str(user))
                    username = user.username
                    data.append({'username': username, 'id': user.id, 'user_id': cloud_user.id})
        return Response(data)

"""
@api_view(['POST'])
def update_tenants(request):
    try:

        pk = request.data['id']
        LOG.info("---- tenants pk is --------" + str(pk))

        tenants = Tenants.objects.get(pk=pk)
        LOG.info("ddddddddddddd")
        LOG.info("request.data is" + str(request.data))
        tenants.tenantsname = request.data['tenantsname']

        LOG.info("dddddddddddd")
        tenants.save()
        #Operation.log(tenants, tenants.name, 'update', udc=tenants.udc,
        #              user=request.user)

        return Response(
            {'success': True, "msg": _('Tenants is updated successfully!')},
            status=status.HTTP_201_CREATED)

    except Exception as e:
        LOG.error("Failed to update tenants, msg:[%s]" % e)
        return Response({"success": False, "msg": _(
            'Failed to update tenants for unknown reason.')})


@require_GET
def is_tenantsname_unique(request):
    tenantsname = request.GET['tenantsname']
    LOG.info("tenantsname is" + str(tenantsname))
    return Response(not Tenants.objects.filter(tenantsname=tenantsname).exists())

"""
