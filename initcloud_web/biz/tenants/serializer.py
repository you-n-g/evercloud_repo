#coding=utf-8

from rest_framework import serializers

from biz.tenants.models import Tenants 

from biz.idc.serializer import DetailedUserDataCenterSerializer

class TenantsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tenants 


class DetailedTenantsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tenants 

