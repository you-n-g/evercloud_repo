#!/bin/sh

rm -fr /var/www/initcloud_web/initcloud_web/render/static/assets/admin/layout/img/favicon.ico
cp favicon.ico /var/www/initcloud_web/initcloud_web/render/static/assets/admin/layout/img/favicon.ico

rm -fr /var/www/initcloud_web/initcloud_web/render/static/assets/admin/layout/img/logo.png
cp logo.png /var/www/initcloud_web/initcloud_web/render/static/assets/admin/layout/img/logo.png

rm -fr /var/www/initcloud_web/initcloud_web/render/static/assets/admin/layout/img/logo-big.png
cp logo-big.png /var/www/initcloud_web/initcloud_web/render/static/assets/admin/layout/img/logo-big.png

rm -fr /var/www/initcloud_web/initcloud_web/render/static/custom/img/logo-big.png
cp logo-big.png /var/www/initcloud_web/initcloud_web/render/static/custom/img/logo-big.png

rm -fr /var/www/initcloud_web/initcloud_web/render/static/custom/img/logo.png
cp logo.png /var/www/initcloud_web/initcloud_web/render/static/custom/img/logo.png

systemctl restart memcached.service

