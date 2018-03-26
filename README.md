# Odoo Device Manager
This is Odoo based alternative to resin.io platform. 

Dependencies:
* **RPC over MQTT** - https://github.com/litnimax/python-mqttrpc
* ** Mosquitto Odoo app**

Work is in progress...

## Show me the power of the rocket...
Imagine a docker container running on RPi. And we have the following Odoo
model:
```python
class DeviceService(models.Model):
    _name = 'device_manager.device_service'

    device = fields.Many2one(comodel_name='device_manager.device')
    service = fields.Many2one(comodel_name='device_manager.service')
    service_name = fields.Char(related='service.name', readonly=True)
    status = fields.Char(compute='_get_status')
```
Every time device form is open status is fetched from RPi in realtime using RPC over MQTT:
```
    @api.one
    def _get_status(self):
        self.status = http_bridge.service_status(dst=self.device.uid,
                                            service_id=self.service.id)
```
Broker log:
```
mosquitto_sub -t '#' -v
rpc/180725257349411/odoo {"params": {}, "jsonrpc": "2.0", "method": "service_status", "id": 7}
rpc/180725257349411/odoo/reply {"jsonrpc": "2.0", "id": 7, "result": "running"}
```

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
