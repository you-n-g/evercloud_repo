#coding=utf-8

import logging

from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.decorators import api_view

from biz.image.models import Image
from biz.image.serializer import ImageSerializer
from biz.account.models import UserProxy
from biz.idc.models import UserDataCenter
from biz.common.decorators import require_POST, require_GET
from cloud.cloud_utils import create_rc_by_dc
from django.conf import settings
from biz.idc.models import DataCenter
from cloud.api import glance
import traceback

LOG = logging.getLogger(__name__)


class ImageList(generics.ListCreateAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

    def list(self, request, *args, **kwargs):

        queryset = self.get_queryset()
        user = request.user

        user_ = UserProxy.objects.get(pk=user.pk)
   
        if user_.is_system_user:
            LOG.info("******* image system user *******")
            return Response(ImageSerializer(queryset, many=True).data)

        if user_.is_safety_user:
            LOG.info("******* image safety user *******")
            return Response(ImageSerializer(queryset, many=True).data)

        if user_.is_audit_user:
            LOG.info("******* image audit user *******")
            return Response(ImageSerializer(queryset, many=True).data)

        if not request.user.is_superuser:
            udc = UserDataCenter.objects.get(pk=request.session["UDC_ID"])
            queryset = queryset.filter(data_center=udc.data_center)
            queryset = queryset.filter(Q(user=None) | Q(user=request.user))

        return Response(ImageSerializer(queryset, many=True).data)


class ImageDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer


@api_view(["POST"])
def create_image(request):
    try:
        request.data['login_name'] = 'user'
        serializer = ImageSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, "msg": _('Image is created successfully!')},
                            status=status.HTTP_201_CREATED)
        else:
            return Response({"success": False, "msg": _('Image data is not valid!'),
                             'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        LOG.error("Failed to create image, msg:[%s]" % e)
        #return Response({"success": False, "msg": _('Failed to create image for unknown reason.')})
        return Response({"success": False, "msg": str(e)})


@api_view(["POST"])
def update_image(request):
    try:

        image = Image.objects.get(pk=request.data['id'])

        serializer = ImageSerializer(instance=image, data=request.data, context={"request": request})

        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, "msg": _('Image is updated successfully!')},
                            status=status.HTTP_201_CREATED)
        else:
            return Response({"success": False, "msg": _('Image data is not valid!'),
                             'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        LOG.error("Failed to create image, msg:[%s]" % e)
        return Response({"success": False, "msg": _('Failed to update image for unknown reason.')})


@api_view(["POST"])
def delete_images(request):

    ids = request.data.getlist('ids[]')

    Image.objects.filter(pk__in=ids).delete()

    return Response({'success': True, "msg": _('Images have been deleted!')}, status=status.HTTP_200_OK)

@require_GET
def is_uuid_unique(request):
    LOG.info(request.GET['uuid'])
    rc = create_rc_by_dc(DataCenter.objects.all()[0])
    try:
        uuid = request.GET['uuid']
        LOG.info("uuid is" + str(uuid))
        client = glance.glanceclient_tm(rc, settings.GLANCE_ENDPOINT, version='2')
        LOG.info("client is" + str(client))
        try:
            images = client.images.get(str(uuid))
        except Exception as e:
            LOG.info(str(e))
        
        return Response(True)
    except:
	return Response(False)
