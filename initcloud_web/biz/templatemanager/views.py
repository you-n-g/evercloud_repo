#-*-coding-utf-8-*-

# Author Yang

from datetime import datetime
from socket import *

import logging
import os
import uuid
import ast
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
from biz.templatemanager.models import Templatemanager 
from biz.templatemanager.serializer import TemplatemanagerSerializer
from biz.templatemanager.utils import * 
from biz.idc.models import DataCenter
from biz.image.models import Image
from biz.common.pagination import PagePagination
from biz.common.decorators import require_POST, require_GET
from biz.common.utils import retrieve_params, fail
from biz.workflow.models import Step
from cloud.tasks import (link_user_to_dc_task, send_notifications,
                         send_notifications_by_data_center)
from frontend.forms import CloudUserCreateFormWithoutCapatcha
from keystoneclient import v2_0
from cloud.api.glance import glanceclient

LOG = logging.getLogger(__name__)


class TemplateManagerList(generics.ListAPIView):
    LOG.info("--------- I am templatemanager list in TemplatemanagerList ----------")

    def list(self, request):
        queryset = Templatemanager.objects.all()
        template = [] 
        template_console = None
        for q in queryset:
            
            LOG.info("ets")
            template_console = "http://" + settings.CONSOLE_IP + ":" + settings.CONSOLE_PORT + "/vnc_auto.html?token=%s" %q.template_uuid
            LOG.info("template_console" + str(template_console))
            template.append({"id": q.id, "template_name": q.template_name, "template_uuid": q.template_uuid, "create_date": q.create_date, "template_softwarelist": q.template_softwarelist, "template_disksize": q.template_disksize, "template_protocol": q.template_protocol, "template_console": template_console})

        LOG.info(template)
        return Response(template)


@require_POST
def create_templatemanager(request):


    template_uuid = uuid.uuid4().hex
    template_baseuuid = ''

    template = request.data.get("template")
    template_iso = request.data.get("iso")
    template_iso = ast.literal_eval(template_iso)
    template_iso_ = None
    for key ,value in template_iso.items():
        template_iso_ = value
    LOG.info("*** template_iso is ***" + str(template_iso_))
    template_vcpu = "1"
    template_memory = "1"
    LOG.info("*** template is ***" +str(template))
    if template == "root":

        LOG.info("start to create root template")
        template_baseuuid = template_uuid
    else:

        LOG.info("start to create child template")
        template_baseuuid = template
    try:
        LOG.info("*** request.data is ***" + str(request.data))
        serializer = Templatemanager(template_name=request.data.get("name"), template_uuid=template_uuid, template_baseuuid=template_baseuuid, template_vcpu=template_vcpu, template_memory=template_memory, template_disksize=request.data.get("disk"), template_protocol=request.data.get("pro"), template_ostype=request.data.get("select_os"), template_iso=template_iso, template_softwarelist=request.data.get("software"), user_id=request.user.id)
        serializer.save()



        ## begin -- construct create root template json message
        template_message = {}
        template_param = {}
        if (template_uuid == template_baseuuid):
            template_message['method']      = 'requestTemplateNew'
        else:
            template_message['method']      = 'requestTemplateCreate'
        template_param['template_name']     = request.data.get('name')
        template_param['template_baseuuid'] = template_baseuuid
        template_param['template_uuid']     = template_uuid
        template_param['template_vcpu']     = '1'
        template_param['template_memory']   = '1'
        template_param['template_disksize'] = request.data.get("disk") 
        template_param['template_protocol'] = request.data.get("pro") 
        template_param['template_serverip'] = '127.0.0.1'
        template_param['template_ostype']   = request.data.get("select_os")
        template_param['template_iso']      = template_iso_
        template_message['param'] = template_param
        send_message = json.dumps(template_message)
        LOG.info("send_message -- " + str(send_message))
        ## end

        ## send to server
        host = '127.0.0.1'
        port = 5999
        sockobj = socket(AF_INET, SOCK_STREAM)
        sockobj.connect((host, port))
        sockobj.send(send_message)
        data = sockobj.recv(1024)
        #print 'Client received:', repr(data)
        sockobj.close()

        return Response({'success': True, "msg": _('Templatemanager is created successfully!')},
                         status=status.HTTP_201_CREATED)
    except Exception as e:
 
        LOG.error("Failed to create flavor, msg:[%s]" % e)
        return Response({"success": False, "msg": _('Failed to create templatemanager for unknown reason.')})



