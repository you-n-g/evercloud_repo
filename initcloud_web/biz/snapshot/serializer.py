#coding=utf-8

from rest_framework import serializers

from biz.snapshot.models import Snapshot 

from biz.idc.serializer import DetailedUserDataCenterSerializer

class SnapshotSerializer(serializers.ModelSerializer):

    class Meta:
        model = Snapshot 


class DetailedSnapshotSerializer(serializers.ModelSerializer):

    class Meta:
        model = Snapshot 

