#-*- coding=utf-8 -*- 

import datetime
import subprocess
import logging
import time

from django.conf import settings

from celery import app

from biz.instance.settings import (INSTANCE_STATE_RUNNING,
                                   INSTANCE_STATE_BOOTING, INSTANCE_STATE_ERROR,
                                   INSTANCE_STATE_DELETE,
                                   INSTANCE_STATE_POWEROFF)
from biz.instance.models import Instance
from biz.network.models import Network
from biz.volume.settings import (VOLUME_STATE_AVAILABLE,
                                 VOLUME_STATE_IN_USE, VOLUME_STATE_ERROR)
from biz.image.settings import WINDOWS, LINUX

from cloud_utils import create_rc_by_instance, create_rc_by_dc, get_admin_client, get_nova_admin
from network_task import make_sure_default_private_network
from cloud import volume_task, billing_task

from api import nova
from api import neutron


LOG = logging.getLogger(__name__)


# Task: create a new flavor if not existing
def flavor_create(instance):
    assert instance  
    # Generate a new name of flavor
    def _generate_name(instance):
        gpu = 'no'
        if instance.gpu == True:
            gpu = 'yes'
        else:
            gpu = 'no'
        name = u"%s.cpu-%s-ram-%s-disk-%s-core-%s-socket-%s-gpu-%s" % (settings.OS_NAME_PREFIX,
                    instance.cpu, instance.memory, instance.sys_disk, instance.core, instance.socket, gpu)
        return name
    # Get flavor by name
    def _get_flavor_by_name(instance, name):
        rc = create_rc_by_instance(instance)
        flavor = None
        # Construct nova admin client
        novaAdmin = get_nova_admin(instance)
        # List all the flavors
        try:
            flavors = novaAdmin.flavors.list(rc)
        except Exception:
            flavors = []
            raise

        if flavors is not None:
            for f in flavors:
                if f.name == name:
                    flavor = f
                    break
        return flavor

    LOG.info(u"Flavor create start, [%s].", instance)
    begin = datetime.datetime.now()
    rc = create_rc_by_instance(instance)
    LOG.info("*** rc is ***" + str(rc))
    name = _generate_name(instance)
    flavor = _get_flavor_by_name(instance, name)
    metadata = {"hw:cpu_cores":int(instance.core),"hw:cpu_sockets":int(instance.socket)}
    # For gpu, set metadata
    if instance.gpu:
        #metadata['pci_passthrough:alias'] = ['alias_1:1']
        metadata['pci_passthrough:alias'] = settings.GPU

    # Not existing, create a new one
    if flavor is None:
        try:
            LOG.info(u"Flavor not exist, create new, [%s][%s].", instance, name)
         
            novaadmin = get_nova_admin(instance)
            flavor = novaadmin.flavors.create(ram=instance.memory, name=name,
                                  vcpus=instance.cpu, disk=instance.sys_disk,
                                  is_public=True)
	    flavor.set_keys(metadata)
        except nova.nova_exceptions.Conflict:
            LOG.info(u"Flavor name conflict, [%s][%s].", instance, name)
            flavor = _get_flavor_by_name(instance, name)
        except:
            raise

    end = datetime.datetime.now()
    LOG.info(u"Flavor create end, [%s][%s], apply [%s] seconds.",
                instance, name, (end-begin).seconds)
    return flavor

