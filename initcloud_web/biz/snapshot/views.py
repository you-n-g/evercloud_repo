#-*-coding-utf-8-*-

# Author Yang

from datetime import datetime
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
from biz.snapshot.models import Snapshot 
from biz.snapshot.serializer import SnapshotSerializer
from biz.snapshot.utils import * 
from biz.idc.models import DataCenter
from biz.common.pagination import PagePagination
from biz.common.decorators import require_POST, require_GET
from biz.common.utils import retrieve_params, fail
from biz.workflow.models import Step
from cloud.tasks import (link_user_to_dc_task, send_notifications,
                         send_notifications_by_data_center)
from frontend.forms import CloudUserCreateFormWithoutCapatcha

LOG = logging.getLogger(__name__)


class SnapshotList(generics.ListAPIView):
    LOG.info("--------- I am snapshot list in SnapshotList ----------")
    queryset = Snapshot.objects.all()
    LOG.info("--------- Queryset is --------------" + str(queryset)) 
    serializer_class = SnapshotSerializer



@require_POST
def create_snapshot(request):

    try:
        serializer = SnapshotSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, "msg": _('Snapshot is created successfully!')},
                            status=status.HTTP_201_CREATED)
        else:
            return Response({"success": False, "msg": _('Snapshot data is not valid!'),
                             'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:

        LOG.error("Failed to create flavor, msg:[%s]" % e)
        return Response({"success": False, "msg": _('Failed to create snapshot for unknown reason.')})



@api_view(["POST"])
def delete_snapshots(request):
    ids = request.data.getlist('ids[]')
    Snapshot.objects.filter(pk__in=ids).delete()
    return Response({'success': True, "msg": _('Snapshots have been deleted!')}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def update_snapshot(request):
    try:

        pk = request.data['id']
        LOG.info("---- snapshot pk is --------" + str(pk))

        snapshot = Snapshot.objects.get(pk=pk)
        LOG.info("ddddddddddddd")
        LOG.info("request.data is" + str(request.data))
        snapshot.snapshotname = request.data['snapshotname']

        LOG.info("dddddddddddd")
        snapshot.save()
        #Operation.log(snapshot, snapshot.name, 'update', udc=snapshot.udc,
        #              user=request.user)

        return Response(
            {'success': True, "msg": _('Snapshot is updated successfully!')},
            status=status.HTTP_201_CREATED)

    except Exception as e:
        LOG.error("Failed to update snapshot, msg:[%s]" % e)
        return Response({"success": False, "msg": _(
            'Failed to update snapshot for unknown reason.')})


@require_GET
def is_snapshotname_unique(request):
    snapshotname = request.GET['snapshotname']
    LOG.info("snapshotname is" + str(snapshotname))
    return Response(not Snapshot.objects.filter(snapshotname=snapshotname).exists())
