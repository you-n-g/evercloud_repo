#-*-coding=utf-8-*-

import datetime
import logging
import random

from django.conf import settings

from celery import app
from api import keystone
from biz.account.models import Contract
from biz.idc.models import UserDataCenter, DataCenter
from cloud.cloud_utils import create_rc_by_dc
from cloud.network_task import edit_default_security_group

LOG = logging.getLogger("cloud.tasks")


# Sync user to keystone backend
@app.task
def link_user_to_dc_task(user, datacenter, tenant_id, password):

    LOG.info("---------start to execute link_user_to_dc_task-----------")

    LOG.info("----------username is-------------" + str(user.username))

    # Check if user data center existed or not
    if UserDataCenter.objects.filter(
            user=user, data_center=datacenter).exists():
        LOG.info("User[%s] has already registered to data center [%s]",
                 user.username, datacenter.name)
        return True

    LOG.info("-----------datacenter is-----------------" + str(datacenter))

    #create rc for auth.
    rc = create_rc_by_dc(datacenter)
    LOG.info("---------------rc is------------" + str(rc))

    #Now we do not let user to create a new tenant.
    # The following logic is create a new tenant for new created user
    """
    tenant_name = "%s-%04d" % (settings.OS_NAME_PREFIX, user.id)

    keystone_user = "%s-%04d-%s" % (settings.OS_NAME_PREFIX, user.id,
                                    user.username)

    LOG.info("Begin to register user [%s] in data center [%s]",
             user.username, datacenter.name)

    t = keystone.tenant_create(rc, name=tenant_name,
                               description=user.username)
    LOG.info("User[%s] is registered as tenant[id:%s][name:%s] in "
             "data center [%s]", user.username, t.id, tenant_name,
             datacenter.name)
    """
    #Get tenant info from openstack
    tenant_ = keystone.tenant_get(rc, tenant_id)
    tenant_name = tenant_.name 
    LOG.info("************ tenant_name is ************" + str(tenant_name))
    #keystone_user = "%s-%04d-%s" % (settings.OS_NAME_PREFIX, user.id,
    #                                user.username)

    keystone_user = user.username 
    #pwd = "cloud!@#%s" % random.randrange(100000, 999999)
    pwd = password
    
    #hard coded tenant id and name for test.
    project_id = tenant_id 

    # Sync action 
    u = keystone.user_create(rc, name=keystone_user, email=user.email,
                             password=pwd, project=project_id)

    user_uuid = u.id
    LOG.info("User[%s] is registered as keystone user[uid:%s] in "
             "data center[%s]", user.username, u.id, datacenter.name)

    # Get all roles from openstack
    roles = keystone.role_list(rc)
    LOG.info("------------------roles are----------------" + str(roles))

    # Grant basic role to user
    roles_id = []
    for role in roles:
        if role.name in ['SwiftOperator', '_member_', 'heat_stack_owner']:
            roles_id.append(role)

    # Assign role to user
    for role in roles_id:

        try:
            keystone.add_tenant_user_role(rc, project=project_id, user=u.id,
                                         role=role.id)
        except:
            pass


    # Save user info to cloud_web
    udc = UserDataCenter.objects.create(
        data_center=datacenter,
        user=user,
        tenant_name=tenant_name,
        tenant_uuid=project_id,
        keystone_user=keystone_user,
        keystone_password=pwd,
        keystone_user_id=user_uuid
    )

    LOG.info("Register user[%s] to datacenter [udc:%s] successfully",
             user.username, udc.id)


    #Add default security group
    try:
        edit_default_security_group(user, udc)
    except:
        LOG.exception("Failed to edit default security group for user[%s] in "
                      "data center[%s]", user.username, datacenter.name)

    # TODO: For chargesystem logic
    Contract.objects.create(
        user=user,
        udc=udc,
        name=user.username,
        customer=user.username,
        start_date=datetime.datetime.now(),
        end_date=datetime.datetime.now(),
        deleted=False
    )

    return u


