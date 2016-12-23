# -*- coding:utf8 -*-

# Author Yang

from datetime import datetime
import logging
import json

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
#from biz.networkmanager.models import Networkmanager 
#from biz.networkmanager.serializer import NetworkmanagerSerializer
from biz.networkmanager.utils import * 
from biz.idc.models import DataCenter
from biz.common.pagination import PagePagination
from biz.common.decorators import require_POST, require_GET
from biz.common.utils import retrieve_params, fail
from biz.workflow.models import Step
from cloud.tasks import (link_user_to_dc_task, send_notifications,
                         send_notifications_by_data_center)
from cloud.cloud_utils import create_rc_by_dc
from cloud.api import neutron
from frontend.forms import CloudUserCreateFormWithoutCapatcha

LOG = logging.getLogger(__name__)


class NetworkmanagerList(generics.ListAPIView):
    def list(self, request):

        datacenter = DataCenter.get_default()
        rc = create_rc_by_dc(datacenter)
        networks = neutron.network_list(rc)
        data = []
        for network in networks:
            LOG.info("1")
            admin_state_up = network.admin_state_up
            LOG.info("1")
            if admin_state_up:
                admin_state_up = "启用"
            data.append({"id":network.id, "name": network.name, "admin_state_up": admin_state_up, "tenant_id": network.tenant_id})
            LOG.info("1")
        LOG.info(" data is " + str(data))
        return Response(data)

@api_view(['POST'])
def batch_delete(request):

    LOG.info("**** start to delete network ****")
    datacenter = DataCenter.get_default()
    rc = create_rc_by_dc(datacenter)
    LOG.info(request.data)
    network_id = request.data['ids[]']
    LOG.info(network_id)
    neutron.network_delete(rc, network_id)
    return Response({"OPERATION_STATUS": 1,
                         "MSG": _("Creating network")})

def _create_network(rc, network_name, admin_state_up, physnet, seg_id, tenant, network_type):
    LOG.info("start to create network")

    if admin_state_up == 'up':
        admin_state_up = 'True'
    try:
        params = {'name': network_name, 'provider:physical_network': physnet, 'tenant_id': tenant, 'provider:network_type': network_type,'admin_state_up': admin_state_up, 'provider:segmentation_id': seg_id}
        LOG.info("params" + str(params))
        network = neutron.network_create(rc, **params)
        msg = ('Network was successfully created.')
        LOG.info(msg)
        return network
    except Exception as e:
        return False


def _create_subnet(rc, subnet_name, cidr, ip_version, gateway, enable_gateway, enable_dhcp, allocation_polls, dns_server, network_id, network_name, host_router, tenant):


    LOG.info("*** start to create subnet ***")
    try:
        params = {'network_id': network_id,
                      'name': subnet_name}

        params['cidr'] = cidr

        if ip_version == 'ipv4':
            ip_version = '4'
        else:
            ip_version = '6'

        params['ip_version'] = int(ip_version)

        if enable_gateway == 'up':
            params['gateway_ip'] = gateway
        else:
            params['gateway_ip'] = None


        params['enable_dhcp'] = True
        if allocation_polls:
            pools = [dict(zip(['start', 'end'], pool.strip().split(',')))
                     for pool in allocation_polls.split('\n')
                     if pool.strip()]
            params['allocation_pools'] = pools
        LOG.info("cccc")

        if host_router:
            routes = [dict(zip(['destination', 'nexthop'],
                               route.strip().split(',')))
                      for route in host_router.split('\n')
                      if route.strip()]
            params['host_routes'] = routes

        LOG.info("cccc")

        if dns_server:
            nameservers = [ns.strip()
                           for ns in dns_server.split('\n')
                           if ns.strip()]
            params['dns_nameservers'] = nameservers

        LOG.info("cccc")
        if tenant:
            params['tenant_id'] = tenant

        LOG.info("**** start to create subnet 8**")
        subnet = neutron.create_subnet(rc, **params)
        msg = ('Subnet was successfully created.')
        LOG.info(msg)
        return subnet
    except Exception as e:
        msg = ('Failed to create subnet for network')
        LOG.info(e)
        return False