# Create a new instance
def instance_create(instance, password):
    if instance.image.os_type not in (LINUX, WINDOWS):
        raise ValueError(u"Unknown image os type, [%s].", instance)

    # Cloud-init formated script
    user_data_format = "#cloud-config\n"\
                       "password: %s\n"\
                       "chpasswd: { expire: False }\n"\
                       "ssh_pwauth: True\n"
    user_data = user_data_format % password
    rc = create_rc_by_instance(instance)

    # nic is alias of Network interface card
    nics = None
    if neutron.is_neutron_enabled(rc):
        nics = [{"net-id": instance.network.network_id, "v4-fixed-ip": ""}]

    LOG.info("**** flavor is ****" + str(instance.flavor_id))
    if instance.image.os_type == LINUX:
        # OpenStack nova server creation
        try:
            server = nova.server_create(rc, name=instance.name,
                                        image=instance.image.uuid,
                                        flavor=instance.flavor_id, key_name=None,
                                        security_groups=[], nics=nics,
                                        user_data=user_data)
        except Exception as e:
            LOG.info("*** error is ***" + str(e))
    else: 
        # For windows generate complexity passwd
        new_pwd = []
        for c in password:
            if c in ["&", "|", "(", ")", "<", ">", "^"]:
                new_pwd.append("^")
            new_pwd.append(c)
        password = "".join(new_pwd)
        LOG.info(u"Windows complexity password, [%s][%s].",
                        instance, password)
        server = nova.server_create(rc, name=instance.name,
                                    image=instance.image.uuid,
                                    flavor=instance.flavor_id,
                                    key_name=None, user_data=None,
                                    security_groups=[], nics=nics,
                                    meta={"admin_pass": password})
    return server


# Get nova server specific info
def instance_get(instance):
    assert instance
    if instance.uuid is None:
        return None

    rc = create_rc_by_instance(instance)
    # Make novaclient to get server detailed info
    try:
        return nova.server_get(rc, instance.uuid)
    except nova.nova_exceptions.NotFound:
        return None

# Get get server vnc console
def instance_get_vnc_console(instance):
    assert instance
    LOG.info("*** start to get novnc ****")
    if instance.uuid is None:
        return None

    rc = create_rc_by_instance(instance)
    LOG.info("  rc is " + str(rc))
    try:
        return nova.server_vnc_console(rc, instance_id=instance.uuid)
    except Exception:
        LOG.exception("Failed to get vnc console, [%s].", instance)
        return None

# Get server console log
def instance_get_console_log(instance, tail_length=None):
    assert instance
    if instance.uuid is None:
        return None
    
    rc = create_rc_by_instance(instance)
    try:
        return nova.server_console_output(rc, instance.uuid,
                                          tail_length=tail_length)
    except Exception:
        LOG.exception("Failed to get console output, [%s].", instance)
        return None
        
# Collecting instance deleted resource
def instance_deleted_release_resource(instance):
    # floatings
    from biz.floating.models import Floating

    floatings = Floating.objects.filter(resource=instance.pk, deleted=False)

    for floating in floatings:
        floating.unbind_resource()
        LOG.info('Floating[%s] of instance[%s][%s] is released.',
                 floating.ip, instance.id, instance.name)

    # volumes
    from biz.volume.models import Volume
    volumes = Volume.objects.filter(instance=instance, deleted=False)
    for vol in volumes:
        vol.instance = None
        vol.status = VOLUME_STATE_AVAILABLE
        vol.save()
        LOG.info('Volume[%s] of instance[%s][%s] is released.',
                 vol.name, instance.id, instance.name)

