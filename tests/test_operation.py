#! /usr/bin/env python
import sys
import json
import requests

# Initcloud API URL
URL = 'http://192.168.1.48:8081/login'

client = requests.session()

# Retrieve the CSRF token first
# Sets cookie
client.get(URL, verify = False) 
csrftoken = client.cookies['csrftoken']
print "******** csrftoken **********"
print csrftoken

# Authenticate
# User created by initcloud(openstack user)
login_data = dict(username='more', password='ydd1121NN', csrfmiddlewaretoken=csrftoken, next='/')
login_return = client.post(URL, data=login_data, headers=dict(Referer=URL))
print "*********** auth status *********"
print login_return.status_code


# Current Operation  Resource, added if necessary
"""
RESOURCE_CHOICES = (
    ("Instance", _("Instance")),
    ("Volume", _("Volume")),
    ("Network", _("Network")),
    ("Subnet", _("Subnet")),
    ("Router", _("Router")),
    ("Floating", _("Volume")),
    ("Firewall", _("Firewall")),
    ("FirewallRules", _("FirewallRules")),
    ("Contract", _("Contract")),
    ("BackupItem", _("BackupItem")),
)


RESOURCE_ACTION_CHOICES = (
    ("reboot", _("reboot")),
    ("power_on", _("power_on")),
    ("power_off", _("power_off")),
    ("vnc_console", _("vnc_console")),
    ("bind_floating", _("bind_floating")),
    ("unbind_floating", _("unbind_floating")),
    ("change_firewall", _("change_firewall")),
    ("attach_volume", _("attach_volume")),
    ("detach_volume", _("detach_volume")),
    ("terminate", _("terminate")),
    ("launch", _("launch")),
    ("create", _("create")),
    ("update", _("update")),
    ("delete", _("delete")),
    ("attach_router", _("attach router")),
    ("detach_router", _("detach router")),
)

Result = (
          ("1": _("success")),
          ("-1": _("failed")),
          ("0": _("error")),
)

Operation_Types(
          ("0": _("logging")),
          ("1": _("alarm")),
)

"""
# Logging
payload = {"user":user, "resource":your_resource, "resource_name": your_resouce_name, "action": your_resource_action, "result": 1, "operation_type": 0}

# Alarm
payload = {"user":user, "resource":your_resource, "resource_name": your_resouce_name, "action": your_resource_action, "result": 1, "operation_type": 1, "message": alarm_message}
# request ulr with get method

URL_ = "http://192.168.1.48:8081/api/operation/collector/"
operation_return = client.get(URL_, params=payload)

print "*********** return status is " + str(operation_return.status_code)
print "*********** return type   is " + str(operation_return.headers['content-type'])
print "*********** content       is \n" + str(operation_return.content)

