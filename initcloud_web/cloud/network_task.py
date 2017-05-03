#-*- coding=utf-8 -*- 

import datetime
import logging
import random
import time

from django.conf import settings

from celery import app
from cloud_utils import (create_rc_by_network, create_rc_by_subnet,
                         create_rc_by_router, create_rc_by_floating,
                         create_rc_by_security,  create_rc_by_udc)

from biz.network.models import Network, Subnet, Router, RouterInterface
from biz.firewall.models import Firewall, FirewallRules
from biz.floating.settings import (FLOATING_AVAILABLE, FLOATING_RELEASED,
                                   FLOATING_BINDED, FLOATING_ERROR,
                                   RESOURCE_TYPE)
from biz.network.settings import NETWORK_STATE_ACTIVE, NETWORK_STATE_ERROR, \
                        NETWORK_STATE_BUILD, NETWORK_STATE_ACTIVE

from biz.instance.models import Instance
from biz.floating.models import Floating
from biz.lbaas.models import BalancerPool
from biz.lbaas.models import BalancerVIP
from biz.billing.models import Order

from cloud import billing_task
from api import neutron
from api import network

LOG = logging.getLogger(__name__)



# Logic: first we try to query network info in openstack and create a new network,including router if not existing. 
def make_sure_default_private_network(instance, rc, user_tenant_uuid):
    network = None
    try:
        network = Network.objects.get(pk=instance.network_id)
    except Network.DoesNotExist:
        LOG.info("network not exist")
        pass

    default_private_network = None
    default_private_subnet = None
    default_router = None

    # Try to get default network
    default_private_networks = Network.objects.filter(deleted=False,
        is_default=True, status__in=[NETWORK_STATE_BUILD, NETWORK_STATE_ACTIVE],
        user=instance.user, user_data_center=instance.user_data_center)
    
    if not default_private_networks.exists():
        LOG.info("*** default private network not exists in initcloud. Going to confirm if it exists in neutron***")
        sleeping = random.uniform(0.4, 5.5)
        time.sleep(sleeping)
        LOG.info("No default network [%s][%s], sleep [%s] seconds",
                instance.user_data_center.tenant_name, instance.name, sleeping)


        default_private_networks = Network.objects.filter(deleted=False,
            is_default=True, status__in=[NETWORK_STATE_BUILD, NETWORK_STATE_ACTIVE],
            user=instance.user, user_data_center=instance.user_data_center)

        # No default network exists, create a new one.
        if not default_private_networks.exists(): 

            LOG.info("*** no default network in initcloud. GOing to confirm if it exists in neutron ***")
            LOG.info("*** vlan enabled or not ***" + str(settings.VLAN_ENABLED))
            if settings.VLAN_ENABLED == True:
                LOG.info("*** vlan enabled ***")
                LOG.info("Double check no default vlan network [%s][%s].",
                        instance.user_data_center.tenant_name, instance.name)
                begin = datetime.datetime.now()
                network_ = neutron.network_list_for_tenant(rc, tenant_id=user_tenant_uuid)
                LOG.info("********** network is ******************" + str(network_))
                network_id = None
                network_name = None
                network_status = None
                subnet_id = None
                subnet_name = None
                subnet_addr = None
                for net in network_:
                    LOG.info("***** net is *******" + str(net))
                    network_id = net.id
                    network_name = net.name
                    network_status = net.admin_state_up
                    subnet = net.subnets
                    for s in subnet:
                        subnet_name = s.name
                        subnet_id = s.id
                        subnet_addr = s.cidr
                LOG.debug("********* network_id is *********" + str(network_id))
                LOG.debug("********* network_name is *********" + str(network_name))
                LOG.debug("********* network_status is *********" + str(network_status))
                LOG.debug("********* subnet_id is *********" + str(subnet_id))
                LOG.debug("********* subnet_name is *********" + str(subnet_name))
                LOG.debug("********* subnet_addr is *********" + str(subnet_addr))
                # Create Default network to initcloud
                default_private_network = Network.objects.create(
                    name=network_name, network_id=network_id, status=network_status,
                    is_default=True, user=instance.user,
                    user_data_center=instance.user_data_center)

                LOG.info("*** default private network create success ***")
                address = None
                for i in xrange(255):
                    tmp_address = settings.TENANT_DEFAULT_NETWORK
                    if not Subnet.objects.filter(user=instance.user,
                                deleted=False, address=tmp_address,
                                user_data_center=instance.user_data_center).exists():
                        address = tmp_address
                        break
                if not address:
                    address = settings.TENANT_DEFAULT_NETWORK 
                # Create default private subnet to initcloud
                default_private_subnet = Subnet.objects.create(
                    name=subnet_name, network=default_private_network,
                    address=subnet_addr, ip_version=4, status=0, user=instance.user,
                    user_data_center=instance.user_data_center)

                LOG.info("*** default_private_subnet create success ***")

                end = datetime.datetime.now()
                LOG.info("Create vlan network db record apply [%s] seconds.",
                              (end-begin).seconds) 

            # User has not default network for vxlan.
            if settings.VLAN_ENABLED == False:

                LOG.info("*** vxlan mode is enabled ***")
                # Start check if network exists in neutron.

                network_ = neutron.network_list_for_tenant(rc, tenant_id=user_tenant_uuid)
                LOG.info("********** network is ******************" + str(network_))
                network_id = None
                network_name = None
                network_status = None
                subnet_id = None
                subnet_name = None
                subnet_addr = None
                for net in network_:
                    LOG.info("***** net is *******" + str(net))
                    network_id = net.id
                    network_name = net.name
                    network_status = net.admin_state_up
                    subnet = net.subnets
                    for s in subnet:
                        subnet_name = s.name
                        subnet_id = s.id
                        subnet_addr = s.cidr

                begin = datetime.datetime.now()
                LOG.info("********* network_status is *********" + str(network_status))

                # User has network in neutron
                if network_name and network_id:
                    LOG.info("*** vxlan user has network in neutron ***")
                    default_private_network = Network.objects.create(
                        name=network_name, network_id=network_id, status=network_status,
                        is_default=True, user=instance.user,
                        user_data_center=instance.user_data_center)

                    # If network exists, check subnet exists or not.
                   
                    # If subnet exists, store data in initcloud.
                    if subnet_id and subnet_name:

                        LOG.info("*** vxlan user has subnet in neutron ***")
                        address = None
                        for i in xrange(255):
                            tmp_address = settings.TENANT_DEFAULT_NETWORK
                            if not Subnet.objects.filter(user=instance.user,
                                        deleted=False, address=tmp_address,
                                        user_data_center=instance.user_data_center).exists():
                                address = tmp_address
                                break
                        if not address:
                            address = settings.TENANT_DEFAULT_NETWORK
                        # Create default private subnet to initcloud
                        default_private_subnet = Subnet.objects.create(
                            name=subnet_name, network=default_private_network, subnet_id=subnet_id,
                            address=subnet_addr, ip_version=4, status=1, user=instance.user,
                            user_data_center=instance.user_data_center)

                        # Check if router exists.

                        neutron_subnets = neutron.subnet_list(rc, network_id=network_id)
                        for n in neutron_subnets:
                            LOG.info("*** n is ***" + str(n))
                        routers = neutron.router_list(rc, tenant_id=user_tenant_uuid)

                        neutron_subnet_id = None
                        neutron_router_id = None
                        neutron_router_name = None
                        external_gateway_info = None
                        external_fixed_ips = None
                        is_router = False
                        gateway_ip = None
                        for r in routers:
                            is_router = True
                            neutron_router_id = r.id
                            neutron_router_name = r.name
                            LOG.info("*** router is ***" + str(r))
                            external_gateway_info = r.external_gateway_info
                            LOG.info("*** external_gateway_info is ***" + str(external_gateway_info))
                            if external_gateway_info:
                                external_fixed_ips = external_gateway_info['external_fixed_ips']
                                if external_fixed_ips:
                                    for fip in external_fixed_ips:
                                        neutron_subnet_id = fip['subnet_id']
                                        gateway_ip = fip['ip_address']

                        ports = neutron.port_list(rc, network_id=network_id)
                        p_network_id = None
                        p_subnet_id = None
                        p_fixed_ips = None
                        os_port_id = None
                        for p in ports:
                            LOG.info("*** p is ***" + str(p))
                            os_port_id = p.id
                            if p.device_owner == "network:router_interface":
                                p_network_id = p.network_id
                                p_fixed_ips = p.fixed_ips
                                for f in p_fixed_ips:
                                    p_subnet_id = f['subnet_id'] 
                        LOG.info("*** gateway_ip is ***" + str(gateway_ip))
                        LOG.info("*** neutron_subnet_id is ***" + str(neutron_subnet_id))
                        LOG.info("*** subnet_id is ***" + str(subnet_id))

                        LOG.info("external_gateway_info is" + str(external_gateway_info))
                        LOG.info("external_fixed_ips is " + str(external_fixed_ips))
                        # router exists
                        if is_router and str(p_subnet_id) == str(subnet_id):
                            LOG.info("*** vxlan user has router exists ***")
                            # external_gateway exists
                            if external_gateway_info:
                                # external_fixed_ips exists, save router info to initcloud
                                if external_fixed_ips:
                                    LOG.info("***** ****************************** ***********")
                                    LOG.info("*** neutron_router_name ***" + str(neutron_router_name))
                                    LOG.info("*** neutron_router_id ***" + str(neutron_router_id))
                                    LOG.info("*** gateway_ip ***" + str(gateway_ip))
                                    default_router = Router.objects.create(
                                        name=str(neutron_router_name), status=1, 
                                        is_default=True,router_id=str(neutron_router_id), gateway=str(gateway_ip),
                                        is_gateway=settings.DEFAULT_ROUTER_AUTO_SET_GATEWAY, user=instance.user,
                                        user_data_center=instance.user_data_center)
                                    LOG.info("*** router create success ***")

                                    RouterInterface.objects.create(
                                    network_id=default_private_network.id, router_id=default_router.id, 
                                    subnet_id=default_private_subnet.id,
                                    user=instance.user, user_data_center=instance.user_data_center,
                                    os_port_id=str(os_port_id))

                                # external_fixed_ips does not exist
                                else:
                                    router_add_interface(rc, router_id=neutron_router_id, subnet_id=neutron_subnet_id)
                                    default_router = Router.objects.create(
                                        name=str(neutron_router_name), status=1,
                                        is_default=True,router_id=str(neutron_router_id), gateway=str(gateway_ip),
                                        is_gateway=settings.DEFAULT_ROUTER_AUTO_SET_GATEWAY, user=instance.user,
                                        user_data_center=instance.user_data_center)

                            # external_gateway does not exist
                            else:
                                router_gateway = neutron.router_add_gateway(rc, router_id=neutron_router_id, network_id=network_id)
                                router_add_interface(rc, router_id=neutron_router_id, subnet_id=neutron_subnet_id)

                                default_router = Router.objects.create(
                                        name=str(neutron_router_name), status=1,
                                        is_default=True,router_id=str(neutron_router_id), gateway=str(gateway_ip),
                                        is_gateway=settings.DEFAULT_ROUTER_AUTO_SET_GATEWAY, user=instance.user,
                                        user_data_center=instance.user_data_center)

                        # Router does not exist
                        else:
                            LOG.info("*** router does not exist ***")
                            default_router = Router.objects.create(
                                name=settings.DEFAULT_ROUTER_NAME, status=1, is_default=True,
                                is_gateway=settings.DEFAULT_ROUTER_AUTO_SET_GATEWAY, user=instance.user,
                                user_data_center=instance.user_data_center)

                            # Start to create real network in neutron
                            #begin = datetime.datetime.now()
                            #create_network(default_private_network)
                            #create_subnet(default_private_subnet)

                            router_create_task(default_router)
                            attach_network_to_router(default_private_network.id,
                                     default_router.id, default_private_subnet.id)

                    # Subnet not exists in neutron, create a subnet in neutron and store in the initcloud.
                    else:
                        LOG.info("*** vxlan subnet does not exists ***")
                        address = None
                        for i in xrange(255):
                            tmp_address = settings.TENANT_DEFAULT_NETWORK
                            if not Subnet.objects.filter(user=instance.user,
                                        deleted=False, address=tmp_address,
                                        user_data_center=instance.user_data_center).exists():
                                address = tmp_address
                                break
                        if not address:
                            address = settings.TENANT_DEFAULT_NETWORK
                        # Create default private subnet to initcloud
                        default_private_subnet = Subnet.objects.create(
                            name=settings.DEFAULT_SUBNET_NAME, network=default_private_network,
                            address=address, ip_version=4, status=0, user=instance.user,
                            user_data_center=instance.user_data_center)


                        default_router = Router.objects.create(
                            name=settings.DEFAULT_ROUTER_NAME, status=0, is_default=True,
                            is_gateway=settings.DEFAULT_ROUTER_AUTO_SET_GATEWAY, user=instance.user,
                            user_data_center=instance.user_data_center)

                        # Start to create real network in neutron
                        begin = datetime.datetime.now()
                        #create_network(default_private_network)
                        create_subnet(default_private_subnet)

                        router_create_task(default_router)
                        attach_network_to_router(default_private_network.id,
                                  default_router.id, default_private_subnet.id)

                # User has not network in neutron and initcloud.
                else:
                    LOG.info("*** vxlan user network does not exist ***")
                    default_private_network = Network.objects.create(
                        name=settings.DEFAULT_NETWORK_NAME, status=NETWORK_STATE_BUILD,
                        is_default=True, user=instance.user,
                        user_data_center=instance.user_data_center)

                    address = None
                    for i in xrange(255):
                        tmp_address = settings.TENANT_DEFAULT_NETWORK
                        if not Subnet.objects.filter(user=instance.user,
                                    deleted=False, address=tmp_address,
                                    user_data_center=instance.user_data_center).exists():
                            address = tmp_address
                            break
                    if not address:
                        address = settings.TENANT_DEFAULT_NETWORK
                    # Create default private subnet to initcloud
                    default_private_subnet = Subnet.objects.create(
                        name=settings.DEFAULT_SUBNET_NAME, network=default_private_network,
                        address=address, ip_version=4, status=0, user=instance.user,
                        user_data_center=instance.user_data_center)


                    default_router = Router.objects.create(
                        name=settings.DEFAULT_ROUTER_NAME, status=0, is_default=True,
                        is_gateway=settings.DEFAULT_ROUTER_AUTO_SET_GATEWAY, user=instance.user,
                        user_data_center=instance.user_data_center)

                    # Start to create real network in neutron
                    begin = datetime.datetime.now()
                    create_network(default_private_network)
                    create_subnet(default_private_subnet)
      

                    router_create_task(default_router)
                    attach_network_to_router(default_private_network.id,
                               default_router.id, default_private_subnet.id)
                    end = datetime.datetime.now()
                    LOG.info("Prepare private network api apply [%s] seconds.",
                                (end-begin).seconds) 
        else:
            LOG.info("Double check instance has default network [%s].", instance.name)
            default_private_network = default_private_networks[0]
    else:
        default_private_network = default_private_networks[0]
        LOG.info("Instance has default network, [%s][%s].",
                    instance, default_private_network)

    LOG.info(" *** i am two ***")
    if not network:
        network = default_private_network
    
    # Wait for network creation complete
    # Sync network creation
    count = 1
    while True:
        if count > settings.MAX_COUNT_SYNC:
            LOG.info("Network not active, instance:[%s] netowk:[%s]." %(
                        instance.name, network.name))
            break

        count = count + 1
        rc = create_rc_by_network(network)
        try:
            network = Network.objects.get(pk=network.id)
            if not network.network_id:
                time.sleep(settings.INSTANCE_SYNC_INTERVAL_SECOND)
                continue

            # Get network info and status
            net = neutron.network_get(rc, network.network_id)
            if net.status.upper() not in ["ACTIVE", ]:
                time.sleep(settings.INSTANCE_SYNC_INTERVAL_SECOND)
                continue 

            if net.subnets:
                break
            else:
                time.sleep(settings.INSTANCE_SYNC_INTERVAL_SECOND) 
        except:
            time.sleep(settings.INSTANCE_SYNC_INTERVAL_SECOND) 

    LOG.info("*** network is ***" + str(network))
    return network