# Task: sync instance status
@app.task
def instance_create_sync_status_task(instance, neutron_enabled, user_tenant_uuid, rc,
                                    retry_count=1):
    assert instance
    assert instance.uuid
    retry_count += 1

    begin = datetime.datetime.now()
    for count in xrange(settings.MAX_COUNT_SYNC):
        srv = instance_get(instance)
        LOG.info("*** srv is ***" + str(srv.addresses))
        status = srv.status.upper() if srv else u"None"

        LOG.info(u"Instance create synchronize status, [Count:%s][%s], "
                "[Status: %s].", count, instance, status)

        # If server status is active, get network info,update server status and save
        if status == "ACTIVE":
            instance.status = INSTANCE_STATE_RUNNING
            # Get network info from neutron
            network_ = neutron.network_list_for_tenant(rc, tenant_id=user_tenant_uuid)
            LOG.info("********** network is ******************" + str(network_))
            network_name = None
            for net in network_:
                LOG.info("***** net is *******" + str(net))
                network_id = net.id
                network_name = net.name
            try:
                network_ = Network.objects.get(pk=instance.network.id)
                LOG.info(network_)
                private_net = network_.name
                LOG.info("*** private_net is ***" + str(private_net))
                # For vlan and flat
                if  settings.VLAN_ENABLED == False and not settings.FLAT:
                    instance.private_ip = srv.addresses.\
                                get(private_net)[0].get("addr", "---")
                else:
                    # For vxlan
                    instance.private_ip = srv.addresses.\
                                get(network_name)[0].get("addr", "---")
            except Exception as ex:
                LOG.info(u"Instance create succeed, "
                         "but set private network failed, "
                         "[%s].", instance)
            instance.save()
            end = datetime.datetime.now()
            LOG.info(u"Instance create succeed, [%s], apply [%s] seconds.",
                            instance, (end-begin).seconds)
            break
        # If server status is error, save in db 
        if status == "ERROR":
            instance.status = INSTANCE_STATE_ERROR
            instance.save() 
            end = datetime.datetime.now()
            if settings.SEND_MAIL_WHEN_BACKEND_ERROR:
                LOG.error(u"Instance create failed, [%s], apply [%s] seconds.",
                                instance, (end-begin).seconds)
            else:
                LOG.warn(u"Instance create failed, [%s], apply [%s] seconds.",
                                instance, (end-begin).seconds)
            break

        time.sleep(settings.INSTANCE_SYNC_INTERVAL_SECOND) 
    else:
        # Sync timeout
        end = datetime.datetime.now()
        if retry_count <= 3:
            LOG.warn(u"Instance create timeout, [%s], apply [%s] seconds.",
                            instance, (end-begin).seconds)
            instance_create_sync_status_task.delay(instance,
                    neutron_enabled, retry_count=retry_count)
            return False
        else:
            LOG.error(u"Instance create timeout, [%s], apply [%s] seconds.",
                            instance, (end-begin).seconds)
            return False
    return True

# Instance create task interface
@app.task
def instance_create_task(instance, **kwargs):
    LOG.debug("*************** I am instance create in instance_create_task ****************")
    password = kwargs.get("password", None)
    assert instance
    assert password

    user_tenant_uuid = kwargs.get("user_tenant_uuid", None)
 
    LOG.info("**** user_tenant_uuid in instance_create_task is ****" + str(user_tenant_uuid))
    begin = datetime.datetime.now()
    LOG.info(u"Instance create start, [%s][pwd:%s].",
                        instance, password)
     
    rc = create_rc_by_instance(instance)
    # Try to create a flavor if not existing
    try: 
        flavor = flavor_create(instance)
        instance.flavor_id = flavor.id 
    except Exception:
        instance.status = INSTANCE_STATE_ERROR
        instance.save()
        LOG.exception(u"Instance create failed by flavor exception, [%s].",
                        instance)
        return False


    # First check if network exists or not.
    neutron_enabled = neutron.is_neutron_enabled(rc)
    LOG.info("********** check neutron is enabled or not **************" + str(neutron_enabled))
    
    # If not exists, create a new one for that tenant.
    if neutron_enabled:
        LOG.info("********** neutron_enabled *************")
        LOG.info("********** start to make sure make_sure_default_private_network ***********")
        network = make_sure_default_private_network(instance, rc, user_tenant_uuid)
        LOG.info("**** network is ****" + str(network))
        instance.network_id = network.id
        instance.save() 
        LOG.info(u"Instance create set network passed, [%s][%s].",
                    instance, network)

    if not instance.firewall_group:
        LOG.info("********** start to set default firewall ************")
        instance.set_default_firewall()
 
    # Server creation action
    try:
        LOG.info("********** start to create instance *****************")
        server = instance_create(instance, password)
    except Exception as ex:
        instance.status = INSTANCE_STATE_ERROR
        instance.status_reason = ex.message
        instance.save()
        LOG.exception(u"Instace create api call raise an exception, [%s][%s].",
                        instance, ex.message)
        return False
    else:
        status = server.status.upper() if server else u"None"
        instance.uuid = server.id
        if status == u"ERROR":
            instance.status = INSTANCE_STATE_ERROR
            instance.save()
            end = datetime.datetime.now()
            LOG.info(u"Instance create api call failed, [%s][%s], "
                     "apply [%s] seconds.",
                    instance, status, (end-begin).seconds)
        else:
            instance.status = INSTANCE_STATE_BOOTING
            instance.save()
            end = datetime.datetime.now()
            LOG.info(u"Instance create api call passed, [%s][%s], "
                    "apply [%s] seconds.",
                    instance, status, (end-begin).seconds)
            time.sleep(settings.INSTANCE_SYNC_INTERVAL_SECOND)
            # Try to sync status
            instance_create_sync_status_task.delay(
                instance, neutron_enabled, user_tenant_uuid, rc, retry_count=1)
            billing_task.charge_resource(instance.id, Instance)

    return instance