@api_view(['POST'])
def create_network(request):

    #udc_id = request.session['UDC_ID']
    #UDC = UserDataCenter.objects.get(pk=udc_id)
    #tenant_id = UDC.tenant_uuid
    #rc = create_rc_by_udc(UDC)

    datacenter = DataCenter.get_default()
    rc = create_rc_by_dc(datacenter)
    LOG.info("*********** data is *************" + str(request.data))

    network_name = request.data['network_name']
    LOG.info(network_name)
    tenant = request.data['tenant']
    LOG.info(tenant)
    physnet = request.data['physnet']
    LOG.info(physnet)
    seg_id = request.data['seg_id']
    LOG.info(seg_id)
    subnet_name = request.data['subnet_name']
    LOG.info(subnet_name)
    status = request.data['status'] or 'up'
    LOG.info("**** status is ****" + str(status))
    cidr = request.data['cidr']
    LOG.info(cidr)
    ip_version = request.data['ip_version'] or 'ipv4'
    LOG.info(ip_version)
    gateway = request.data['gateway']
    LOG.info(gateway)
    enable_gateway = request.data['enable_gateway'] or 'up'
    LOG.info(enable_gateway)
    enable_dhcp = request.data['enable_dhcp'] or 'up'
    LOG.info(enable_dhcp)
    allocation_polls = request.data['allocation_polls']
    LOG.info(allocation_polls)
    dns_server = request.data['dns_server']
    LOG.info(dns_server)
    host_router = request.data['host_router']
    LOG.info(host_router)

    admin_state_up = status

    network_type = "vlan"
    network = _create_network(rc, network_name, admin_state_up, physnet, seg_id, tenant, network_type)
    LOG.info("**** network is ****" + str(network))

    network_id = network.id
    LOG.info(network_id)
    network_name = network.name
    LOG.info(network_name)
    LOG.info(tenant)
    try:
        subnet = _create_subnet(rc, subnet_name, cidr, ip_version, gateway, enable_gateway, enable_dhcp, allocation_polls, dns_server, network_id, network_name, host_router, tenant)
    except Exception as e:
        LOG.info(e)
    LOG.info("*** subnet is ***" + str(subnet))
    if not subnet:
        neutron.network_delete(rc, network.id)
        return Response({"OPERATION_STATUS": 0,
                         "MSG": _('Network address exists')})

    LOG.info(" start to save network info in db *****")
    return Response({"OPERATION_STATUS": 1,
                         "MSG": _("Creating network")})


"""

@require_POST
def create_networkmanager(request):

    try:
        serializer = NetworkmanagerSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, "msg": _('Networkmanager is created successfully!')},
                            status=status.HTTP_201_CREATED)
        else:
            return Response({"success": False, "msg": _('Networkmanager data is not valid!'),
                             'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:

        LOG.error("Failed to create flavor, msg:[%s]" % e)
        return Response({"success": False, "msg": _('Failed to create networkmanager for unknown reason.')})



@api_view(["POST"])
def delete_networkmanagers(request):
    ids = request.data.getlist('ids[]')
    Networkmanager.objects.filter(pk__in=ids).delete()
    return Response({'success': True, "msg": _('Networkmanagers have been deleted!')}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def update_networkmanager(request):
    try:

        pk = request.data['id']
        LOG.info("---- networkmanager pk is --------" + str(pk))

        networkmanager = Networkmanager.objects.get(pk=pk)
        LOG.info("ddddddddddddd")
        LOG.info("request.data is" + str(request.data))
        networkmanager.networkmanagername = request.data['networkmanagername']

        LOG.info("dddddddddddd")
        networkmanager.save()
        #Operation.log(networkmanager, networkmanager.name, 'update', udc=networkmanager.udc,
        #              user=request.user)

        return Response(
            {'success': True, "msg": _('Networkmanager is updated successfully!')},
            status=status.HTTP_201_CREATED)

    except Exception as e:
        LOG.error("Failed to update networkmanager, msg:[%s]" % e)
        return Response({"success": False, "msg": _(
            'Failed to update networkmanager for unknown reason.')})


@require_GET
def is_networkmanagername_unique(request):
    networkmanagername = request.GET['networkmanagername']
    LOG.info("networkmanagername is" + str(networkmanagername))
    return Response(not Networkmanager.objects.filter(networkmanagername=networkmanagername).exists())
"""
