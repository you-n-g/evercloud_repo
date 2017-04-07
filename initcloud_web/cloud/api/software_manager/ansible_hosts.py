#!/usr/bin/env python
# coding:utf8

import sys
import os
import re
from optparse import OptionParser
import json
import copy
import yaml
import logging
DIRNAME = os.path.abspath(os.path.dirname(__file__))

from django.conf import settings
if not settings.configured:
    sys.path.append(os.path.abspath(os.path.join(DIRNAME,
        os.path.pardir, os.path.pardir, os.path.pardir)))
    import django
    os.environ["DJANGO_SETTINGS_MODULE"] = 'initcloud_web.settings'
    django.setup()


LOG = logging.getLogger(__name__)


'''
Here is an example of config.yml. Hosts is not necessary if you are not
debugging software mangement module alone.
--
ansible_ssh_user: "username"
ansible_ssh_pass: "password"
'''

config_path = os.path.join(DIRNAME, "config.yml")
try:
    with open(config_path) as f:
        config = yaml.load(f)
except IOError:
    LOG.warning("You didn't configure %s, please follow the instructions"
            " of \"cloud/api/software_manager/ansible_hosts.py\" to create the"
            "configuration.")
    config = {
        'ansible_ssh_user': "username",
        'ansible_ssh_pass': "password",
        'hosts': ["192.168.1.1"]
    }



VARS = {
    "ansible_ssh_host": None,
    "ansible_ssh_user": config["ansible_ssh_user"],
    "ansible_ssh_pass": config["ansible_ssh_pass"],
    "ansible_ssh_port": 5985,
    # "ansible_ssh_port": 5986,
    "ansible_connection": "winrm",
    "ansible_winrm_server_cert_validation": "ignore",
}


def get_hosts():
    global hosts
    try:
        from biz.floating.models import Floating
        LOG.info("Getting floating ips from models.")
        fips = [ip.ip for ip in Floating.objects.all()]
    except ImportError:
        fips = config.get("hosts", [])
        LOG.warning("Getting floating ips from config.yml")
    hosts = {
        'all': {
            'hosts': fips,
        }
    }
    return hosts

hosts = get_hosts()


def pick_host(name):
    res = copy.deepcopy(VARS)
    res["ansible_ssh_host"] = name
    return res


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option(
        "--list",
        action="store_true",
        dest="list_host",
        default=None,
        help="list hosts"
    )
    parser.add_option(
        "--host",
        dest="host_name",
        help="get info about a HOST",
        metavar="HOST"
    )

    (options, args) = parser.parse_args()

    if options.host_name:
        print(pick_host(options.host_name))
        sys.exit(0)

    if options.list_host:
        print(json.dumps(get_hosts()))
        sys.exit(0)