# Reboot server
def reboot(instance):
    rc = create_rc_by_instance(instance)
    server = instance_get(instance)
    if server:
        nova.server_reboot(rc, instance.uuid) 
    # After rebooting,sync status 
    for count in xrange(settings.MAX_COUNT_SYNC):
        time.sleep(settings.INSTANCE_SYNC_INTERVAL_SECOND)
        server = instance_get(instance)
        status = server.status.upper() if server else "None"
        LOG.info("Instance action [reboot] synchronize status, "
                "[Count:%s][%s][status: %s].",
                 count, instance, status)

        if status == u"ACTIVE":
            instance.status = INSTANCE_STATE_RUNNING
            instance.save()
            break

        if status == u"ERROR":
            instance.status = INSTANCE_STATE_ERROR
            instance.save()
            break

    return True

# Delete server from openstack
def _server_delete(instance):
    rc = create_rc_by_instance(instance)
    server = instance_get(instance)
    
    if server:
        nova.server_delete(rc, instance.uuid)
    
    for count in xrange(settings.MAX_COUNT_SYNC):
        time.sleep(settings.INSTANCE_SYNC_INTERVAL_SECOND)
        server = instance_get(instance)
        status = server.status.upper() if server else "None"
        LOG.info("Instance action [reboot] synchronize status, "
                "[Count:%s][%s][status: %s].",
                 count, instance, status)

        if server is None:
            instance.status = INSTANCE_STATE_DELETE
            instance.terminate_date = datetime.datetime.now()
            instance.deleted = True
            instance.save()
            instance_deleted_release_resource(instance)
            break

        if status == u"ERROR":
            instance.status = INSTANCE_STATE_ERROR
            instance.save()
            break
   
    return True

# Start a server
def _server_start(instance):
    rc = create_rc_by_instance(instance)
    server = instance_get(instance)
    if server:
        nova.server_start(rc, instance.uuid)
# Stop a server
def _server_stop(instance):
    rc = create_rc_by_instance(instance)
    server = instance_get(instance)
    if server:
        nova.server_stop(rc, instance.uuid)

# Unpause a server
def _server_unpause(instance):
    rc = create_rc_by_instance(instance)
    server = instance_get(instance)
    if server:
        nova.server_unpause(rc, instance.uuid)

# Pause a server
def _server_pause(instance):
    rc = create_rc_by_instance(instance)
    server = instance_get(instance)
    if server:
        nova.server_pause(rc, instance.uuid)

