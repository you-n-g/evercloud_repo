#!/bin/sh

# 1 install software
yum -y groupinstall "Development tools"
yum -y install openldap openldap-devel libffi-devel python-pip mariadb-devel python-devel

# 2 add initcloud user/group
groupadd initcloud
useradd initcloud -g initcloud -m -d /home/initcloud
echo "initcloud ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/initcloud

# 3 log
mkdir -p /var/log/initcloud
chown -R initcloud:initcloud /var/log/initcloud

# 4 config initcloud_web
#pushd .
#cp -a ../initcloud_web /var/www/
#cd /var/www/initcloud_web
#pip install virtualenv
#virtualenv .venv
#/var/www/initcloud_web/.venv/bin/pip install -r requirements.txt
#popd


# 5 create db and user
/usr/bin/mysql -u root < cloud_web.sql

# 6 generate local_settings.py
pushd .
cd /var/www/initcloud_web/
/var/www/initcloud_web/.venv/bin/python initcloud_web/manage.py migrate_settings
popd

# 7 migrate db
pushd .
cd /var/www/initcloud_web/
/var/www/initcloud_web/.venv/bin/python initcloud_web/manage.py migrate
popd

# 8 create super user
pushd .
cd /var/www/initcloud_web/
/var/www/initcloud_web/.venv/bin/python initcloud_web/manage.py createsuperuser
popd

#Username (leave blank to use 'root'): zhouxuhong
#Email address: zhouxuhong@gmail.com
#Password:
#Password (again):
#Superuser created successfully.

# 9 init flavor
pushd .
cd /var/www/initcloud_web/
/var/www/initcloud_web/.venv/bin/python initcloud_web/manage.py init_flavor
popd

# 10 test webserver
#pushd .
#cd /var/www/initcloud_web/
#/var/www/initcloud_web/.venv/bin/python initcloud_web/manage.py runserver 0.0.0.0:8081
#popd


# 11 rabbit configure
rabbitmqctl add_user initcloud_web password
rabbitmqctl add_vhost initcloud
rabbitmqctl set_permissions -p initcloud initcloud_web ".*" ".*" ".*"
cp celery/celeryd.conf /etc/default/celeryd
cp celery/celeryd /etc/init.d/celeryd
cp celery/celerybeat /etc/init.d/celerybeat
chown -R initcloud:initcloud /var/log/initcloud/celery_task.log
chgrp -R initcloud /var/log/initcloud/celery_task.log
chown -R initcloud:initcloud /var/log/initcloud/initcloud.log
chgrp -R initcloud /var/log/initcloud/initcloud.log
chmod +x /etc/init.d/celeryd
/etc/init.d/celeryd restart
/etc/init.d/celeryd status
chmod +x /etc/init.d/celerybeat
/etc/init.d/celerybeat stop
/etc/init.d/celerybeat start
/etc/init.d/celerybeat status


# 12 run_celery with auto start
#vim /etc/rc.d/rc.local
echo -e 'su - initcloud -c "cd /var/www/initcloud_web/initcloud_web/;/var/www/initcloud_web/.venv/bin/celery multi restart initcloud_worker -A cloud --pidfile=/var/log/initcloud/celery_%n.pid --logfile=/var/log/initcloud/celery_%n.log &"' >> /etc/rc.local
chmod +x /etc/rc.d/rc.local


# 13 deploy on apache (nginx in beta3)
#echo "Listen 8081" >> /etc/httpd/conf/ports.conf
cp 16-initcloud_web.conf /etc/httpd/conf.d/
systemctl restart httpd.service

# 14 make template storage
mkdir /data/
chmod 777 /data/
echo "100" > /data/index
chmod 777 /data/index

## slyt LVM
mkdir /opt/disks
chown qemu:qemu disks/
chmod 777 disks/
