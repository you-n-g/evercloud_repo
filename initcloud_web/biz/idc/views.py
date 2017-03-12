#-*- coding=utf-8 -*-

import logging

from rest_framework import generics, status
from rest_framework.response import Response
#udpate 2016.06.02
from rest_framework.decorators import api_view, permission_classes
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q

from biz.idc.models import DataCenter, UserDataCenter
from biz.account.models import Contract
#update 2016.06.02
from biz.common.views import IsSystemUser, IsAuditUser, IsSafetyUser
#update end
from biz.idc.serializer import DataCenterSerializer, UserDataCenterSerializer
import traceback
import os
import subprocess
import MySQLdb
LOG = logging.getLogger(__name__)

#update 2016.06.02
#update decorators
#@permission_classes((IsSystemUser, ))


class DataCenterList(generics.ListAPIView):

    #update 2016.06.02
    #permission_classes = (IsSystemUser,)
    #update end
 
    queryset = DataCenter.objects.all()
    serializer_class = DataCenterSerializer

    def list(self, request):
        serializer = self.serializer_class(self.queryset, many=True)
        return Response(serializer.data)


class UserDataCenterList(generics.ListAPIView):
    queryset = UserDataCenter.objects.all()
    serializer_class = UserDataCenterSerializer

    def list(self, request):
        queryset = self.get_queryset()
        # If there is user id, retrive user data center which have no contract associated
        if 'user' in request.query_params:
            user_id = request.query_params['user']
            queryset = queryset.filter(user=user_id).exclude(
                contract__in=Contract.objects.filter(user=user_id, deleted=False))

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)


class UserDataCenterDetail(generics.RetrieveAPIView):
    queryset = UserDataCenter.objects.all()
    serializer_class = UserDataCenterSerializer


@api_view(['POST'])
@permission_classes((IsSystemUser, ))
def create_data_center(request):
    try:
        serializer = DataCenterSerializer(data=request.data,
                                        context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True,
                             "msg": _('Data Center is created successfully!')},
                            status=status.HTTP_201_CREATED)
        else:
            return Response({"success": False,
                             "msg": _('Data Center data is not valid!'),
                             'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        LOG.error("Failed to create data center, msg:[%s]" % e)
        return Response({"success": False,
                "msg": _('Failed to create data center for unknown reason.')})


@api_view(['POST'])
def update_data_center(request):
    try:
        pk = request.data['id']
        host = request.data['host']

        if DataCenter.objects.filter(host=host).exclude(pk=pk).exists():
            return Response({"success": False,
                            "msg": _('This host has been used by other data center.')},
                            status=status.HTTP_400_BAD_REQUEST)

        data_center = DataCenter.objects.get(pk=pk)
	LOG.info("--------------------------- test for data_center ------------------")
	old_host = data_center.host
	new_host = request.data['host']
        for field, value in request.data.items():
            setattr(data_center, field, value)
	#ip_files = open('/var/www/initcloud_web/ips.conf', 'r')
	#db = MySQLdb.connect(user='keystone_admin', passwd='d62246baf4464581', db='keystone')
	#cur = db.cursor()
	#try:
	#    cur.execute('update endpoint set url = replace(url, %s,%s)',(old_host,new_host))
	#    db.commit()
	#except:
	#    db.rollback()
	#cur.close()
	#db.close()
	try:
	#    for files in ip_files.readlines():
	#        full_ip_file = '/etc/' + files
	#	cp_cmd = 'sudo cp -f ' + full_ip_file.strip('\n') + ' /var/www/initcloud_web/test_ip'
	#	subprocess.Popen(cp_cmd, shell=True)
	#	sed_cmd = 'sudo sed -i \'s/' + old_host + '/' + new_host + '/g\' ' + full_ip_file.strip('\n')
	#	subprocess.Popen(sed_cmd, shell=True)
	#	restart_openstack_cmd = 'openstack-service restart'
	#	wait1 = subprocess.Popen(restart_openstack_cmd, shell=True)
	#	wait1.wait()
	#	restart_rabbit_cmd = 'systemctl restart rabbitmq-server.service'
	#	wait2 = subprocess.Popen(restart_rabbit_cmd, shell=True)
	#	wait2.wait()
	#	restart_network_cmd = 'systemctl restart network.service'
	#	wait3 = subprocess.Popen(restart_network_cmd, shell=True)
	#	wait3.wait()
	    cmd = 'sudo /var/www/initcloud_web/change_ip.sh ' + old_host + ' ' + new_host
	    subprocess.Popen(cmd,shell=True)
	except:
	    traceback.print_exc()
        data_center.save()
	
        return Response({'success': True,
                        "msg": _('Data Center is updated successfully!')},
                        status=status.HTTP_201_CREATED)
    except Exception as e:
        LOG.error("Failed to create data center, msg:[%s]" % e)
        return Response({"success": False,
                "msg": _('Failed to create data center for unknown reason.')})


@api_view(['POST'])
def delete_data_centers(request):
    try:
        ids = request.data.getlist('ids[]')
        DataCenter.objects.filter(pk__in=ids).delete()

        return Response({'success': True, "msg": _('Data centers have been deleted!')},
                        status=status.HTTP_201_CREATED)
    except Exception as e:
        LOG.error("Failed to delete data centers, msg:[%s]" % e)
        return Response({"success": False, 
                "msg": _('Failed to delete data centers for unknown reason.')})

@api_view(['GET'])
def is_name_unique(request):
    name = request.query_params['name']
    return Response(not DataCenter.objects.filter(name = name).exists())

@api_view(['GET'])
def is_host_unique(request):
    host = request.query_params['host']
    response = os.system("ping -c 1 " + str(host))
    active = False
    if response == 0:
        active = True
    pk = request.query_params.get('id', None)
    queryset = DataCenter.objects.filter(host=host)

    # If pk is not empty, then user must be editing
    # other than creating a data center
    if pk:
        queryset = queryset.exclude(pk=pk)

    if not queryset.exists() and active:
        return Response(True) 
    else:
        return Response(False)
    #return Response(not queryset.exists())


@api_view(["GET"])
def switch_list(request):
    result = {"DataCenterList": []}
    try: 
        current_udc_id = request.session["UDC_ID"]
        udc = UserDataCenter.objects.filter(user=request.user)
        current_udc = UserDataCenter.objects.get(pk=current_udc_id)
        dc = DataCenter.objects.filter(~Q(id=current_udc.data_center.id))
        
        for d in dc:
            result["DataCenterList"].append(
                {
                    "id": d.id,
                    "name": d.name,
                    "is_active": len(udc.filter(data_center = d)) >0,
                })
    except Exception as ex:
       LOG.exception(ex)

    return Response(result, status=status.HTTP_201_CREATED)
