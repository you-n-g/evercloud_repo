# -*- coding: utf-8 -*-
from django.conf import settings
import requests, logging, time

from rest_framework.response import Response
from rest_framework import generics

from biz.common.decorators import require_GET, require_POST
from biz.common.pagination import PagePagination
from biz.vir_desktop.serializer import VDStatusSerializer
from biz.vir_desktop.models import VirDesktopAction
from biz.common.views import IsSystemUser

import cloud.software_mgr_task as mgr

LOG = logging.getLogger(__name__)

# TODO: Remove after merging with Foldex
class VDStatusList(generics.ListAPIView):
    """View class for /api/vdstatus/

    Attributes:
        serializer_class: serializer class for this view
        pagination_class: pagination class for this view
    """
    serializer_class = VDStatusSerializer
    pagination_class = PagePagination
    
    def get_queryset(self):
        LOG.debug("---vir_desktop.views---")
        ret = []
        try:
            LOG.info("Call %s/vdstatus, no parameters" % settings.MGR_HTTP_ADDR)
            r = requests.get('{}/vdstatus'.format(settings.MGR_HTTP_ADDR))
            if r.status_code == 200:
                ret = r.json()
                LOG.debug(ret)
                LOG.info("Call %s/vdstatus success" % settings.MGR_HTTP_ADDR)
            else:
                ret = [{"user": "Error code: "+str(r.status_code), "vm": "null"}]
                LOG.warning("Call %s/vdstatus failed" % settings.MGR_HTTP_ADDR)
        except Exception, e:
            LOG.error("Call %s/vdstatus failed" % settings.MGR_HTTP_ADDR)
        
        return ret

@require_GET
def software_can_setup(request):
    """Use software manager API to get softwares can be installed

    Handle request to /api/software/selectsetup/

    Args:
        requests: http request object

    Returns:
        A response object contains a list of software can be installed
    """
    return Response({'code': 0, 'softwares': mgr.get_available_software()})

@require_GET
def software_can_remove(request):
    """Use software manager API to get softwares can be uninstalled

    Handle request to /api/software/selectremove/

    Args:
        requests: http request object

    Returns:
        A response object contains a list of software can be uninstalled
    """
    addr = request.query_params.get("addr")
    # Use the API to get corresponding data
    try:
        return Response({'code': 0, 'softwares': mgr.get_installed_software(addr)})
    except RuntimeError:
        return Response({'code': 1, 'softwares': []})

@require_POST
def software_setup(request):
    """Use software manager API to install softwares

    Handle request to /api/software/setup/

    Args:
        requests: http request object

    Returns:
        A response object contains status of this operation
    """
    LOG.debug(request.data)
    try:
        rsp = { "success": True, "msg": "Setup OK" }
        users = request.data.getlist("users[]")
        vms = request.data.getlist("vms[]")
        ip_addrs = request.data.getlist("ip_addrs[]")
        softwares = request.data.getlist("softwares[]")
        # Add a log in auditor DB and the status is setuping
        action_ids = []
        for vm in vms:
            action = VirDesktopAction(vm_id=vm, state='setuping')
            action.save()
            LOG.debug("action id: %s" % action.id)
            action_ids.append(action.id)
        rsp["ids"] = action_ids
        # Use the API to setup softwares
        ares = mgr.install_software.delay(action_ids, ip_addrs, softwares)
    except Exception, e:
        LOG.error("---software_setup---: %s" % e)
        rsp["success"] = False
        rsp["msg"] = e

    return Response(rsp)

@require_POST
def software_remove(request):
    """Use software manager API to uninstall softwares

    Handle request to /api/software/remove/

    Args:
        requests: http request object

    Returns:
        A response object contains status of this operation
    """
    try:
        rsp = { "success": True, "msg": "Remove OK" }
        users = request.data.getlist("users[]")
        vms = request.data.getlist("vms[]")
        ip_addrs = request.data.getlist("ip_addrs[]")
        softwares = request.data.getlist("softwares[]")
        # Add a log in auditor DB and the status is removing
        action_ids = []
        for vm in vms:
            action = VirDesktopAction(vm_id=vm, state='removing')
            action.save()
            LOG.debug("action id: %s" % action.id)
            action_ids.append(action.id)
        rsp["ids"] = action_ids
        # Use the API to Remove softwares
        mgr.uninstall_software.delay(action_ids, ip_addrs, softwares)
    except Exception, e:
        LOG.error("---software_remove---: %s" % e)
        rsp["success"] = False
        rsp["msg"] = e

    return Response(rsp)

# API to trace status
@require_GET
def action_status(request):
    """Check the process of install/uninstall operations

    Handle request to /api/software/actionstatus/

    Args:
        requests: http request object

    Returns:
        A response object contains the current status
    """
    action_id = request.query_params.get("vm")
    # product_id = request.query_params.get("product")
    try:
        action = VirDesktopAction.objects.filter(id=action_id)
        LOG.debug("---%d %s %s---" % (len(action), action[0].create_date, action[0].state))
        if len(action) > 0:
            return Response({'status': action[0].state})
    except Exception, e:
        LOG.error("Action status error: %s" % e)
        return Response({'success': False})

