#!/bin/bash

env | sort 

echo "Running SSH on port ${SSH_PORT:=22}"

sed -i "s/Port 22/Port ${SSH_PORT:=22}/g" /etc/ssh/sshd_config

exec /usr/sbin/sshd -D -e