#!/bin/sh
set -e

chown mosquitto:mosquitto -R /var/lib/mosquitto

dockerize -template /etc/mosquitto.d/auth-plugin.conf.tmpl:/etc/mosquitto.d/auth-plugin.conf


if [ "$1" = 'mosquitto' ]; then
    # Wait postgres
    dockerize -timeout 30s -wait tcp://${DB_HOST:-db}:${DB_PORT:-5432}
    sleep 1
    while [ "$(PGPASSWORD=${DB_PASSWORD:-odoo} psql -h ${DB_HOST:-db} -U ${DB_USER:-odoo} -c '' postgres 2>&1)" = "psql: FATAL:  the database system is starting up" ]
    do
      echo "Waiting for the database system to start up"
      sleep 0.1
    done
    # Postgres is up. Go!
	exec /usr/local/sbin/mosquitto -c /etc/mosquitto/mosquitto.conf -v
fi

exec "$@"
