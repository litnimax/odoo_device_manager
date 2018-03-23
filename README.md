# Odoo Device Manager
This is Odoo based alternative to resin.io platform. 

Dependencies:
* **RPC over MQTT** - https://github.com/litnimax/python-mqttrpc
* ** Mosquitto Odoo app**

Work is in progress...

## Concepts
Create an application. Generate an access token. Run supervisor.py like this:
```sh
export REGISTER_URL='http://localhost:8069/device_manager/register?db=test'
export REGISTER_TOKEN='bla-bla-token'
./supervisor.py
```
Each device running supervisor as it's own device uid printed on run:
```
INFO:mqtt_rpc:Client 180725257349411 initialized
```
This device id can be overriden by CLIENT_UID env var.

After device is registered using application token it received 
*username* and *password* for MQTT connection and all other communication is done
using RPC over MQTT. These credintials are saved in *settings.json* file that is 
loaded on start.

After successful startup and connection to MQTT broker supervisor syncronizes application 
services.

A service is a docker container that is pulled from the repository as set in services settings.

All docker operations are controlled from Odoo.

## Running
This repo containes a docker-compose file that consists of the following components:
* PostgreSQL database
* Odoo
* Mosquitto broker
* HTTP bridge built upon MQTTRPC interconnecting Odoo JSON-RPC with MQTT RPC

Start services one by one, as Odoo needs PostgreSQL to be initialized first, and Odoo
itself needs time to create a database. 

## Support & Development
Feel free to create feature requests and bus reports.
