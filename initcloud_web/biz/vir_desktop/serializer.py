# -*- coding: utf-8 -*-

from rest_framework import serializers

class VDStatusSerializer(serializers.Serializer):
    """Serializer class for VDStatusList view

    Attributes:
        user: the user of this virtual desktop
        vm: the virtual desktop
        ip_addr: the IP address of this virtual desktop
    """
    user = serializers.CharField(max_length=200)
    vm = serializers.CharField(max_length=200)
    ip_addr = serializers.CharField(max_length=200)