# Sync server status
@app.task
def instance_status_synchronize_task(instance, action):
    assert instance
    assert action 

    # For different status,save status to db
    def _server_is_active(instance, status):
        if status == u"ACTIVE":
            instance.status = INSTANCE_STATE_RUNNING
            instance.save()
            return True
        
        if status in [u"ERROR", u"None"]:
            instance.status = INSTANCE_STATE_ERROR
            instance.save()
            return True

        return False

    def _server_is_none(instance, status):
        if status == u"ERROR":
            instance.status = INSTANCE_STATE_ERROR
            instance.save()
            return True
        
        if status == u"None":
            instance.status = INSTANCE_STATE_DELETE
            instance.terminate_date = datetime.datetime.now()
            instance.deleted = True
            instance.save()
            instance_deleted_release_resource(instance)
            return True

        return False

    def _server_is_poweroff(instance, status):
        if status == u"SHUTOFF":
            instance.status = INSTANCE_STATE_POWEROFF
            instance.save()
            return True
        
        if status in [u"ERROR", u"None"]:
            instance.status = INSTANCE_STATE_ERROR
            instance.save()
            return True

        return False

    _ACTION_MAPPING = {
        "reboot": _server_is_active,
        "terminate": _server_is_none,
        "power_on": _server_is_active,
        "power_off": _server_is_poweroff,
    }

    begin = datetime.datetime.now()
    for count in xrange(settings.MAX_COUNT_SYNC):
        time.sleep(settings.INSTANCE_SYNC_INTERVAL_SECOND)
        server = instance_get(instance)
        status = server.status.upper() if server else u"None"
        LOG.info("Instance action [%s] synchronize status, "
                "[Count:%s][%s][status: %s].",
                 action, count, instance, status) 
        act = _ACTION_MAPPING.get(action)
        if act(instance, status):
            end = datetime.datetime.now()
            LOG.info("Instance action [%s] synchronize status end, [%s], "
                    "apply [%s] seconds.",
                    action, instance, (end-begin).seconds) 
            break
    else:
        end = datetime.datetime.now()
        LOG.info("Instance action [%s] synchronize status timeout, [%s], "
                 "apply [%s] seconds.",
                 action, instance, (end-begin).seconds) 

    return True

# Task: attach volume to a instance
@app.task
def attach_volume_to_instance(volume, instance):
    rc = create_rc_by_instance(instance)
    LOG.info("Volume attach start, [%s][%s].",
                    instance, volume)

    begin = datetime.datetime.now()
    # Try to attach volume to a instance
    try:
        nova.instance_volume_attach(rc, volume_id=volume.volume_id,
                                    instance_id=instance.uuid, device=None)
    except Exception:
        volume.change_status(VOLUME_STATE_ERROR)
        end = datetime.datetime.now()
        LOG.exception("Volume attach api call failed, [%s][%s], "
                      "apply [%s] seconds.",
                      instance, volume, (end-begin).seconds)
        return False
    else:
        end = datetime.datetime.now()
        LOG.info("Volume attach api call succeed, [%s][%s], "
                      "apply [%s] seconds.",
                      instance, volume, (end-begin).seconds)

    begin = datetime.datetime.now()
    # Sync status
    for count in xrange(settings.MAX_COUNT_SYNC):
        time.sleep(settings.INSTANCE_SYNC_INTERVAL_SECOND)
        vol = volume_task.volume_get(volume)
        status = vol.status.upper() if vol else "None"
        
        end = datetime.datetime.now()
        if status == u'ERROR':
            volume.change_status(VOLUME_STATE_ERROR)
            LOG.info("Volume attach failed, "
                    "[Count:%s][%s][%s][status: %s], apply [%s] seconds.",
                    count, instance, volume, status, (end-begin).seconds)
            break
        elif status == u'ERROR_ATTACHING':
            volume.instance = instance
            volume.change_status(VOLUME_STATE_ERROR)
            LOG.info("Volume attach failed, "
                    "[Count:%s][%s][%s][status: %s], apply [%s] seconds.",
                    count, instance, volume, status, (end-begin).seconds)
            break
        elif status == u'IN-USE':
            volume.instance = instance
            volume.change_status(VOLUME_STATE_IN_USE)
            LOG.info("Volume attach succeed, "
                    "[Count:%s][%s][%s][status: %s], apply [%s] seconds.",
                    count, instance, volume, status, (end-begin).seconds)
            break
        elif status == "None":
            LOG.info("Volume attach failed, volume is None, "
                    "[Count:%s][%s][%s][status: %s], apply [%s] seconds.",
                    count, instance, volume, status, (end-begin).seconds)
            volume.instance = None
            volume.deleted = True
            volume.save()
            break 
        else:
             LOG.info("Volume attach synchronize status, "
                "[Count:%s][%s][%s][status: %s].",
                 count, instance, volume, status)
    else:
        end = datetime.datetime.now()
        LOG.info("Volume attach timeout, [%s][%s], apply [%s] seconds.",
                 instance, volume, (end-begin).seconds)
        return False

    end = datetime.datetime.now()
    if volume.status == VOLUME_STATE_ERROR:
        LOG.error("Volume attach failed, [%s][%s], apply [%s] seconds.",
                  instance, volume, (end-begin).seconds)
        return False
    else: 
        return True