# Task: create network in openstack
@app.task
def create_network(network):
    # Construct network auth info
    rc = create_rc_by_network(network)
    network_params = {'name': "network-%s" % network.id, "admin_state_up": True}
    LOG.info("Start to create network, id:[%s], name[%s]",
             network.id, network.name)
    begin = datetime.datetime.now()

    LOG.info("----------- rc is -------------" + str(rc))
    try:
        net = neutron.network_create(rc, **network_params)
        LOG.info("net create success")
        end = datetime.datetime.now()
        LOG.info("Create network api apply [%s] seconds", \
                    (end-begin).seconds) 
        network.network_id = net.id
        # Save network status in db
        network.status = NETWORK_STATE_ACTIVE
        network.save()
    except Exception as ex:
        end = datetime.datetime.now()
        LOG.info("Create network api apply [%s] seconds", \
                            (end-begin).seconds) 
        network.status = NETWORK_STATE_ERROR
        network.save()
        LOG.exception("Failed to create network, id:[%s], name[%s], "
                      "exception:[%s]",
                      network.id, network.name, ex)
        raise ex

    return network

# Task: delete the network in openstack
@app.task
def delete_network(network):
    # Construct auth info
    rc = create_rc_by_network(network)
    LOG.info("Start to delete network, id:[%s], name[%s]",
             network.id, network.name)
    try:

        subnet_set = Subnet.objects.filter(network_id=network.id, deleted=False)
        for subnet in subnet_set:
            delete_subnet(subnet)

        neutron.network_delete(rc, network.network_id)

        network.network_id = None
        # Set db 
        network.deleted = True
        network.save()
    except Exception as ex:
        network.status = NETWORK_STATE_ERROR
        network.save()
        LOG.exception("Failed to delete network, id:[%s], name[%s], msg:[%s]",
                      network.id, network.name, ex)
        raise ex

    return network

