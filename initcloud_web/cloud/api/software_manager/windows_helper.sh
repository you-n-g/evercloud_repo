#!/bin/sh

source /var/www/initcloud_web/.venv/bin/activate
DIR="/root/tmp/"


mkdir -p $DIR

# .Net4
if [ ! -e $DIR/dotNetFx40_Full_x86_x64.exe ] ; then 
    wget -P $DIR 'https://download.microsoft.com/download/9/5/A/95A9616B-7A37-4AF6-BC36-D6EA96C8DAAE/dotNetFx40_Full_x86_x64.exe'
fi

# Powershell 3.0
if [ ! -e $DIR/Windows6.1-KB2506143-x86.msu ] ; then 
    wget -P $DIR 'https://download.microsoft.com/download/E/7/6/E76850B8-DA6E-4FF5-8CCE-A24FC513FD16/Windows6.1-KB2506143-x86.msu'
fi

# If you are using x64 system, please use the following command to download the right version
if [ ! -e $DIR/Windows6.1-KB2506143-x64.msu ] ; then 
    wget -P $DIR 'https://download.microsoft.com/download/E/7/6/E76850B8-DA6E-4FF5-8CCE-A24FC513FD16/Windows6.1-KB2506143-x64.msu'
fi

if [ ! -e $DIR/ConfigureRemotingForAnsible.ps1 ] ; then 
    wget -P $DIR 'https://raw.githubusercontent.com/litterbear/ansible/devel/examples/scripts/ConfigureRemotingForAnsible.ps1'
fi

# wget -P $DIR 'https://notepad-plus-plus.org/repository/7.x/7.3/npp.7.3.Installer.exe'
# wget -P $DIR 'https://www.python.org/ftp/python/2.7.13/python-2.7.13.msi'

for url in `python -c "import api; api.Config.print_package_urls()"` ; do
    if [ ! -e $DIR/`basename "$url"` ] ; then 
	wget -P $DIR "$url"
    fi
done

cat <<EOF > $DIR/enable-http-5985
winrm set winrm/config/service/auth @{Basic="true"}
winrm set winrm/config/service @{AllowUnencrypted="true"}
winrm set winrm/config/client/auth @{Basic="true"}
winrm set winrm/config/client @{AllowUnencrypted="true"}
EOF

chmod a+rx /root/
chmod a+rx /root/tmp/
chmod a+r /root/tmp/*

cd $DIR

# python -m SimpleHTTPServer
