#-*- coding=utf-8 -*- 

import logging, time
from celery import app

from biz.vir_desktop.models import VirDesktopAction
from biz.instance.models import Instance

import cloud.api.software_manager.api as mgr


LOG = logging.getLogger(__name__)

def get_available_software():
    return mgr.get_available_software()

def get_installed_software(addr):
    return mgr.get_installed_software(addr)

# TODO: directly change to 
#   get_available_software = mgr.get_available_software
#   get_installed_software = mgr.get_installed_software

@app.task
def install_software(ids, addrs, softwares):
    """Initilize a celery task to execute install operation

    Args:
        ids: IDs of virtual desktop
        addrs: IP addresses of virtual desktop
        softwares: softwares to be installed

    Returns:
        True if install successfully
    """
    try:
        LOG.debug("---install_software---: start task")
        ret = mgr.install_software(softwares, addrs)
        # Change the log's status to install OK/Err in autitor DB
        # time.sleep(5)
        if ret:
            new_state = 'setup_ok'
        else:
            new_state = 'error'
        for vm in ids:
            VirDesktopAction.objects.filter(id=vm).update(state=new_state)
        LOG.debug("---install_software---: finish task")
    except Exception, e:
        LOG.error("---install_software---: %s" % e)
        for vm in ids:
            VirDesktopAction.objects.filter(id=vm).update(state='error')
    
    return True

@app.task
def uninstall_software(ids, addrs, softwares):
    """Initilize a celery task to execute uninstall operation

    Args:
        ids: IDs of virtual desktop
        addrs: IP addresses of virtual desktop
        softwares: softwares to be installed

    Returns:
        True if uninstall successfully
    """
    try:
        LOG.debug("---uninstall_software---: start task")
        ret = mgr.uninstall_software(softwares, addrs)
        # Change the log's status to uninstall OK/Err in autitor DB
        # time.sleep(5)
        if ret:
            new_state = 'remove_ok'
        else:
            new_state = 'error'
        for vm in ids:
            VirDesktopAction.objects.filter(id=vm).update(state=new_state)
        LOG.debug("---uninstall_software---: finish task")
    except Exception, e:
        LOG.error("---uninstall_software---: %s" % e)
        for vm in ids:
            VirDesktopAction.objects.filter(id=vm).update(state='error')
    
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