# Task: create a new subnet in openstack
@app.task
def create_subnet(subnet=None):
    rc = create_rc_by_subnet(subnet)
    LOG.info("subnet is" + str(subnet))
    LOG.info("subnet address is"+ str(subnet.address))

    # start to get gateway.
    sub_cidr = str(subnet.address)
    subnet_split = sub_cidr.split('/') 
    sub_addr = subnet_split[0]
    sub_addr_split = sub_addr.split('.')
    gateway = sub_addr_split[0] + "." + sub_addr_split[1] + "." + sub_addr_split[2] + ".1"
    LOG.debug("gateway is" + str(gateway)) 

    # Subnet params
    subnet_params = {"network_id": subnet.network.network_id,
                     "name": "subnet-%s" % subnet.id,
                     "cidr": subnet.address,
                     "ip_version": subnet.ip_version,
                     "dns_nameservers": settings.DNS_NAMESERVERS,
                     "gateway_ip": gateway,
                     "enable_dhcp": True}

    LOG.info("Start to create subnet, id[%s], name[%s]",
             subnet.id, subnet.name)

    begin = datetime.datetime.now()
    try:
        sub = neutron.subnet_create(rc, **subnet_params)
        end = datetime.datetime.now()
        LOG.info("Create subnet api apply [%s] seconds", \
                            (end-begin).seconds) 
        subnet.subnet_id = sub.id
        subnet.status = NETWORK_STATE_ACTIVE
        subnet.save()
    except Exception as ex:
        end = datetime.datetime.now()
        LOG.info("Create subnet api apply [%s] seconds", \
                            (end-begin).seconds) 
        subnet.status = NETWORK_STATE_ERROR
        subnet.save()
        LOG.exception("Failed to create subnet, id:[%s], name:[%s], msg:[%s]",
                      subnet.id, subnet.name, ex)
        raise ex

    return subnet