# Task detach volume from a instance
@app.task
def detach_volume_from_instance(volume):
    assert volume is not None
    assert volume.instance is not None

    instance = volume.instance
    rc = create_rc_by_instance(instance)
    LOG.info("Volume detach start, [%s][%s].",
             instance, volume)
    
    begin = datetime.datetime.now()
    # OpenStack action
    try:
        # OpenStack action
        nova.instance_volume_detach(rc, instance.uuid, volume.volume_id)
    except Exception:
        volume.change_status(VOLUME_STATE_ERROR)
        end = datetime.datetime.now()
        LOG.exception("Volume detach api call failed, [%s][%s], "
                      "apply [%s] seconds.",
                      instance, volume, (end-begin).seconds)
        return False
    else:
        end = datetime.datetime.now()
        LOG.info("Volume detach api call succeed, [%s][%s], "
                      "apply [%s] seconds.",
                      instance, volume, (end-begin).seconds)

    # Sync status
    begin = datetime.datetime.now()
    for count in xrange(settings.MAX_COUNT_SYNC):
        time.sleep(settings.INSTANCE_SYNC_INTERVAL_SECOND)
        vol = volume_task.volume_get(volume)
        status = vol.status.upper() if vol else 'None'

        end = datetime.datetime.now()
        
        if status == u'ERROR':
            LOG.info("Volume detach failed, "
                    "[Count:%s][%s][%s][status: %s], apply [%s] seconds.",
                    count,instance, volume, status, (end-begin).seconds)
            volume.change_status(VOLUME_STATE_ERROR)
            break
        elif status == u'AVAILABLE':
            LOG.info("Volume detach succeed, "
                    "[Count:%s][%s][%s][status: %s], apply [%s] seconds.",
                    count,instance, volume, status, (end-begin).seconds)
            volume.instance = None
            volume.change_status(VOLUME_STATE_AVAILABLE)
            break
        elif status == "None":
            LOG.info("Volume detach volume is None, "
                    "[Count:%s][%s][%s][status: %s], apply [%s] seconds.",
                    count,instance, volume, status, (end-begin).seconds)
            volume.instance = None
            volume.delete = True
            volume.save()
            break
        else:
            LOG.info("Volume detach synchronize status, "
                    "[Count:%s][%s][%s][status: %s], apply [%s] seconds.",
                    count,instance, volume, status, (end-begin).seconds)

    else:
        end = datetime.datetime.now()
        LOG.info("Volume detach timeout, "
                    "[%s][%s], apply [%s] seconds.",
                    instance, volume, (end-begin).seconds)
        return False

    end = datetime.datetime.now()
    if volume.status == VOLUME_STATE_ERROR:
        LOG.error("Volume detach failed, "
                    "[%s][%s], apply [%s] seconds.",
                    instance, volume, (end-begin).seconds)
        return False
    else:
        return True


# Overview data
@app.task
def hypervisor_stats_task(data_center):
    assert data_center is not None
    rc = create_rc_by_dc(data_center)
    stats = None
    
    # Get hypervisor data
    try:
        stats = nova.hypervisor_stats(rc)
    except:
        LOG.exception("Get hypervisor stats error!")

    return stats

# Get server port info, including ip, mac and so on.
def instance_get_port(instance):
    assert instance
    if instance.uuid is None:
        return None

    rc = create_rc_by_instance(instance)
    try:
        return nova.instance_interface_list(rc, instance.uuid)
    except nova.nova_exceptions.NotFound:
        return None


# Task: delete user instance and related network
@app.task
def delete_user_instance_network(request, instance_id):

    #
    LOG.info("*** instance_id is ***" + str(instance_id))
    novaAdmin = get_nova_admin(request)
    try:
        server_deleted = novaAdmin.servers.delete(str(instance_id))
        LOG.info("*** delete success ***")
    except Exception:
        server_deleted = []
        LOG.info("*** server delete failed ***")
        pass
    return True