@api_view(["POST"])
def delete_templatemanagers(request):
    ids = request.data.getlist('ids[]')
    Templatemanager.objects.filter(pk__in=ids).delete()
    return Response({'success': True, "msg": _('Templatemanagers have been deleted!')}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def get_isos(request):
    try:

        file_name = os.listdir("/vmstorage/iso/")
        template_iso = []
        i = 1
        for f in file_name:
            template_iso.append({"name":f})
            i = i+1
      
        return Response(template_iso)

    except Exception as e:
        LOG.error("Failed to update templatemanager, msg:[%s]" % e)
        return Response({"success": False, "msg": _(
            'Failed to update templatemanager for unknown reason.')})


@api_view(['GET'])
def get_templates(request):
    try:

        templates = Templatemanager.objects.all()
        templates_ = []

        for template in templates:
            templates_.append({"name": template.template_name, "template_uuid": template.template_uuid})
        return Response(templates_)

    except Exception as e:
        LOG.error("Failed to update templatemanager, msg:[%s]" % e)
        return Response({"success": False, "msg": _(
            'Failed to update templatemanager for unknown reason.')})


@api_view(['POST'])
def update_templatemanager(request):
    try:

        pk = request.data['id']
        LOG.info("---- templatemanager pk is --------" + str(pk))

        templatemanager = Templatemanager.objects.get(pk=pk)
        LOG.info("ddddddddddddd")
        LOG.info("request.data is" + str(request.data))
        templatemanager.templatemanagername = request.data['templatemanagername']

        LOG.info("dddddddddddd")
        templatemanager.save()
        #Operation.log(templatemanager, templatemanager.name, 'update', udc=templatemanager.udc,
        #              user=request.user)

        return Response(
            {'success': True, "msg": _('Templatemanager is updated successfully!')},
            status=status.HTTP_201_CREATED)

    except Exception as e:
        LOG.error("Failed to update templatemanager, msg:[%s]" % e)
        return Response({"success": False, "msg": _(
            'Failed to update templatemanager for unknown reason.')})


@require_GET
def is_templatemanagername_unique(request):
    templatemanagername = request.GET['templatemanagername']
    LOG.info("templatemanagername is" + str(templatemanagername))
    return Response(not Templatemanager.objects.filter(templatemanagername=templatemanagername).exists())

@api_view(['POST'])
def template_action(request, template_id):

    template_id = template_id

    template = Templatemanager.objects.get(pk=template_id) 
    LOG.info("template is" + str(template))
    action = request.data.get("action")
    LOG.info(action)
    template_uuid = template.template_uuid
    template_name = template.template_name
    if action == "power_on":

        LOG.info("start to power_on the template")
        try:
            template_message = {}
            template_param = {}
            template_message['method'] = 'requestTemplateStart'
            template_param['template_uuid'] = template_uuid
            template_message['param'] = template_param
            send_message = json.dumps(template_message)
            LOG.info("666666666")
            ## end
            ## begin -- socket
            host = '127.0.0.1'
            port = 5999
            sockobj = socket(AF_INET, SOCK_STREAM)
            LOG.info("666666666")
            sockobj.connect((host, port))
            sockobj.send(send_message)
            data = sockobj.recv(1024)
            LOG.info('Client received:%s', repr(data))
            sockobj.close( )
        except :

            LOG.error("Failed to create flavor, msg:[%s]" % e)
            return Response({"success": False, "msg": _('Failed to create templatemanager for unknown reason.')})
 

    if action == "power_off":

        LOG.info("start to power_off the template")
        try:

            ## begin start/stop/delete templte
            template_message = {}
            template_param = {}
            template_message['method'] = 'requestTemplateStop'
            template_param['template_uuid'] = template_uuid
            template_message['param'] = template_param
            send_message = json.dumps(template_message)
            ## end
            ## socker send
            host = '127.0.0.1'
            port = 5999
            sockobj = socket(AF_INET, SOCK_STREAM)
            sockobj.connect((host, port))
            sockobj.send(send_message)
            data = sockobj.recv(1024)
            LOG.info('Client received:%s', repr(data))
            sockobj.close( )
            ## end
        except:


            LOG.error("Failed to create flavor, msg:[%s]" % e)
            return Response({"success": False, "msg": _('Failed to create templatemanager for unknown reason.')})


    if action == "template_delete":

        LOG.info("start to delete the template")
        try:
            template_message = {}
            template_param = {}
            template_message['method'] = 'requestTemplateDelete'
            template_param['template_uuid'] = template_uuid
            template_message['param'] = template_param
            send_message = json.dumps(template_message)
            ## end
            ## begin -- socker
            host = '127.0.0.1'
            port = 5999
            sockobj = socket(AF_INET, SOCK_STREAM)
            sockobj.connect((host, port))
            sockobj.send(send_message)
            data = sockobj.recv(1024)
            LOG.info('Client received:%s', repr(data))
            sockobj.close( )
            ## end
            template.delete()
            
        except:

            LOG.error("Failed to create flavor, msg:[%s]" % e)
            return Response({"success": False, "msg": _('Failed to create templatemanager for unknown reason.')})


    if action == "upload":


        LOG.info("start to upload the template")
        try:

            ## begin start/stop/delete templte
            template_message = {}
            template_param = {}
            template_message['method'] = 'requestTemplateUpload'
            template_param['template_uuid'] = template_uuid
            template_param['template_name'] = template_name
            template_message['param'] = template_param
            send_message = json.dumps(template_message)
            ## end
            ## socker send
            host = '127.0.0.1'
            port = 5999
            sockobj = socket(AF_INET, SOCK_STREAM)
            sockobj.connect((host, port))
            sockobj.send(send_message)
            data = sockobj.recv(1024)
            LOG.info('Client received:%s', repr(data))
            sockobj.close( )
            LOG.info("response data is" + str(data))
            if str(data) == "OK":
                images = glanceclient(request).images.list()
                LOG.info("start to get images")
                LOG.info(images)
                for img in images:
                    LOG.info(img)
                    LOG.info("image name is" + str(img.name))
                    if str(img.name) == str(template_name):
                        image_id = img.id
                        LOG.info("image_id is" + str(image_id)) 
                        LOG.info("image_id is" + str(template_name))
                        LOG.info("image_id is" + str(template.template_disksize))
                        data_center = DataCenter.objects.all()[0]
                        LOG.info("data center" + str(data_center))
                        try:
                            glance_obj = Image(name=template_name, disk_size=template.template_disksize, login_name="linux", os_type=2, uuid=image_id, data_center=data_center, create_at=timezone.now())
                        except Exception as e:
                            LOG.exception(e)
                        LOG.info("ccccccc")
                        glance_obj.save()
                        break;
                        LOG.info("glance obj is" + str(glance_obj))
        except:

            LOG.error("Failed to create flavor, msg:[%s]" % e)
            return Response({"success": False, "msg": _('Failed to create templatemanager for unknown reason.')})

    return Response({'success': True, "msg": _('Templatemanager action is created successfully!')},
                      status=status.HTTP_201_CREATED)
@require_POST
def batch_delete(request):

    template_id_list = request.data.getlist('ids[]')
    for template_id in template_id_list:
        template = Templatemanager.objects.get(pk=template_id)
        LOG.info("template is" + str(template))
        template_uuid = template.template_uuid
        template_name = template.template_name

        LOG.info("start to delete the template")
        try:
            template_message = {}
            template_param = {}
            template_message['method'] = 'requestTemplateDelete'
            template_param['template_uuid'] = template_uuid
            template_message['param'] = template_param
            send_message = json.dumps(template_message)
            ## end
            ## begin -- socker
            host = '127.0.0.1'
            port = 5999
            sockobj = socket(AF_INET, SOCK_STREAM)
            sockobj.connect((host, port))
            sockobj.send(send_message)
            data = sockobj.recv(1024)
            LOG.info('Client received:%s', repr(data))
            sockobj.close( )
            ## end
            template.delete()
        except:
            LOG.error("Failed to create flavor, msg:[%s]" % e)
            return Response({"success": False, "msg": _('Failed to create templatemanager for unknown reason.')})
    return Response({'success': True, "msg": _('Templatemanager action is created successfully!')},
                      status=status.HTTP_201_CREATED)