# Task: delete a subnet from openstack
@app.task
def delete_subnet(subnet):
    rc = create_rc_by_subnet(subnet)
    try:
        LOG.info("Start to delete subnet, id[%s], name[%s]",
                 subnet.id, subnet.name)
        neutron.subnet_delete(rc, subnet.subnet_id)

        subnet.deleted = True
        subnet.save()
    except Exception as ex:
        subnet.status = NETWORK_STATE_ERROR
        subnet.save()
        LOG.exception("Failed to delete subnet, id:[%s], name:[%s], msg:[%s]",
                      subnet.id, subnet.name, ex)
        raise ex

    return subnet

# Task: create a router
@app.task
def router_create_task(router=None):

    LOG.info("********** start to create router ***********")
    rc = create_rc_by_router(router)

    # Router param
    router_params = {"name": "router-%s" % router.id}
                     #"distributed": False,
                     #"ha": False}
    begin = datetime.datetime.now()
    try:
        LOG.debug("*********** create start **********")
        rot = neutron.router_create(rc, **router_params)
        end = datetime.datetime.now()
        LOG.info("Create router api apply [%s] seconds", \
                            (end-begin).seconds) 
        router.router_id = rot.id
        if router.is_gateway:
            # Call a new task to handle this
            router_add_gateway_task(router)
        router.status = NETWORK_STATE_ACTIVE
        router.save()
    except Exception as ex:
        end = datetime.datetime.now()
        LOG.info("Create router api apply [%s] seconds", \
                            (end-begin).seconds) 
        router.status = NETWORK_STATE_ERROR
        router.save()
        LOG.info("delete router error,id:[%s], msg:[%s]" % (router.id, ex))
        raise ex

    return router

