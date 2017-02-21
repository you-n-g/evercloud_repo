# !/bin/sh
export PYTHONOPTIMIZE=1

echo "\n---------------- restart httpd.service -----------------"
systemctl restart httpd.service


echo "\n---------------- stop celery ---------------------------"
pushd .
cd /var/www/initcloud_web/initcloud_web/
/var/www/initcloud_web/.venv/bin/celery multi stop initcloud_worker --pidfile=/var/log/initcloud/celery_%n.pid
popd
/etc/init.d/celeryd stop
/etc/init.d/celerybeat stop

echo "\n------------------ start celery -------------------------"
pushd .
su - initcloud -c "cd /var/www/initcloud_web/initcloud_web/; PYTHONOPTIMIZE=1  ../.venv/bin/python -O /var/www/initcloud_web/.venv/bin/celery multi restart initcloud_worker -A cloud --pidfile=/var/log/initcloud/celery_%n.pid --logfile=/var/log/initcloud/celery_%n.log &"
popd

/etc/init.d/celeryd start
/etc/init.d/celerybeat start

/etc/init.d/celeryd status
/etc/init.d/celerybeat status


