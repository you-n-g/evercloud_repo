#-*- coding=utf-8 -*- 

import logging, time
from celery import app

from biz.vir_desktop.models import VirDesktopAction
from biz.instance.models import Instance

import cloud.api.software_manager.api as mgr
# import cloud.api as mgr


LOG = logging.getLogger(__name__)

# data for testing
soft_list = []
for i in range(20):
    soft_list.append({"name": "software" + str(i)})

# @app.task
def get_available_software():
    # time.sleep(3)
    # return soft_list
    return mgr.get_available_software()

# @app.task
def get_installed_software(addr):
    # time.sleep(3)
    # return soft_list
    return mgr.get_installed_software(addr)

@app.task
def install_software(ids, addrs, softwares):
    for aid, addr in zip(ids, addrs):
        try:
            LOG.info("---install_software---: start task")
            LOG.info("softwares=%s, addr=%s" % (str(softwares), str(addr)))
            ret = mgr.install_software(softwares, [addr])
            # Change the log's status to install OK/Err in autitor DB
            # time.sleep(5)
            if ret:
                new_state = 'setup_ok'
            else:
                new_state = 'error'
            VirDesktopAction.objects.filter(id=aid).update(state=new_state)
            LOG.info("---install_software---: finish task")
        except Exception, e:
            LOG.info("---install_software---: %s" % e)
            VirDesktopAction.objects.filter(id=aid).update(state='error')
    
    return True

@app.task
def uninstall_software(ids, addrs, softwares):
    for aid, addr in zip(ids, addrs):
        try:
            LOG.info("---uninstall_software---: start task")
            LOG.info("softwares=%s, addr=%s" % (str(softwares), str(addr)))
            ret = mgr.uninstall_software(softwares, [addr])
            # Change the log's status to uninstall OK/Err in autitor DB
            # time.sleep(5)
            if ret:
                new_state = 'remove_ok'
            else:
                new_state = 'error'
            VirDesktopAction.objects.filter(id=aid).update(state=new_state)
            LOG.info("---uninstall_software---: finish task")
        except Exception, e:
            LOG.info("---uninstall_software---: %s" % e)
            VirDesktopAction.objects.filter(id=aid).update(state='error')
    
    return True

@app.task
def set_wallpaper(instance, host_list, wallpaper):
    try:
        LOG.info("---set wallpaper---: start task")
        ret = mgr.set_wallpaper(host_list, wallpaper)                                                                                   
        if ret:                                                                                                                         
            Instance.objects.filter(id=instance.id).update(security_cls=Instance.JIMI)                                                  
            LOG.info("Set wallpaper successfully")                                                                                      
        else:                                                                                                                           
            Instance.objects.filter(id=instance.id).update(security_cls=Instance.MIMI)                                             
            LOG.info("Fail to set wallpaper")      
        LOG.info("---set wallpaper---: finish task")
    except Exception, e:
        LOG.info("---set wallpaper---: %s" % e)
        Instance.objects.filter(id=instance.id).update(security_cls=Instance.MIMI)
    return True