# Create a new role in openstack
@app.task
def role_create(request, role_name):


    LOG.info("************* start to create a new role in keystone ***************")
    rc = create_rc_by_dc(DataCenter.objects.all()[0])
    LOG.info("************* rc is ***************" + str(rc))
    try:
        role = keystone.role_create(rc, role_name)
    except:
        return False
    return True

# Delete a role in openstack
@app.task
def role_delete(request, role_name):


    LOG.info("************* start to create a new role in keystone ***************")
    rc = create_rc_by_dc(DataCenter.objects.all()[0])
    LOG.info("************* rc is ***************" + str(rc))

    roles = keystone.role_list(rc)
    role_id = None
    for role_ in roles:
        if role_name == role_.name:
            role_id = role_.id
    try:
        role = keystone.role_delete(rc, role_id)
    except:
        return False
    return True

# Add user role 
@app.task
def add_user_role(keystone_user, role, user_tenant_id):

    # Get default datacenter info
    datacenter = DataCenter.get_default()
    rc = create_rc_by_dc(datacenter)
    LOG.info("********* keystone_user is *********" + str(keystone_user))
    LOG.info("********* role is *********" + str(role))
    LOG.info("********* user_tenant_id is *********" + str(user_tenant_id))
    # get user_id
    users = keystone.user_list(rc, project=user_tenant_id)
    LOG.info("******* users are ******" + str(users))
    user_id = None
    for u in users:
        if u.username == keystone_user:
            user_id = u.id
    LOG.info("****** user_id is *********" + str(user_id))

    # Format role
    role_id = None
    roles = keystone.role_list(rc)
    for r in roles:
        if r.name == role:
            role_id = r.id
    LOG.info("******** role_id is ********" + str(role_id))

    # Openstack action
    try:
        keystone.add_tenant_user_role(rc, project=user_tenant_id, user=user_id,
                                      role=role_id)
    except:
        pass
    return False

# Task: delete a user from user
@app.task
def delete_keystone_user(tenant_id, username):
    datacenter = DataCenter.get_default()
    rc = create_rc_by_dc(datacenter)
    users = keystone.user_list(rc, project=tenant_id)
    LOG.info("******* users are ******" + str(users))
    user_id = None
    for u in users:
        if u.username == username:
            user_id = u.id
    try:
        keystone.user_delete(rc, user_id)
    except:
        pass
    return True

# Task: change user password in openstack
@app.task
def change_user_keystone_passwd(user_id, username, tenant_id, new_passwd):

    datacenter = DataCenter.get_default()
    rc = create_rc_by_dc(datacenter)
    users = keystone.user_list(rc, project=tenant_id)
    LOG.debug("*** rc is ***" + str(rc))
    LOG.info("******* users are ******" + str(users))
    udc_user_id = user_id
    LOG.info("*** udc_user_id is ***" + str(udc_user_id))
    user_id = None
    for u in users:
        if u.username == username:
            user_id = u.id
    LOG.info("**** user_id is ****" + str(user_id))

    # Openstack action
    try:
        keystone.user_update_password(rc, user_id, new_passwd, admin=True)
        LOG.info("**** user password updated ****")
        udc = UserDataCenter.objects.get(user_id=udc_user_id)
        LOG.info("**** user password updated ****")
        udc.keystone_password = new_passwd 
        LOG.info("**** user password updated ****")
        udc.save()
        LOG.info("**** user password updated ****")

    except:
        raise
    return True


# Task: list keystone users
@app.task
def keystone_list_users(request):


    LOG.info("************* start to create a new role in keystone ***************")
    rc = create_rc_by_dc(DataCenter.objects.all()[0])
    LOG.info("************* rc is ***************" + str(rc))
    users = None
    try:
        users = keystone.user_list(rc)
        LOG.info("*** users are ***" + str(users))
    except:
        return False
    return users

