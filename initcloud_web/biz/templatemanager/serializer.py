#coding=utf-8

from rest_framework import serializers

from biz.templatemanager.models import Templatemanager 

from biz.idc.serializer import DetailedUserDataCenterSerializer

class TemplatemanagerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Templatemanager 


class DetailedTemplatemanagerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Templatemanager 

