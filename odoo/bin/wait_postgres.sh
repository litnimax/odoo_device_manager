#!/bin/bash
#
# Wait until postgresql is running.
#
set -e


dockerize -timeout 30s -wait tcp://${DB_HOST:-db}:${DB_PORT:-5432}

# now the port is up but sometimes postgres is not totally ready yet:
# 'createdb: could not connect to database template1: FATAL:  the database system is starting up'
# we retry if we get this error

while [ "$(PGPASSWORD=${DB_PASSWORD:-odoo} psql -h ${DB_HOST:-db} -U ${DB_USER:-odoo} -c '' postgres 2>&1)" = "psql: FATAL:  the database system is starting up" ]
do
  echo "Waiting for the database system to start up"
  sleep 0.1
done