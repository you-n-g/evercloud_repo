# -*- coding:utf-8 -*-

from datetime import datetime
import logging
import os
import etcd
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
from biz.common.decorators import require_POST
from biz.common.utils import retrieve_params

LOG = logging.getLogger(__name__)

@api_view(["GET"])
def list_kv(request):
    LOG.info("list_kv")
    LOG.info(settings.ETCD_IP)
    LOG.info(settings.ETCD_PORT)
    try:
        client = etcd.Client(host=settings.ETCD_IP, port=settings.ETCD_PORT)
        directory = client.get("/")
        LOG.info(directory)
        result = []
        for r in directory.children:
            tmp = {}
            tmp["key"] = r.key.strip('/')
            tmp["value"] = r.value
            result.append(tmp)
        LOG.info(result)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        LOG.error("Failed to List KV, msg:[%s]" % e)
        return Response({"success": False, "msg": _('获取ETCD服务失败 异常 未知原因！')})

@api_view(['POST'])
def create_kv(request):
    LOG.info("create_kv")
    try:
        LOG.info(request.data)
        client = etcd.Client(host=settings.ETCD_IP, port=settings.ETCD_PORT)
        client.write(request.data['key'], request.data['value'])
        return Response(
                {'success': True, "msg": _('部署服务成功！')},
                status='1')
    except Exception as e:
        LOG.error("Failed to create KV, msg:[%s]" % e)
        return Response({"success": False, "msg": _('获取ETCD服务失败 异常 未知原因！')})

@api_view(['POST'])
def update_kv(request):
    try:
        LOG.info("update_kv")
        LOG.info(request.data)
        LOG.info(request.data['key'])
        LOG.info(request.data['value'])
        client = etcd.Client(host=settings.ETCD_IP, port=settings.ETCD_PORT)
        client.write(request.data['key'], request.data['value'])
        return Response(
            {'success': True, "msg": _('KV is updated successfully!')},
            status=status.HTTP_201_CREATED)
    except Exception as e:
        LOG.error("Failed to update KV, msg:[%s]" % e)
        return Response({"success": False, "msg": _(
            'Failed to update KV for unknown reason.')})

@api_view(["POST"])
def delete_kvs(request):
    LOG.info("delete_kvs")
    LOG.info(request.data)
    try:
        keys = request.data.getlist('keys[]')
        LOG.info(keys)
        client = etcd.Client(host=settings.ETCD_IP, port=settings.ETCD_PORT)
        for key in keys:
            client.delete(key)
        return Response({'success': True, "msg": _('KVs have been deleted!')}, status=status.HTTP_201_CREATED)
    except Exception as e:
        LOG.error("Failed to delete KV, msg:[%s]" % e)
        return Response({"success": False, "msg": _(
            'Failed to delete KV for unknown reason.')})