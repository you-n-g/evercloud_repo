"""
User role spec.
"""
from cloud.tasks import user_role


def system_role(request, user):
    role = user_role(request,user)    

    response = False
    if role == "system":
        response = True
    else:
        response = False
    return response

def audit_role(request, user):
    role = user_role(request,user)    

    response = False
    if role == "audit":
        response = True
    else:
        response = False
    return response


def security_role(request, user):
    role = user_role(request,user)    

    response = False
    if role == "security":
        response = True
    else:
        response = False
    return response

def member_role(request, user):
    role = user_role(request,user)    

    response = False
    if role == "member":
        response = True
    else:
        response = False
    return response