# Task: delete a router
@app.task
def router_delete_task(router=None):
    rc = create_rc_by_router(router)

    LOG.info("delete router,id:[%s],name[%s]" % (router.id, router.name))
    try:
        # Delete a router in openstack
        neutron.router_delete(rc, router.router_id)
        router.router_id = None
        router.deleted = True
        router.save()
    except Exception as ex:
        router.status = NETWORK_STATE_ERROR
        router.save()
        LOG.info("delete router error,id:[%s],name[%s],msg:[%s]" % (network.id, network.name, ex))
        raise ex

    return network

# Task: add a gateway to a router
@app.task
def router_add_gateway_task(router=None):
    if not router:
        return
    rc = create_rc_by_router(router)
    LOG.info("Begin set gateway [Router:%s][%s]", router.id, router.name)
    # 1. find external network
    search_opts = {'router:external': True}
    networks = neutron.network_list(rc, **search_opts)
    ext_net_name = router.user_data_center.data_center.ext_net
    ext_net = filter(lambda n: n.name.lower() == ext_net_name, networks)
    ext_net_id = None
    if ext_net and len(ext_net) > 0:
        ext_net_id = ext_net[0].id

    if not ext_net_id:
        router.set_gateway_failed()
        LOG.error("No external network [%s] was found!", ext_net_name)
        return False

    # 2. set external gateway
    try:
        neutron.router_add_gateway(rc, router.router_id, ext_net_id)
        time.sleep(3)
    except Exception as ex:
        router.set_gateway_failed()
        LOG.exception(ex)
        return False 
    
    # 3.update cloud db router gateway info
    try:
        os_router = neutron.router_get(rc, router.router_id) 
        
        if os_router.external_gateway_info:
            LOG.info("Router [%s][%s] set gateway info [%s]", router.id,
                                    router.name, os_router.external_gateway_info)
            ext_fixed_ips = os_router.external_gateway_info.get("external_fixed_ips", [])
            if ext_fixed_ips:
                router.gateway = ext_fixed_ips[0].get("ip_address", "N/A")
                router.is_gateway = True 
            else:
                router.gateway = None
                router.is_gateway = False
        router.status = NETWORK_STATE_ACTIVE
        router.save()
    except Exception as ex:
        router.set_gateway_failed()
        LOG.exception(ex)
        
    LOG.info("End set gateway [Router:%s][%s]", router.id, router.name)
    return True

# Task: remove a gateway from a router
@app.task
def router_remove_gateway_task(router=None):
    if not router:
        return
    rc = create_rc_by_router(router)
    LOG.info("Begin clean gateway [Router:%s][%s]", router.id, router.name)
    try:
        # Request openstack to remove gateway
        neutron.router_remove_gateway(rc, router.router_id)
        router.gateway = None
        router.status = NETWORK_STATE_ACTIVE
        router.is_gateway = False
        router.save()
    except Exception as ex:
        router.status = NETWORK_STATE_ACTIVE
        router.save()
        LOG.exception(ex)

    LOG.info("End clean gateway [Router:%s][%s]", router.id, router.name)

# Task: composite network creation and subnet creation
@app.task
def create_network_and_subnet(network, subnet):
    create_network(network)
    create_subnet(subnet)

