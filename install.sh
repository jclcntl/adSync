#!/bin/bash

yum install python-ldap -y

(crontab -l 2>/dev/null; echo "0 * * * * python sync.py") | crontab -

cp nagiosXiConfigTemplate /tmp/nagiosXiConfig
sed -i "s/{{ apikey }}/$(echo $1)/g" /tmp/nagiosXiConfig
sed -i "s/{{ host }}/$(echo $2)/g" /tmp/nagiosXiConfig
sed -i "s/{{ adminFilter }}/$(echo $3)/g" /tmp/nagiosXiConfig
sed -i "s/{{ userFilter }}/$(echo $4)/g" /tmp/nagiosXiConfig
sed -i "s/{{ baseDn }}/$(echo $5)/g" /tmp/nagiosXiConfig
sed -i "s/{{ DC }}/$(echo $6)/g" /tmp/nagiosXiConfig
sed -i "s/{{ ldapServer }}/$(echo $7)/g" /tmp/nagiosXiConfig
