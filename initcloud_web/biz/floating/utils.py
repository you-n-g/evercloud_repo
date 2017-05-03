#coding=utf-8

from cloud.tasks import allocate_floating_task, floating_action_task
from biz.account.models import Operation
from biz.floating.models import Floating
from biz.floating.settings import (ALLOWED_FLOATING_ACTIONS,
                            FLOATING_ACTION_NEXT_STATE,
                            ACTION_FLOATING_ASSOCIATE,)

# Operation status
OPERATION_SUCCESS = 1
OPERATION_FAILED = 0

def allocate_floating(floating):
    """
    Action with allocate fip
    """

    Operation.log(floating, obj_name=floating.ip, action='allocate', result=1)
    allocate_floating_task.delay(floating) 
    return {"OPERATION_STATUS": OPERATION_SUCCESS}


def floating_action(user, DATA):
    """
    floating action, action is a string
    """
    floating_id = DATA.get("floating_id")
    act = DATA.get("action")
    kwargs = DATA
   
    if act not in ALLOWED_FLOATING_ACTIONS.keys():
        return {"OPERATION_STATUS": OPERATION_FAILED, "status": "un supported action [%s]" % act}

    # first,save fip info to db
    floating = Floating.objects.get(pk=floating_id, user=user) 
    floating.status = FLOATING_ACTION_NEXT_STATE[act]
    if act == ACTION_FLOATING_ASSOCIATE:
        resource_type = DATA.get('resource_type')
        resource = DATA.get('resource')
        if resource:
            floating.resource = resource
            floating.resource_type = resource_type
    floating.save()

    # operation logic
    Operation.log(floating, obj_name=floating.ip, action=act, result=1)
   
    # celery handle the request to openstack api 
    floating_action_task.delay(floating, act, **kwargs)

    return {"OPERATION_STATUS": OPERATION_SUCCESS, "status": floating.status}