# Task: attach network to a router.Network ID, subnet ID and router ID are required
@app.task
def attach_network_to_router(network_id, router_id, subnet_id):

    network = Network.objects.get(pk=network_id)
    router = Router.objects.get(pk=router_id)
    subnet = Subnet.objects.get(pk=subnet_id)

    rc = create_rc_by_router(router)

    begin = datetime.datetime.now()
    # Request to openstack neutron for add
    try:
        LOG.info("Start to attach network[%s] to router[%s]",
                 network.name, router.name)
        router_inf = neutron.router_add_interface(
            rc, router.router_id, subnet_id=subnet.subnet_id)
    except Exception as e:
        end = datetime.datetime.now()
        LOG.info("Attach network to router api apply [%s] seconds", \
                            (end-begin).seconds) 
        LOG.exception("Failed to attach network[%s] to router[%s], "
                      "exception:%s",  network.name, router.name, e)
        network.change_status(NETWORK_STATE_ERROR)
    else:
        # RouterInterface 
        end = datetime.datetime.now()
        LOG.info("Attach network to router api apply [%s] seconds", \
                            (end-begin).seconds) 
        RouterInterface.objects.create(
            network_id=network_id, router=router, subnet=subnet,
            user=subnet.user, user_data_center=subnet.user_data_center,
            os_port_id=router_inf['port_id'])

        network.change_status(NETWORK_STATE_ACTIVE)

# Task: detach network from a router
@app.task
def detach_network_from_router(network_id):

    network = Network.objects.get(pk=network_id)
    subnet = network.subnet_set.filter(deleted=False)[0]
    rc = create_rc_by_network(network)
    interface_set = RouterInterface.objects.filter(network_id=network.id,
                                                   subnet=subnet, deleted=False)

    LOG.info("Start to detach network[%s]", network.name)

    try:
        for router_interface in interface_set:

            LOG.info("Start to delete router interface, router:[%s], "
                     "subnet[%s], id:[%s], port_id:[%s]",
                     router_interface.router.name, router_interface.subnet.name,
                     router_interface.id, router_interface.os_port_id)
            neutron.router_remove_interface(rc,
                                            router_interface.router.router_id,
                                            subnet.subnet_id,
                                            router_interface.os_port_id)

            router_interface.fake_delete()
    except Exception as e:
        LOG.exception("Failed to delete router interface, router:[%s], "
                      "subnet[%s], id:[%s], port_id:[%s], exception:%s",
                      router_interface.router.name,
                      router_interface.subnet.name,
                      router_interface.id, router_interface.os_port_id, e)
        network.change_status(NETWORK_STATE_ERROR)
        raise e
    else:
        network.change_status(NETWORK_STATE_ACTIVE)

# Allocate a fip
@app.task
def allocate_floating_task(floating=None):
    rc = create_rc_by_floating(floating)
    LOG.info("Begin to allocate floating, [%s]" % floating.id);
    pools = network.floating_ip_pools_list(rc)
    ext_net = filter(lambda n: n.name.lower() == \
                    floating.user_data_center.data_center.ext_net, pools)
    ext_net_id = None
    if ext_net and len(ext_net) > 0:
        ext_net_id = ext_net[0].id
    if ext_net_id: 
        # Request to openstack for allocation
        try:
            fip = network.tenant_floating_ip_allocate(rc, pool=ext_net_id)
            floating.ip = fip.ip
            # Set status in cloud_web
            floating.status = FLOATING_AVAILABLE
            floating.uuid = fip.id
            floating.save()
            # TODO: Chargesystem logic
            billing_task.charge_resource(floating.id, Floating)
            LOG.info("End to allocate floating, [%s][%s]" % (floating.id, fip.ip));
        except Exception as e:
            floating.status = FLOATING_ERROR
            LOG.info(str(e.message))
            floating.status_reason = e.message
            floating.save()
            LOG.exception(e)
            LOG.info("End to allocate floating, [%s][exception]" % floating.id);
    else:
        floating.status = FLOATING_ERROR
        floating.save()
        LOG.info("End to allocate floating, [%s][---]" % floating.id);

# Task: release a fip
def floating_release(floating, **kwargs):
    rc = create_rc_by_floating(floating)
    result = True
    if floating.uuid:
        # Request to openstack for releasing
        result = network.tenant_floating_ip_release(rc, floating.uuid)
        LOG.info("release floating associate instance, [%s]" % result)
    # Update info in cloud_web 
    floating.status = FLOATING_RELEASED
    floating.deleted = 1
    floating.delete_date = datetime.datetime.now()
    floating.save()

    # TODO: Chargesystem logic
    Order.disable_order_and_bills(floating)
    if floating.ip:
        ins = Instance.objects.filter(public_ip=floating.ip)
        ins.update(public_ip=None)

    LOG.info("floating action, [%s][relese][%s]" % (floating.id, result));

