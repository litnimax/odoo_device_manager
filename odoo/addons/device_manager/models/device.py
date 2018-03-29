import json
from requests import ConnectionError
import logging
from odoo import models, fields, api, _
from odoo.exceptions import Warning
from tinyrpc.exc import RPCError
from .utils import MqttRpcBridge

logger = logging.getLogger(__name__)

class Device(models.Model):
    _name = 'device_manager.device'
    _rec_name = 'uid'

    uid = fields.Char(required=True, index=True, string="UID", oldname='device_uid')
    application = fields.Many2one(comodel_name='device_manager.application')
    services = fields.One2many(comodel_name='device_manager.device_service',
                               inverse_name='device')
    state = fields.Selection(selection=(
        ('online', 'Online'),
        ('offline', 'Offline'))
    )
    username = fields.Char()
    password = fields.Char()
    last_online = fields.Datetime()
    host_os_version = fields.Char()
    supervisor_version = fields.Char()
    ip_address = fields.Char(string='IP Address')
    commit = fields.Char()
    notes = fields.Text()
    logs = fields.One2many(comodel_name='device_manager.device_log',
                           inverse_name='device')

    ports = fields.One2many(comodel_name='device_manager.device_port',
                            inverse_name='device')
    environment = fields.One2many(comodel_name='device_manager.device_environment',
                            inverse_name='device')

    @api.one
    def application_restart(self):
        self.ensure_one()
        try:
            mqtt_rpc_bridge = MqttRpcBridge(self)
            result = mqtt_rpc_bridge.application_restart(dst=self.uid,
                                                    timeout=30, reload=True)
        except ConnectionError:
            raise Warning('Cannot connect to the bridge')
        except RPCError as e:
            raise Warning('{}'.format(e))



    @api.model
    def application_build(self, uid):
        device = self.env['device_manager.device'].search(
            [('uid', 'in', uid)])
        if not device:
            logger.warning('Device {} not found'.format(uid))
            return {}
        device.last_online = fields.Datetime.now()
        # Add services
        logger.debug('App services: {}'.format(
            [k.name for k in device.application.services]))
        device_services = self.env['device_manager.service'].search(
            [('id', 'in', [k.service.id for k in device.services])])
        logger.debug('Device services: {}'.format([k.name for k in device_services]))
        services_to_add = device.application.services - device_services
        logger.debug('Services to add: {}'.format([s.name for s in services_to_add]))
        device_env = {}
        for s in services_to_add:
            logger.info('Adding service {} to {}'.format(s.name, device.uid))
            d_s = self.env['device_manager.device_service'].create({
                    'service': s.id, 
                    'device': device.id,
                })
            # Copy application ports to device service ports
            for port in s.ports:
                self.env['device_manager.device_port'].create({
                    'device': device.id,
                    'device_port': port.port,
                    'host_port': port.port,
                    'protocol': port.protocol,
                })
            """
            # First take service env
            device_env.update(dict([(e.name, e.value) for e in s.environment]))
            # Now take device env
            device_env.update(dict([(e.name, e.value) for e in device.environment]))
            # Now update device service env
            for name, value in device_env.items():
                self.env['device_manager.device_service_environment'].create({
                    'device_service': d_s.id,
                    'name': name,
                    'value': value,
                })
            """
        # Now delete removed services
        services_to_del = device_services - device.application.services
        logger.debug('Services to del: {}'.format([s.name for s in services_to_del]))
        for s in services_to_del:
            logger.info('Removing service {} from {}'.format(s.name, device.uid))
            d_s = self.env['device_manager.device_service'].search([
                ('device', '=', device.id), ('service', '=', s.id)])
            d_s.unlink()
        # Prepare the result dict
        result = {'services': {}}
        for dev_service in device.services:
            result['services'][
                dev_service.service.id] = dev_service.service_get()[0]
        return result



class DeviceService(models.Model):
    _name = 'device_manager.device_service'

    device = fields.Many2one(comodel_name='device_manager.device',
                             ondelete='cascade')
    service = fields.Many2one(comodel_name='device_manager.service',
                              ondelete='cascade')
    service_name = fields.Char(related='service.name', readonly=True)
    status = fields.Char(compute='status_get')

    _sql_constraints = [
        (
            'uniq',
            'UNIQUE(device,service)',
            _(u'This device already has this service!')
        )
    ]

    @api.one
    def service_get(self):
        self.ensure_one()
        # Merge environment for service and device service
        env = {}
        env.update(dict([(e.name, e.value) for e in self.service.environment]))
        logger.debug('Service env: {}'.format(env))
        # Now take device env
        env.update(dict([(e.name, e.value) for e in self.device.environment]))
        logger.debug('Service & device env: {}'.format(env))
        config = {
            'id': self.service.id,
            'Name': self.service.name,
            'Image': '{}:{}'.format(self.service.image, self.service.tag),
            'Env': ['{}={}'.format(k,v) for k,v in env.items()],
        }
        for p in self.device.ports:
            config.update({
                'PortBindings': {
                    '{}/{}'.format(p.device_port, p.protocol): [
                        {"HostPort": "{}".format(p.host_port)}]}})
        if self.service.cmd:
            config.update({'Cmd': json.loads(self.service.cmd)})
        return config

    @api.one
    def status_get(self):
        self.ensure_one()
        try:
            mqtt_rpc_bridge = MqttRpcBridge(self)
            self.status = mqtt_rpc_bridge.service_status(dst=self.device.uid,
                                                     timeout=2,
                                                     service_id=self.service.id)
        except RPCError:
            self.status = 'error'

    @api.one
    def start(self):
        try:
            mqtt_rpc_bridge = MqttRpcBridge(self)
            mqtt_rpc_bridge.service_start(dst=self.device.uid, timeout=30,
                                      service_id=self.service.id)
        except RPCError as e:
            raise Warning(str(e))

    @api.one
    def stop(self):
        try:
            mqtt_rpc_bridge.service_stop(dst=self.device.uid, timeout=30,
                                     service_id=self.service.id)
        except RPCError as e:
            raise Warning(str(e))

    @api.one
    def restart(self):
        try:
            mqtt_rpc_bridge = MqttRpcBridge(self)
            mqtt_rpc_bridge.service_restart(dst=self.device.uid, timeout=60,
                                        service_id=self.service.id)
        except RPCError as e:
            raise Warning(str(e))


class DeviceLog(models.Model):
    _name = 'device_manager.device_log'
    _order = 'create_date desc'

    device = fields.Many2one(comodel_name='device_manager.device')
    service = fields.Many2one('device_manager.service')
    log = fields.Char()


class DevicePort(models.Model):
    _name = 'device_manager.device_port'
    _order = 'device_port'

    device = fields.Many2one(comodel_name='device_manager.device',
                             required=True, ondelete='cascade')
    device_port = fields.Integer(required=True, help="Port on docker container")
    host_port = fields.Integer(required=True, help="Port on docker host")
    protocol = fields.Selection(selection=(('udp', 'UDP'), ('tcp', 'TCP')),
                                default='tcp', required=True)



class DeviceEnvironment(models.Model):
    _name = 'device_manager.device_environment'
    _order = 'name'

    device = fields.Many2one(comodel_name='device_manager.device',
                             ondelete='cascade')
    name = fields.Char(required=True)
    value = fields.Char()

    _sql_constraints = [
        (
            'uniq_env',
            'UNIQUE(name,value,device)',
            _(u'This var is already defined for this device!')
        )
    ]

