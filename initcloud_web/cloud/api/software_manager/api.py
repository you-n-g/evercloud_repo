# coding:utf8

import json
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase

import os
DIRNAME = os.path.abspath(os.path.dirname(__file__))
import ansible_hosts


def execute_tasks(play_name, tasks, hosts, host_list=os.path.join(DIRNAME, 'ansible_hosts.sh'), callback="default"):
    """Execute the task

    :param play_name: the name of the play(a group of task)
    :param tasks: the diction to describe the tasks
    :param hosts: the hosts to execute the tasks
    :param host_list: the script to get the information of the hosts.
    :param callback: user can pass specific callback class to collect the result.

    :rtype: if the task run successfully, it will return 0. Otherwise it will return 0.
    """
    # NOTICE: Here is a trick. The host we acquired must in the host list
    # everytime. However I can't get the host list in advance. So I add the
    # hosts into the host list eveytime if it doesn't exist.
    if hosts not in ansible_hosts.hosts["all"]["hosts"]:
        ansible_hosts.hosts["all"]["hosts"].append(hosts)

    # initialize needed objects
    variable_manager = VariableManager()
    loader = DataLoader()

    # create inventory and pass to var manager
    inventory = Inventory(loader=loader, variable_manager=variable_manager, host_list=host_list)
    variable_manager.set_inventory(inventory)

    # create play with tasks
    play_source = dict(
        name=play_name,
        hosts=hosts,
        gather_facts='no',
        tasks=tasks)

    play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

    Options = namedtuple('Options', ['connection', 'module_path', 'forks',
        'become', 'become_method', 'become_user', 'check'])
    options = Options(connection=None, module_path=None, forks=10, become=None,
        become_method=None, become_user=None, check=False)
    passwords = dict()

    # actually run it
    tqm = None
    try:
        tqm = TaskQueueManager(
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            options=options,
            passwords=passwords,
            stdout_callback=callback)
        return tqm.run(play)
    finally:
        if tqm is not None:
            tqm.cleanup()
        pass


class Config(object):
    """Configuration and helper functions
        
    Attributes:
        package_list: the configuration of the softwares
            here is an configuration example of a msi installation package.
            {
                "name": "python2.7.13(x64)",  # The name of the software, it will be displayed in the frontend.
                "filename": r'python-2.7.13.amd64.msi',  # the file name of the installation package
                "Product_Id": "{4A656C6C-D24A-473F-9747-3A8D00907A04}", # The product id of the package. 
                "url": 'https://www.python.org/ftp/python/2.7.13/python-2.7.13.amd64.msi',  # Here is the download url. It will only be used in `windows_helper.sh`
            },
            here is an configuration example of an exe installation package.
            {
                "name": "Microsoft Visual C thingy(x64)",  # The name of the software, it will be displayed in the frontend.
                "filename": r'vcredist_x64.exe',  # the file name of the installation package
                "Product_Id": "{CF2BEA3C-26EA-32F8-AA9B-331F7E34BA97}",  # The product id of the package. 
                "InstallArguments": "/install /passive /norestart",  # The arguments used when installing the software
                "UninstallArguments": "/uninstall /passive /norestart",  # The arguments used when uninstalling the software
                "url": 'http://download.microsoft.com/download/1/6/B/16B06F60-3B20-4FF2-B699-5E9B7962F9AE/VSU_4/vcredist_x64.exe',  # Here is the download url. It will only be used in `windows_helper.sh`
            },
            You can get the product id by run `Get-WmiObject -Class Win32_Product` in powershell after installation of the software
        dest_dir: the path to upload the installation package in the virtual machine
        package_dir: the path to store the installation package on the server run ansible
        package_list: the configuration of softwares 
        wallpaper_path:  the wallpaper path of the virtual machine
        wallpaper_options: the optional wallpaper path of the virtual machine

    """
    dest_dir = r'C:\\ansible\\'
    package_dir = "/root/tmp/"
    package_list = [
        {
            "name": "Microsoft Visual C thingy(x64)",
            "filename": r'vcredist_x64.exe',
            "Product_Id": "{CF2BEA3C-26EA-32F8-AA9B-331F7E34BA97}",
            "InstallArguments": "/install /passive /norestart",
            "UninstallArguments": "/uninstall /passive /norestart",
            "url": 'http://download.microsoft.com/download/1/6/B/16B06F60-3B20-4FF2-B699-5E9B7962F9AE/VSU_4/vcredist_x64.exe',
        },
        {
            "name": "Microsoft Visual C thingy(x86)",
            "filename": r'vcredist_x86.exe',
            "Product_Id": "{BD95A8CD-1D9F-35AD-981A-3E7925026EBB}",
            "InstallArguments": "/install /passive /norestart",
            "UninstallArguments": "/uninstall /passive /norestart",
            "url": 'http://download.microsoft.com/download/1/6/B/16B06F60-3B20-4FF2-B699-5E9B7962F9AE/VSU_4/vcredist_x86.exe',
        },
        #{
        #    "name": "Notepad++(x86)",
        #    "filename": r'npp.7.3.Installer.exe',
        #    "Product_Id": "Notepad++",
        #    "InstallArguments": "/S",
        #    "UninstallArguments": "/S",
        #    "UninstallFile": r"C:\Program Files\Notepad++\uninstall.exe",
        #    "url": 'https://notepad-plus-plus.org/repository/7.x/7.3/npp.7.3.Installer.exe',
        #},
        {
            "name": "python2.7.13(x86)",
            "filename": r'python-2.7.13.msi',
            "Product_Id": "{4A656C6C-D24A-473F-9747-3A8D00907A03}",
            "url": 'https://www.python.org/ftp/python/2.7.13/python-2.7.13.msi',
        },
        {
            "name": "python2.7.13(x64)",
            "filename": r'python-2.7.13.amd64.msi',
            "Product_Id": "{4A656C6C-D24A-473F-9747-3A8D00907A04}",
            "url": 'https://www.python.org/ftp/python/2.7.13/python-2.7.13.amd64.msi',
        },
        {
            "name": "7zip(x64)",
            "filename": r'7z920-x64.msi',
            "Product_Id": "{23170F69-40C1-2702-0920-000001000000}",
            "url": 'http://www.7-zip.org/a/7z920-x64.msi',
        },
    ]

    # 和桌面背景相关
    wallpaper_path = r"C:\wallpaper\pic.jpg"
    wallpaper_options = {
        "mimi": r"C:\wallpaper\pic1.jpg",
        "jimi": r"C:\wallpaper\pic2.jpg",
    }

    @staticmethod
    def get_software_from_pid(Product_Id):
        """get software configuration by product id

        :param Product_Id: the product id of the software.
        :rtype the detailed software package configuration.
        """
        for software in Config.package_list:
            if software["Product_Id"] == Product_Id:
                return software
        return None

    @staticmethod
    def print_package_urls():
        """print the software download urls.

        It will only be use in the windows_helper.sh
        """
        for software in Config.package_list:
            print software['url']