# Task: associate a fip
def floating_associate(floating, **kwargs):

    # Two resources can be associate with fip, INSTANCE and LOADBALANCE
    resource_type_dict = dict(RESOURCE_TYPE)
    resource_type = kwargs.get('resource_type')[0]
    resource = kwargs.get('resource')[0]
    if resource:
        rc = create_rc_by_floating(floating)
        ports = None
        resource_obj = None

        if resource_type_dict[str(resource_type)] == 'INSTANCE':
            ins = Instance.objects.get(pk=resource)
            resource_obj = ins
            if neutron.is_neutron_enabled(rc):
                # Request to neutron for associate 
                ports = network.floating_ip_target_get_by_instance(rc, ins.uuid)
            else:
                ports = ins.uuid
        elif resource_type_dict[resource_type] == 'LOADBALANCER':
            pool = BalancerPool.objects.get(pk=resource)
            if not pool or not pool.vip:
                floating.status = FLOATING_AVAILABLE
                floating.save()
                return None
            resource_obj = pool
            ports = pool.vip.port_id+"_"+pool.vip.address

        if not ports:
            LOG.info("floating action, resourceType[%s],[%s][associate][ins:%s] ports is None" % (resource_type_dict[resource_type], floating.id, resource));
            floating.status = FLOATING_AVAILABLE
            floating.resource = None
            floating.resource_type = None
            floating.save()
            return

        LOG.info("floating action, [%s][associate][ins:%s][ports:%s]" % (
                            floating.id, resource, ports))
        # Fip associate
        try:
            network.floating_ip_associate(rc, floating.uuid, ports)
            if len(ports.split('_')) > 1:
                port, fixed_ip = ports.split('_')
            else:
                port, fixed_ip = ports, ports
            # Update info in db
            floating.resource = resource
            floating.resource_type = resource_type
            floating.status = FLOATING_BINDED
            floating.fixed_ip = fixed_ip
            floating.port_id = port
            floating.save()
            if resource_type_dict[str(resource_type)] == 'INSTANCE':
                resource_obj.public_ip = floating.ip
                resource_obj.save()
            elif resource_type_dict[resource_type] == 'LOADBALANCER':
                vip = BalancerVIP.objects.get(pk=resource_obj.vip.id)
                vip.public_address = floating.ip
                vip.save()
        except Exception as e:
            LOG.exception(e)
            floating.status = FLOATING_AVAILABLE
            floating.resource = None
            floating.resource_type = None
            floating.save()
    else:
        LOG.info("floating action, [%s][associate] no ins_id" % floating.id);

# Disassociate fip
def floating_disassociate(floating, **kwargs):
    LOG.info("Begin to disassociate floating [%s]", floating)
    try:
        if floating.uuid and floating.port_id:
            rc = create_rc_by_floating(floating)
            # disassociate fip from port
            network.floating_ip_disassociate(rc, floating.uuid,
                                             floating.port_id)
    except Exception:
        LOG.exception("Failed to disassociate floating[%s]", floating)
        floating.status = FLOATING_BINDED
        floating.save()
        return False
    else:
        floating.unbind_resource()
        LOG.info("Floating IP[%s] is disassociated.", floating)
        return True

# FIP action interface 
@app.task
def floating_action_task(floating=None, act=None, **kwargs):
    LOG.info("Begin to floating action, [%s][%s]" % (floating.id, act));
    try:
        # Call action to do this
        globals()["floating_%s" % act](floating, **kwargs) 
    except Exception as e:
        LOG.exception(e)

    LOG.info("End floating action, [%s][%s]" % (floating.id, act));

# Security_group task
@app.task
def security_group_create_task(firewall):
    assert firewall
    rc = create_rc_by_security(firewall)
    start = datetime.datetime.now()
    try:
        LOG.info(u"Firewall create task start, [%s]." % firewall)
        # Call neutron to handle
        security_group = network.security_group_create(rc,
                                firewall.name, firewall.desc)
    except Exception as ex:
        end = datetime.datetime.now()
        LOG.exception(u"Firewall create api call failed, [%s], "
                    "apply [%s] seconds." % (firewall, (end-start).seconds))
        return False
    else:
        end = datetime.datetime.now()
        LOG.info(u"Firewall create task succeed, [%s], "
                    "apply [%s] seconds." % (firewall, (end-start).seconds))
        firewall.firewall_id = security_group.id
        firewall.save()
        return True

# Delete a security goup
@app.task
def security_group_delete_task(firewall):
    rc = create_rc_by_security(firewall)
    start = datetime.datetime.now()
    try:
        LOG.info(u"Firewall delete task start, [%s].", firewall)
        network.security_group_delete(rc, firewall.firewall_id)
    except Exception:
        end = datetime.datetime.now()
        LOG.exception(u"Firewall delete api call failed, [%s], "
                      "apply [%s] seconds.",
                      firewall, (end - start).seconds)
        return False
    else: 
        # Save rule info to cloud_web
        for rule in firewall.firewallrules_set.all():
            rule.firewall_rules_id = None
            rule.deleted = True
            rule.delete()
        firewall.firewall_id = None
        firewall.deleted = True
        firewall.save()
       
        end = datetime.datetime.now()
        LOG.info(u"Firewall delete task succeed, [%s], "
                 "apply [%s] seconds.",
                 firewall, (end - start).seconds)


        return True

