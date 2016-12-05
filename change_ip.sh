#cd /etc/
#sed -i 's/192.168.1.53/192.168.1.54/g' `grep -rl '192.168.1.53'`
#mysql -uroot keystone -e "update endpoint set url =  replace(url, '192.168.1.53','192.168.1.54');"
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
