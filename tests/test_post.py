#! /usr/bin/env python
import sys
import json
import requests

# Initcloud API URL
URL = 'http://192.168.1.64:8081/login'

client = requests.session()

# Retrieve the CSRF token first
# Sets cookie
client.get(URL, verify = False) 
csrftoken = client.cookies['csrftoken']
print "******** csrftoken **********"

# Authenticate
# User created by initcloud(openstack user)
#login_data = dict(username='admin', password='13456', csrfmiddlewaretoken=csrftoken, next='/')
#login_data = dict(username='admin', password='123456', next='/')
#login_return = client.post(URL, data=login_data, headers=dict(Referer=URL))
print "*********** auth status *********"
#print login_return.status_code

url = "http://192.168.1.64:8081/api/users/"
print client.get(url).content

#URL_ = "http://192.168.1.64:8081/api/instances/"
#payload=dict(test=999, next='/')
#operation_return = client.post(URL_, params=payload, headers=dict(Referer=URL_))

#print "*********** return status is " + str(operation_return.status_code)
#print "*********** return type   is " + str(operation_return.headers['content-type'])
#print "*********** content       is \n" + str(operation_return.content)