# 1. 获取可安装软件的列表
def get_available_software():
    """get available software configurations"""
    return Config.package_list


# 2. 获取某个虚拟机已安装软件的列表.
LIST_SCRIPT = '''$UninstallKey="SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall"
#Create an instance of the Registry Object and open the HKLM base key
$reg=[microsoft.win32.registrykey]::OpenRemoteBaseKey(‘LocalMachine’,$computername)
#Drill down into the Uninstall key using the OpenSubKey Method
$regkey=$reg.OpenSubKey($UninstallKey)
#Retrieve an array of string that contain all the subkey names
echo $regkey.GetSubKeyNames()


# get Wow6432Node!!!
$UninstallKey="SOFTWARE\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall"
#Create an instance of the Registry Object and open the HKLM base key
$reg=[microsoft.win32.registrykey]::OpenRemoteBaseKey(‘LocalMachine’,$computername)
#Drill down into the Uninstall key using the OpenSubKey Method
$regkey=$reg.OpenSubKey($UninstallKey)
#Retrieve an array of string that contain all the subkey names
echo $regkey.GetSubKeyNames()
'''


class InstallResultCallback(CallbackBase):
    """A call back class to collect the result when executing ansible tasks successfully
    Attributes:
        result: the return result of the tasks
        host: the hosts where the tasks are executed.
    """

    def v2_runner_on_ok(self, result, **kwargs):
        """A hook function after executing the tasks successfully

        :param result: the result
        :param **kwargs: other arguments will not be used by this class
        """
        self.result = result._result
        self.host = result._host

    def get_result(self):
        """get the result of task"""
        return getattr(self, "result", {})


def get_installed_software(hosts):
    """get installed software of specific host

    :param hosts: the host we are querying
    :raises: RuntimeError when we fail to execute the task,
    """
    callback = InstallResultCallback()
    code = execute_tasks(play_name="List installed software", tasks=[{"raw": LIST_SCRIPT}],
        hosts=hosts, callback=callback)
    if code != 0:
        raise RuntimeError("Error when get installed software, return code is %d." % code)
    return [p for p in Config.package_list if p["Product_Id"] in callback.get_result().get("stdout_lines", [])]


