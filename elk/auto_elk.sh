yum install -y java-1.8.0-openjdk*
cp -f elk.repo /etc/yum.repos.d/
yum install -y elasticsearch kibana logstash
