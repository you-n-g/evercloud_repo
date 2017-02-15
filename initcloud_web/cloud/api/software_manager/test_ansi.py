import api

host = "192.168.1.224"

print api.get_installed_software(host)
# api.install_software(api.Config.package_list[1:], ['192.168.1.217'])
api.install_software([api.Config.package_list[1]["Product_Id"]], [host])
print api.get_installed_software(host)
api.uninstall_software([api.Config.package_list[1]["Product_Id"]], [host])
print api.get_installed_software(host)