# Task: add user role
@app.task
def add_user_role(keystone_user, role, user_tenant_id):

    datacenter = DataCenter.get_default()
    rc = create_rc_by_dc(datacenter)
    LOG.info("********* keystone_user is *********" + str(keystone_user))
    LOG.info("********* role is *********" + str(role))
    LOG.info("********* user_tenant_id is *********" + str(user_tenant_id))
    # get user_id
    users = keystone.user_list(rc, project=user_tenant_id)
    LOG.info("******* users are ******" + str(users))
    user_id = None
    for u in users:
        if u.username == keystone_user:
            user_id = u.id
    LOG.info("****** user_id is *********" + str(user_id))

    role_id = None
    roles = keystone.role_list(rc)
    for r in roles:
        if r.name == role:
            role_id = r.id
    LOG.info("******** role_id is ********" + str(role_id))
    try:
        keystone.add_tenant_user_role(rc, project=user_tenant_id, user=user_id,
                                      role=role_id)
    except:
        pass
    return False


# Task: add user to a tenant
@app.task
def add_user_tenants(request, tenant_id, ID):

    # Get rc info
    datacenter = DataCenter.get_default()
    rc = create_rc_by_dc(datacenter)
    roles = keystone.role_list(rc)
    LOG.info("------------------roles are----------------" + str(roles))

    # Grant basic role to user
    roles_id = []
    for role in roles:
        if role.name in ['SwiftOperator', '_member_', 'heat_stack_owner']:
            roles_id.append(role)


    # Openstack action
    for role in roles_id:
        try:
            keystone.add_tenant_user_role(rc, project=tenant_id, user=ID,
                                         role=role.id)
        except:
            pass
    return True

# Task: delete a user from openstack
@app.task
def user_delete(request, tenant_id, ID):

    datacenter = DataCenter.get_default()
    rc = create_rc_by_dc(datacenter)
    keystone.remove_tenant_user(rc, project=tenant_id, user=ID)
    return True

# Task: create a newproject in openstack
@app.task
def project_create(request, tenant_name, tenant_description):


    LOG.info("************* start to create a new role in keystone ***************")
    rc = create_rc_by_dc(DataCenter.objects.all()[0])
    LOG.info("************* rc is ***************" + str(rc))
    tenant_id = None
    LOG.info("tenant name" + str(tenant_name))
    LOG.info("tenant name" + str(tenant_description))
    try:
        project = keystone.tenant_create(rc, tenant_name)
        LOG.info("*** project is ***" + str(project))
        tenant_id = project.id
        LOG.info(" tenant_id is" + str(tenant_id))
    except:
        return False
    return tenant_id

# Task: delete a project from openstack
@app.task
def project_delete(request, ID):


    LOG.info("************* start to create a new role in keystone ***************")
    rc = create_rc_by_dc(DataCenter.objects.all()[0])
    LOG.info("************* rc is ***************" + str(rc))
    try:
        role = keystone.tenant_delete(rc, ID)
        LOG.info("*** create success ***")
    except:
        return False
    return True

# Task: get user member role from openstack
@app.task
def user_role_member(request,udc_id):

    # Get user info
    UDC = UserDataCenter.objects.get(pk=udc_id)
    LOG.info(UDC)
    keystone_user_id = UDC.keystone_user_id
    tenant_uuid = UDC.tenant_uuid
    rc = create_rc_by_dc(DataCenter.objects.all()[0])

    # List user roles by tenant
    user_roles = keystone.roles_for_user(rc, keystone_user_id, tenant_uuid)
    tri = False
    for user_role in user_roles:
        if user_role.name == "system":
            response = "system" 
            tri = True
            break
        if user_role.name == "security":
            response = "security"
            tri = True
            break
        if user_role.name == "audit":
            response = "audit"
            tri = True
            break
    return tri

# Task: get user role
@app.task
def user_role(request,udc_id):
    UDC = UserDataCenter.objects.get(pk=udc_id)
    LOG.info(UDC)
    keystone_user_id = UDC.keystone_user_id
    tenant_uuid = UDC.tenant_uuid
    rc = create_rc_by_dc(DataCenter.objects.all()[0])
    # List user role
    user_roles = keystone.roles_for_user(rc, keystone_user_id, tenant_uuid)
    for user_role in user_roles:
        if user_role.name == "system":
            response = "system" 
            break
        if user_role.name == "security":
            response = "security"
            break
        if user_role.name == "audit":
            response = "audit"
            break
        if user_role.name == "_member_":
            response = "member"
            break
    return response
