#coding=utf-8

from django.utils.translation import ugettext_lazy as _


# Floating ip available status
FLOATING_ERROR = 0
FLOATING_ALLOCATE = 1
FLOATING_APPLYING = 2
FLOATING_REJECTED = 3
FLOATING_AVAILABLE = 10
FLOATING_BINDED = 20
FLOATING_BINDING = 21
FLOATING_RELEASED = 90
FLOATING_RELEASING = 91


# Floating ip status i18n
FLOATING_STATUS = (
    (FLOATING_ERROR, _("Floating ERROR")),
    (FLOATING_ALLOCATE, _("Floating Allocate")),
    (FLOATING_APPLYING, _("Applying")),
    (FLOATING_REJECTED, _("Rejected")),
    (FLOATING_AVAILABLE, _("Floating Avaiable")),
    (FLOATING_BINDED, _("Floating Binded")), 
    (FLOATING_BINDING, _("Floating Binding")), 
    (FLOATING_RELEASED, _("Floating Released")), 
    (FLOATING_RELEASING, _("Floating Releasing")),
)

CANNOT_BILL_STATES = (FLOATING_APPLYING, FLOATING_ERROR,
                      FLOATING_RELEASED, FLOATING_RELEASING)

# 0表示不稳定，1表示稳定
FLOATING_STATUS_DICT = {
    FLOATING_ERROR: (_("Floating ERROR"), 1),
    FLOATING_ALLOCATE: (_("Floating Allocate"), 0),
    FLOATING_APPLYING: (_("Applying"), 0),
    FLOATING_REJECTED: (_("Rejected"), 1),
    FLOATING_AVAILABLE: (_("Floating Avaiable"), 1),
    FLOATING_BINDED: (_("Floating Binded"), 1), 
    FLOATING_BINDING: (_("Floating Binding"), 0), 
    FLOATING_RELEASED: (_("Floating Released"), 1), 
    FLOATING_RELEASING: (_("Floating Releasing"), 0), 
}


# Floating ip available action
ACTION_FLOATING_ALLOCATE = "allocate"
ACTION_FLOATING_RELEASE = "release"
ACTION_FLOATING_ASSOCIATE = "associate"
ACTION_FLOATING_DISASSOCIATE = "disassociate"


# Floating ip next state
FLOATING_ACTION_NEXT_STATE = {
    ACTION_FLOATING_ALLOCATE: FLOATING_AVAILABLE,
    ACTION_FLOATING_RELEASE: FLOATING_RELEASING,
    ACTION_FLOATING_ASSOCIATE: FLOATING_BINDING,
    ACTION_FLOATING_DISASSOCIATE: FLOATING_RELEASING,
}

# Allowed floating actions
ALLOWED_FLOATING_ACTIONS = {
    ACTION_FLOATING_ALLOCATE: _("allocate"),
    ACTION_FLOATING_RELEASE: _("release"),
    ACTION_FLOATING_ASSOCIATE: _("associate"),
    ACTION_FLOATING_DISASSOCIATE : _("disassociate"),
}


RESOURCE_INSTANCE = 'INSTANCE'
RESOURCE_LOADBALANCER = 'LOADBALANCER'

#绑定公网IP资源类型
RESOURCE_TYPE = (
    ('INSTANCE', 'INSTANCE'),
    ("LOADBALANCER", 'LOADBALANCER'),
)

