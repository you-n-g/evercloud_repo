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
from biz.ceilometer.models import Ceilometer 
from biz.ceilometer.serializer import CeilometerSerializer
from biz.ceilometer.utils import * 
from biz.idc.models import DataCenter
from biz.common.pagination import PagePagination
from biz.common.decorators import require_POST, require_GET
from biz.common.utils import retrieve_params, fail
from biz.workflow.models import Step
from cloud.tasks import (link_user_to_dc_task, send_notifications,
                         send_notifications_by_data_center)
from frontend.forms import CloudUserCreateFormWithoutCapatcha
from cloud.api import nova, ceilometer
from biz.idc.models import UserDataCenter, DataCenter
from cloud.cloud_utils import create_rc_by_udc, create_rc_by_dc
import traceback
from djproxy.views import HttpProxy
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

LOG = logging.getLogger(__name__)

def get_sample_data(request, meter_name, resource_id, project_id = None):
    query = [{'field':'resource_id', 'op':'eq', 'value':resource_id}]
    sample_data = ceilometer.sample_list(request, meter_name, query, limit = 7)
    return sample_data

class MonitorProxy(HttpProxy):
    #base_url = settings.MONITOR_CONFIG['base_url']
    #base_url = "http://192.168.1.51:5601"
    #base_url = "http://192.168.1.51:5601/app/kibana#/visualize/edit/test_1?embed&_a=(filters:!(),linked:!f,query:(query_string:(analyze_wildcard:!t,query:'*')),uiState:(),vis:(aggs:!((enabled:!t,id:'1',params:(),schema:metric,type:count),(enabled:!t,id:'2',params:(field:loglevel.keyword,order:desc,orderBy:'1',size:5),schema:segment,type:terms)),listeners:(),params:(addLegend:!t,addTooltip:!t,isDonut:!f,legendPosition:right,shareYAxis:!t),title:test_1,type:pie))"
    base_url = "http://192.168.1.51:5601/app/kibana#/visualize/"
    #forbidden_pattern = re.compile(r"elasticsearch/.kibana/visualization/")
    def proxy(self):
        #url = self.kwargs.get('url', '')
        #if self.forbidden_pattern.search(url):
        #    return HttpResponse('', status=status.HTTP_403_FORBIDDEN)
        return super(MonitorProxy, self).proxy()

monitor_proxy = login_required(csrf_exempt(MonitorProxy.as_view()))


class CeilometerList(generics.ListAPIView):
    LOG.info("--------- I am ceilometer list in CeilometerList ----------")
    queryset = Ceilometer.objects.all()
    LOG.info("--------- Queryset is --------------" + str(queryset)) 
    serializer_class = CeilometerSerializer
    def list(self, request):
	#udc_id = request.session['UDC_ID']
	#udc = UserDataCenter.objects.get(id = udc_id)
	#rc = create_rc_by_udc(udc)
	dc = DataCenter.get_default()
	rc = create_rc_by_dc(dc)
	try:
	    servers = nova.server_list(rc, all_tenants = True)[0]
	    #LOG.info(servers)
	    for each in servers:
		LOG.info(each.id)
	        disk_write = get_sample_data(rc, 'disk.write.bytes.rate', each.id)
		for sample in disk_write:
		    LOG.info(sample.counter_volume)
	#	LOG.info(disk_write)
	except:
	    traceback.print_exc()
	LOG.info("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzz")
	#disk_write = get_sample_data(rc, 'disk.write.bytes.rate', each.id)
	#disk__read = get_sample_data(rc, 'disk.read.bytes.rate', each.id)
	#cpu_util = get_sample_data(rc, 'cpu_util', each.id)
	return Response()


@require_POST
def create_ceilometer(request):

    try:
        serializer = CeilometerSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, "msg": _('Ceilometer is created successfully!')},
                            status=status.HTTP_201_CREATED)
        else:
            return Response({"success": False, "msg": _('Ceilometer data is not valid!'),
                             'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:

        LOG.error("Failed to create flavor, msg:[%s]" % e)
        return Response({"success": False, "msg": _('Failed to create ceilometer for unknown reason.')})



@api_view(["POST"])
def delete_ceilometers(request):
    ids = request.data.getlist('ids[]')
    Ceilometer.objects.filter(pk__in=ids).delete()
    return Response({'success': True, "msg": _('Ceilometers have been deleted!')}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def update_ceilometer(request):
    try:

        pk = request.data['id']
        LOG.info("---- ceilometer pk is --------" + str(pk))

        ceilometer = Ceilometer.objects.get(pk=pk)
        LOG.info("ddddddddddddd")
        LOG.info("request.data is" + str(request.data))
        ceilometer.ceilometername = request.data['ceilometername']

        LOG.info("dddddddddddd")
        ceilometer.save()
        #Operation.log(ceilometer, ceilometer.name, 'update', udc=ceilometer.udc,
        #              user=request.user)

        return Response(
            {'success': True, "msg": _('Ceilometer is updated successfully!')},
            status=status.HTTP_201_CREATED)

    except Exception as e:
        LOG.error("Failed to update ceilometer, msg:[%s]" % e)
        return Response({"success": False, "msg": _(
            'Failed to update ceilometer for unknown reason.')})


@require_GET
def is_ceilometername_unique(request):
    ceilometername = request.GET['ceilometername']
    LOG.info("ceilometername is" + str(ceilometername))
    return Response(not Ceilometer.objects.filter(ceilometername=ceilometername).exists())
