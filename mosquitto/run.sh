#!/bin/sh
set -e

chown mosquitto:mosquitto -R /var/lib/mosquitto

dockerize -template /etc/mosquitto.d/auth-plugin.conf.tmpl:/etc/mosquitto.d/auth-plugin.conf

cat /etc/mosquitto/mosquitto.conf

if [ "$1" = 'mosquitto' ]; then
	exec /usr/local/sbin/mosquitto -c /etc/mosquitto/mosquitto.conf -v
fi

exec "$@"
