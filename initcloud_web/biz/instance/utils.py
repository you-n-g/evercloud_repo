#-*- coding=utf-8 -*-

import logging

from django.utils.translation import ugettext_lazy as _

from biz.account.models import Operation
from biz.backup.models import BackupItem
from biz.instance.models import Instance
from biz.instance.settings import (ALLOWED_INSTANCE_ACTIONS,
                                   INSTANCE_ACTION_NEXT_STATE)
from cloud.cloud_utils import create_rc_by_instance
from biz.billing.models import Order

from cloud.tasks import (instance_status_synchronize_task,
                         instance_get_vnc_console, instance_get_spice_console, instance_get_realvnc_console)
from cloud.api import nova

from django.conf import settings
import datetime
from cloud.cloud_utils import get_nova_admin
from biz.instance.settings import (INSTANCE_STATE_RUNNING,
                                   INSTANCE_STATE_BOOTING, INSTANCE_STATE_ERROR,
                                   INSTANCE_STATE_DELETE,
                                   INSTANCE_STATE_POWEROFF)
import cloud.api.software_manager.api as software_api

OPERATION_SUCCESS = 1
OPERATION_FAILED = 0
OPERATION_FORBID = 2

LOG = logging.getLogger(__name__)

def get_ins_status(ins):
    if ins.status == u'ACTIVE':
	return INSTANCE_STATE_RUNNING
    elif ins.status == u"ERROR":
	return INSTANCE_STATE_ERROR
    elif ins.status == u"None":
        return INSTANCE_STATE_ERROR
    elif ins.status == u"SHUTOFF":
        return INSTANCE_STATE_POWEROFF
    elif ins.status == u"VERIFY_RESIZE":
	return 99
    else:
	LOG.info("-------------- WRONG STATUS------------")
	return 11

def flavor_create(instance):
    assert instance
    def _generate_name(instance):
        name = u"%s.cpu-%s-ram-%s-disk-%s-core-%s-socket-%s" % (settings.OS_NAME_PREFIX,
                    instance.cpu, instance.memory, instance.sys_disk, instance.core, instance.socket)
        return name

    def _get_flavor_by_name(instance, name):
        rc = create_rc_by_instance(instance)
        flavor = None
        novaAdmin = get_nova_admin(instance)
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

    begin = datetime.datetime.now()
    rc = create_rc_by_instance(instance)
    name = _generate_name(instance)
    flavor = _get_flavor_by_name(instance, name)
    metadata = {"hw:cpu_cores":instance.core,"hw:cpu_sockets":instance.socket}
    if flavor is None:
        try:
            LOG.info(u"Flavor not exist, create new, [%s][%s].", instance, name)

            novaadmin = get_nova_admin(instance)
            flavor = novaadmin.flavors.create(ram=instance.memory, name=name,
                                  vcpus=instance.cpu, disk=instance.sys_disk,
                                  is_public=True)
            flavor.set_keys(metadata)
            #LOG.info(flavor.get_keys(flavor))
        except nova.nova_exceptions.Conflict:
            LOG.info(u"Flavor name conflict, [%s][%s].", instance, name)
            flavor = _get_flavor_by_name(instance, name)
        except:
            raise

    end = datetime.datetime.now()
    LOG.info(u"Flavor create end, [%s][%s], apply [%s] seconds.",
                instance, name, (end-begin).seconds)
    return flavor


def get_instance_spice_console(instance):
    spice = instance_get_spice_console(instance)
    LOG.info("*** spice is ***" + str(spice))
    LOG.info(spice['url'])
    if spice and spice['url']:
        LOG.info("success")
        return {"OPERATION_STATUS": OPERATION_SUCCESS,
                "spice_url": spice['url']}

    else:
        return {"OPERATION_STATUS": OPERATION_FAILED}


def get_instance_vnc_console(instance):
    vnc = instance_get_realvnc_console(instance)
    LOG.info("**** vnc is ****" + str(vnc))
    if vnc and vnc['url']:
        return {"OPERATION_STATUS": OPERATION_SUCCESS,
                "vnc_url": vnc['url']}
    else:
        return {"OPERATION_STATUS": OPERATION_FAILED}