# 3. 给指定虚拟机(列表)安装指定的软件(列表)
def install_software(software_list, hosts_list):
    """install softwares for hosts

    :param software_list: the softwares to be installed.
    :param hosts_list: the hosts where the softwares are installed.

    :rtype: True will be returned if softwares are installed successfully. Otherwise False will be returned.
    """
    res = True
    for hosts in hosts_list:
        for Product_Id in software_list:
            software = Config.get_software_from_pid(Product_Id)
            win_package_task = {
                'action': {
                    'module': 'win_package',
                    'args': {
                        'name': software["name"],
                        'path': Config.dest_dir + software['filename'],
                        'Product_Id': software["Product_Id"],
                    }
                },
                'name': "Installing " + software["name"]
            }
            if software.get("InstallArguments") is not None:
                win_package_task['action']['args']['Arguments'] = software.get("InstallArguments")
            res = res and (0 == execute_tasks(play_name="Installing software", tasks=[
                {
                    "action": {
                        "module": "win_file",
                        "args": {
                            'path': Config.dest_dir,
                            'state': 'directory',
                        }
                    }
                },
                {
                    "action": {
                        "module": "win_copy",
                        "args": {
                            "src": os.path.join(Config.package_dir, software['filename']),
                            "dest": Config.dest_dir,
                        }
                    }
                },
                win_package_task,
            ], hosts=hosts))
    return bool(res)


# 4. 卸载指定虚拟机的指定软件(列表)
def uninstall_software(software_list, hosts_list):
    """uninstall softwares for hosts

    :param software_list: the softwares to be uninstalled.
    :param hosts_list: the hosts where the softwares are uninstalled.

    :rtype: True will be returned if softwares are uninstalled successfully. Otherwise False will be returned.
    """
    res = True
    for hosts in hosts_list:
        for Product_Id in software_list:
            software = Config.get_software_from_pid(Product_Id)
            win_package_task = {
                'action': {
                    'module': 'win_package',
                    'args': {
                        'name': software["name"],
                        'path': Config.dest_dir + software['filename'],
                        'Product_Id': software["Product_Id"],
                        'state': "absent",
                    }
                },
                'name': "Uninstalling " + software["name"]
            }
            if software.get("UninstallArguments") is not None:
                win_package_task['action']['args']['Arguments'] = software.get("UninstallArguments")
            res = res and (0 == execute_tasks(play_name="Uninstalling software", tasks=[
                {
                    "action": {
                        "module": "win_file",
                        "args": {
                            'path': Config.dest_dir,
                            'state': 'directory',
                        }
                    }
                },
                {
                    "action": {
                        "module": "win_copy",
                        "args": {
                            "src": os.path.join(Config.package_dir, software['filename']),
                            "dest": Config.dest_dir,
                        }
                    }
                },
                win_package_task,
            ], hosts=hosts))

    return bool(res)

def set_reg(host_list, key, value, data, state='present', datatype='string'):
    """edit the registry of the hosts

    :param host_list: the hosts whose registry will be edited.
    :param key:  Name of registry path.  Should be in one of the following
                 registry hives: HKCC, HKCR, HKCU, HKLM, HKU.
    :param value: Name of registry entry in path.
    :param data:  Value of the registry entry name in path.
    :param state: State of registry entry. present or absent
    :param datatype: Registry value data type. 
                    (binary , dword , expandstring , multistring , string , qword)

    :rtype: True will be returned if registries are set successfully. Otherwise False will be returned.
    """
    for hosts in host_list:
        if 0 != execute_tasks(play_name="Set Registry Key", tasks=[
            {
                "action": {
                    "module": 'win_regedit',
                    "args": {
                        "key": key,
                        "value": value,
                        "data": data,
                        "datatype": datatype,
                        "state": state,
                    }
                },
                "name": "Set Registry Key",
            },
        ], hosts=hosts):
            # fail to set reg
            return False
    # set reg successfully
    return True


def set_wallpaper(host_list, wallpaper):
    """set wallpaper for hosts

    :param host_list: the hosts to set wall paper
    :param wallpaper:  the wall paper you want. The value can be mimi or jimi
    """
    for hosts in host_list:
        if 0 != execute_tasks(play_name="set_wallpaper", tasks=[
            {
                "action": {
                    "module": 'raw',
                    #"module": 'win_command',
                    #"module": 'win_shell',
                    "args": 'copy %s %s' % (Config.wallpaper_options[wallpaper], Config.wallpaper_path),
                },
                "name": "copy_file",
            },
        ], hosts=hosts):
            # fail to set reg
            return False
    # set reg successfully
    return True
