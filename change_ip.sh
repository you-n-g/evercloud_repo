#cd /etc/
#service rabbit-server restart
cd /etc/
for file in `grep -rl $1 * `;
do sudo cp -f $file ${file}.bak;
done
sleep 5
sudo sed -i 's/'$1'/'$2'/g' `grep -rl $1 *|grep -v '.bak'`
sudo mysql -uroot keystone -e "update endpoint set url =  replace(url, '$1','$2');"
service network restart
service rabbitmq-server restart
openstack-service restart
service httpd restart
sudo sed -i 's/'$1'/'$2'/g' /root/keystonerc_admin
sudo sed -i 's/'$1'/'$2'/g' /var/www/initcloud_web/initcloud_web/initcloud_web/settings.py