def get_instance_novnc_console(instance):
    vnc = instance_get_vnc_console(instance) 
    if vnc and vnc.url:
        return {"OPERATION_STATUS": OPERATION_SUCCESS,
                "novnc_url": "%s&instance_name=%s(%s)" % (
                    vnc.url, instance.name, instance.uuid)}
    else:
        return {"OPERATION_STATUS": OPERATION_FAILED}


def set_instance_jimi(instance):
    # import rpdb; rpdb.set_trace()
    if instance.is_running and instance.public_ip and software_api.set_wallpaper([instance.public_ip], "jimi"):
        instance.security_cls = Instance.JIMI
        instance.save()
        return {"OPERATION_STATUS": OPERATION_SUCCESS, "status": instance.status}
    return {"OPERATION_STATUS": OPERATION_FAILED, "status": instance.status}


def _server_reboot(rc, instance):
    if instance.uuid:
        nova.server_reboot(rc, instance.uuid)
    return True


def _server_delete(rc, instance):
    if instance.uuid:
        try:
            nova.server_delete(rc, instance.uuid) 
        except nova.nova_exceptions.NotFound:
            pass
    return True


def _server_start(rc, instance):
    if instance.uuid:
        nova.server_start(rc, instance.uuid)
    return True


def _server_stop(rc, instance):
    if instance.uuid:
        nova.server_stop(rc, instance.uuid)
    return True


def _server_unpause(rc, instance):
    if instance.uuid:
        nova.server_unpause(rc, instance.uuid)
    return True


def _server_pause(rc, instance):
    if instance.uuid:
        nova.server_pause(rc, instance.uuid)
    return True


def instance_action(user, instance_id, action):
    if action not in ALLOWED_INSTANCE_ACTIONS.keys():
        return {"OPERATION_STATUS": OPERATION_FAILED,
                "status": "Unsupported action [%s]" % action}
    #instance = Instance.objects.get(pk=instance_id, user=user, deleted=False)
    instance = Instance.objects.get(pk=instance_id, deleted=False)
    # restoring instance can't do any action!

    if BackupItem.is_any_restoring(instance):
        return {"OPERATION_STATUS": OPERATION_FORBID,
                "MSG": _("Cannot operate this instance because it's in "
                         "restore process."),
                "status": instance.status}

    if action in ('reboot', 'power_on'):
        for volume in instance.volume_set.all():

            if BackupItem.is_any_restoring(volume):
                return {"OPERATION_STATUS": OPERATION_FAILED,
                        "MSG": _("Cannot operate this instance because "
                                 "one volume attached to it is in "
                                 "restore process."),
                        "status": instance.status}

    if action == 'terminate' and \
        BackupItem.living.filter(
            resource_id=instance.id,
            resource_type=Instance.__name__).exists():

        return {"OPERATION_STATUS": OPERATION_FAILED,
                "MSG": _("This instance have backup chains, please delete "
                         "these first."),
                "status": instance.status}

    if action == 'terminate':
        Order.disable_order_and_bills(instance)

    if action == "vnc_console":
        return get_instance_vnc_console(instance)

    if action == "spice_console":
        LOG.info("*** start to get spice console ***")
        return get_instance_spice_console(instance)


    if action == "novnc_console":
        return get_instance_novnc_console(instance)

    if action == "set_jimi":
        return set_instance_jimi(instance)

    Operation.log(instance, obj_name=instance.name, action=action)
    

    _ACTION_MAPPING = {
        "reboot": _server_reboot,
        "terminate": _server_delete,
        "power_on": _server_start,
        "power_off": _server_stop,
        "restore": _server_unpause,
        "pause": _server_pause,
    }

    try:
        rc = create_rc_by_instance(instance)
        act = _ACTION_MAPPING.get(action)
        act(rc, instance)
        instance.status = INSTANCE_ACTION_NEXT_STATE[action]
        instance.save()
        instance_status_synchronize_task.delay(instance, action)
    except Exception as ex:
        LOG.exception("Instance action [%s] raise exception, [%s].",
                            action, instance)
        return {"OPERATION_STATUS": OPERATION_FAILED, 
                "status": "%s" % ex.message}
    else: 
        return {"OPERATION_STATUS": OPERATION_SUCCESS, "status": instance.status}

