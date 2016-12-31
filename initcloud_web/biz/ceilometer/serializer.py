#coding=utf-8

from rest_framework import serializers

from biz.ceilometer.models import Ceilometer 

from biz.idc.serializer import DetailedUserDataCenterSerializer

class CeilometerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ceilometer 


class DetailedCeilometerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ceilometer 