# Get vnc port by qemu remote command
def instance_get_realvnc_console(instance):

    assert instance
    if instance.uuid is None:
        return None


    LOG.info("****** i am vdi view with method get ********")

    spice = {}
    if instance:
        # Construct nova admin client
        novaAdmin = get_nova_admin(instance)
        server = novaAdmin.servers.get(instance.uuid)
        # Get detailed info
        server_dict = server.to_dict()
        server_host = server_dict['OS-EXT-SRV-ATTR:host']
        server_status = server_dict['status']
        LOG.info("******* server_status is *******" + str(server_status))
        LOG.info("******* server_host is *******" + str(server_host))
        # Get instance running host
        host_ip = settings.COMPUTE_HOSTS[server_host]
        LOG.info("host ip is" + str(host_ip))
        # Format command
        cmd="virsh -c qemu+tcp://" + host_ip + "/system vncdisplay " + instance.uuid
        LOG.info("cmd=" + cmd)
        p = subprocess.Popen("virsh -c qemu+tcp://" + host_ip + "/system vncdisplay " + instance.uuid, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        LOG.info(" p is " + str(p))
        port = None
        for line in p.stdout.readlines():
            port = line
            LOG.info(" line is " + str(line))
            break
        LOG.info("host_ip=" + host_ip)
        LOG.info("port=" + str(port))
        if "error" in str(port):
            return Response({"success": False, "msg": _('Failed to create flavor for unknown reason.')})
        # Get spice port by vnc port
        split_port = port.split(":")
        LOG.info(split_port)
        port_1 = split_port[1]
        LOG.info(port_1)
        port_2 = port_1.split("\\")
        LOG.info(port_2)
        port_3 = port_2[0]
        LOG.info(port_3)
        vnc_port = 5900 + int(port_3)
        LOG.info(vnc_port)
        vnc_url = "spicevm:vnc:" + host_ip + ":" + str(vnc_port)
        vnc = {"url": vnc_url, "type": "realvnc"}
        LOG.info(spice)

        return vnc

# Task get spice console
def instance_get_spice_console(instance):

    assert instance
    if instance.uuid is None:
        return None


    LOG.info("****** i am vdi view with method get ********")

    spice = {}
    if instance:
        LOG.info("******")
        novaAdmin = get_nova_admin(instance)
        LOG.info("******")
        server = novaAdmin.servers.get(instance.uuid)
        LOG.info("******")
        server_dict = server.to_dict()
        LOG.info("******")
        server_host = server_dict['OS-EXT-SRV-ATTR:host']
        server_status = server_dict['status']
        LOG.info("******* server_status is *******" + str(server_status))
        LOG.info("******* server_host is *******" + str(server_host))
        host_ip = settings.COMPUTE_HOSTS[server_host]
        LOG.info("host ip is" + str(host_ip))
        cmd="virsh -c qemu+tcp://" + host_ip + "/system vncdisplay " + instance.uuid
        LOG.info("cmd=" + cmd)
        p = subprocess.Popen("virsh -c qemu+tcp://" + host_ip + "/system vncdisplay " + instance.uuid, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        port = None
        for line in p.stdout.readlines():
            port = line
            break
        LOG.info("host_ip=" + host_ip)
        LOG.info("port=" + str(port))
        if "error" in str(port):
            return Response({"success": False, "msg": _('Failed to create flavor for unknown reason.')})
        split_port = port.split(":")
        LOG.info(split_port)
        port_1 = split_port[1]
        LOG.info(port_1)
        port_2 = port_1.split("\\")
        LOG.info(port_2)
        port_3 = port_2[0]
        LOG.info(port_3)
        vnc_port = 5900 + int(port_3)
        LOG.info(vnc_port)
        spice_port = int(vnc_port) + 1
        LOG.info(spice_port)
        spice_url = "spicevm:spice:" + host_ip + ":" + str(spice_port)
        LOG.info("*** spice_url is ***" + str(spice_url))
        spice = {"url": spice_url, "type": "spice"}
        LOG.info(spice)

        return spice