# Task: security group rule creation
@app.task
def security_group_rule_create_task(firewall_rule=None):
    assert firewall_rule
    rc = create_rc_by_security(firewall_rule)
    start = datetime.datetime.now()
    try:
        LOG.info(u"Firewall rule create task start, [%s].", firewall_rule)
        # handle sc request to openstack
        rule = network.security_group_rule_create(rc,
                            parent_group_id=firewall_rule.firewall.firewall_id,
                            direction=firewall_rule.direction,
                            ethertype=firewall_rule.ether_type,
                            ip_protocol=firewall_rule.protocol,
                            from_port=firewall_rule.port_range_min,
                            to_port=firewall_rule.port_range_max,
                            cidr=firewall_rule.remote_ip_prefix,
                            group_id=firewall_rule.remote_group_id)
    except Exception as e:
        firewall_rule.delete()
        end = datetime.datetime.now()
        LOG.exception(u"Firewall rule create api call failed, [%s], "
                       "apply [%s] seconds.",
                        firewall_rule, (end-start).seconds)
        return False
    else:
        # Save rule info to db
        firewall_rule.firewall_rules_id = rule.id
        firewall_rule.save()
        end = datetime.datetime.now()
        LOG.info(u"Firewall rule create task succeed, [%s], "
                       "apply [%s] seconds.",
                        firewall_rule, (end-start).seconds)
        return True

# Task: delete a sc rule to task
@app.task
def security_group_rule_delete_task(firewall_rule):
    assert firewall_rule
    rc = create_rc_by_security(firewall_rule)
    start = datetime.datetime.now()
    try:
        LOG.info(u"Firewall rule delete task start, [%s].", firewall_rule)
        if firewall_rule.firewall_rules_id:
            network.security_group_rule_delete(rc,
                        firewall_rule.firewall_rules_id)
    except Exception as e:
        end = datetime.datetime.now()
        LOG.exception(u"Firewall rule delete api call failed, [%s], "
                      "apply [%s] seconds.",
                      firewall_rule, (end-start).seconds)
        return False
    else:
        firewall_rule.delete()
        end = datetime.datetime.now()
        LOG.info(u"Firewall rule delete task succeed, [%s], "
                      "apply [%s] seconds.",
                      firewall_rule, (end-start).seconds)
        return True

# Update server sc
@app.task
def server_update_security_groups_task(instance, firewall=None):
    assert firewall
    rc = create_rc_by_security(firewall)
    start = datetime.datetime.now()
    try:
        LOG.info(u"Instance change firewall task start, [%s][%s]." % (
                                    instance, firewall))
        # Request to openstack for updating server's sc
        network.server_update_security_groups(rc, instance.uuid, [firewall.firewall_id])
    except Exception as e:
        end = datetime.datetime.now()
        LOG.exception(u"Instance change firewall api call failed, "
                    "[%s][%s], apply [%s] seconds." % (
                    instance, firewall, (end-start).seconds))
        return False
    else:
        # Save sc info in db
        end = datetime.datetime.now()
        LOG.info(u"Instance change firewall task succeed, [%s][%s], "
                 "apply [%s] seconds." % (
                    instance, firewall, (end-start).seconds))
        instance.firewall_group = firewall
        instance.save()
        return True

# edit default sc in openstack
def edit_default_security_group(user, udc):
    rc = create_rc_by_udc(udc) 
    sec_group_list = network.security_group_list(rc)
    default_sec_group = None
    # Check if default sc existing
    for sec_group in sec_group_list:
        if sec_group.name == "default":
            default_sec_group = sec_group
            break

    if default_sec_group is None:
        LOG.error("Default security group not found. user:[%s], date_center:[%s]",\
                user.username, udc.data_center.name)
        return
    # Sync firewall staus
    firewall = Firewall.objects.create(name=settings.DEFAULT_FIREWALL_NAME,
                        desc=settings.DEFAULT_FIREWALL_NAME,
                        is_default=True,
                        firewall_id=default_sec_group.id,
                        user=user,
                        user_data_center=udc,
                        deleted=False)
# Task: delete user router
@app.task
def delete_user_router_interface(router=None):
    rc = create_rc_by_router(router)


    router_remove_gateway_(router)

    time.sleep(1)
    LOG.info("delete router,id:[%s],name[%s]" % (router.id, router.name))
    try:
        # Forward router deletion to openstack
        neutron.router_delete(rc, router.router_id)
        router.router_id = None
        router.deleted = True
        router.save()
    except Exception as ex:
        router.status = NETWORK_STATE_ERROR
        router.save()
        LOG.info("delete router error,id:[%s],name[%s],msg:[%s]" % (network.id, network.name, ex))
        raise ex

    return network

# Remove router gateway
def router_remove_gateway_(router=None):
    if not router:
        return
    rc = create_rc_by_router(router)
    LOG.info("Begin clean gateway [Router:%s][%s]", router.id, router.name)
    try:
        # Forward request to openstack neutron
        neutron.router_remove_gateway(rc, router.router_id)
        router.gateway = None
        router.status = NETWORK_STATE_ACTIVE
        router.is_gateway = False
        router.save()
    except Exception as ex:
        router.status = NETWORK_STATE_ACTIVE
        router.save()
        LOG.exception(ex)

    LOG.info("End clean gateway [Router:%s][%s]", router.id, router.name)

