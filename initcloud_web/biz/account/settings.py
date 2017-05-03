#coding=utf-8

from django.utils.translation import ugettext_lazy as _


# Signup 
USER_TYPE_CHOICES = (
    (1, _("Personal")),
    (2, _("Company")),
)

# TODO: QUOTA
QUOTA_ITEM = (
    ("instance", _("Instance")),
    ("vcpu", _("CPU")),
    ("memory", _("Memory(MB)")),
    ("volume_size", _("Volume(GB)")),
    ("volume", _("Volume Count")),
    ("floating_ip", _("Floating IP")),
)


# Operation resource choice
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

# Operation resource action choice
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
    ("backup", _("backup")),
    ("restore", _("restore")),
)


class NotificationLevel(object):

    INFO = 1
    SUCCESS = 2
    ERROR = 3
    WARNING = 4
    DANGER = 5

    OPTIONS = (
        (INFO, _("Information")),
        (SUCCESS, _("Success")),
        (ERROR, _("Error")),
        (WARNING, _("Warning")),
        (DANGER, _("Danger")),
    )

    MAP = dict(OPTIONS)

    @classmethod
    def get_label(cls, value, default=""):
        return  cls.MAP.get(value, default)


class TimeUnit(object):

    SECOND = 1000

    MINUTE = 60 * SECOND

    HOUR = 60 * MINUTE

    DAY = 24 * HOUR

    YEAR = 365 * DAY
