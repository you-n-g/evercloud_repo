import api

#host = "172.24.4.227"
host = "192.168.1.205"
print api.get_installed_software(host)
api.install_software(api.Config.package_list[1:], [host])
print api.get_installed_software(host)
api.uninstall_software(api.Config.package_list[1:], [host])
print api.get_installed_software(host)
