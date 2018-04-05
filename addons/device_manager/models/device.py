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
    _inherits = {
        'mosquitto.account': 'mqtt_account',
        'res.users': 'user' 
    }
    _rec_name = 'uid'

    uid = fields.Char(required=True, index=True, string="UID", oldname='device_uid')
    application = fields.Many2one(comodel_name='device_manager.application',
                                  required=True)
    services = fields.One2many(comodel_name='device_manager.device_service',
                               inverse_name='device')
    state = fields.Selection(selection=(('online', 'Online'), 
                                        ('offline', 'Offline')),
                             default='offline')
    last_online = fields.Datetime()
    supervisor_version = fields.Char()
    ip_address = fields.Char(string='IP Address')
    notes = fields.Text()
    logs = fields.One2many(comodel_name='device_manager.device_log',
                           inverse_name='device')

    ports = fields.One2many(comodel_name='device_manager.device_port',
                            inverse_name='device')
    environment = fields.One2many(comodel_name='device_manager.device_environment',
                            inverse_name='device')
    mqtt_account = fields.Many2one('mosquitto.account', ondelete='restrict',
                                   required=True)
    user = fields.Many2one('res.users', ondelete='restrict', required=True)
    set_password = fields.Char()


    @api.model
    def create(self, vals):
        # Set partner name to UID
        pw = vals.get('set_password')
        if pw:
            # Add password fields for inherited mqtt.account
            vals['reset_password'] = pw
            # Set password for res.users
            vals['password'] = pw
            vals.pop('set_password') # Remove from fields
        # res.users fields
        vals['login'] = vals['uid']
        vals['name'] = vals['uid']
        vals['groups_id'] = [self.env.ref('device_manager.device_group').id]
        # mosquitto fields
        vals['username'] = vals['uid']        
        device = super(Device, self).create(vals)
        # Create ACL to make rpc requests
        self.env['mosquitto.acl'].sudo().create({
                              'username_id': device.mqtt_account.id,
                              'topic': 'rpc/+/{}'.format(device.uid),
                              'rw': '2'})
        # Read reply
        self.env['mosquitto.acl'].sudo().create({
                              'username_id': device.mqtt_account.id,
                              'topic': 'rpc/+/{}/reply'.format(device.uid),
                              'rw': '1'})
        # ACL for receiving RPC
        self.env['mosquitto.acl'].sudo().create({
                              'username_id': device.mqtt_account.id,
                              'topic': 'rpc/{}/+'.format(device.uid),
                              'rw': '1'})
        # Write a reply
        self.env['mosquitto.acl'].sudo().create({
                              'username_id': device.mqtt_account.id,
                              'topic': 'rpc/{}/+/reply'.format(device.uid),
                              'rw': '2'})
        # Will message published by broker on behalf of client
        self.env['mosquitto.acl'].sudo().create({
                              'username_id': device.mqtt_account.id,
                              'topic': 'will/{}'.format(device.uid),
                              'rw': '2'})
        return device


    @api.multi
    def write(self, vals):
        # Set partner name to UID
        pw = vals.get('set_password')
        if pw:
            # Add password fields for inherited res.user and mqtt.account
            vals['reset_password'] = pw
            # THIS DOES NOT WORK BUT IN create it DOES! WTF? vals['password'] = pw 
            vals.pop('set_password')
        res = super(Device, self).write(vals)
        if res and pw:
            self.user.sudo()._set_password(pw)
        return res


    @api.one
    def unlink(self):
        user = self.user
        partner = user.partner_id
        mqtt_account =self.mqtt_account
        super(Device, self).unlink()
        mqtt_account.unlink()
        user.unlink()
        partner.unlink()


    @api.model
    def register(self, app, config):
        device = self.env['device_manager.device'].sudo().create({
            'uid': config['uid'],
            'set_password': config['password'],
            'application': app.id,
            'state': 'online',
            'last_online': fields.Datetime.now(),
            'supervisor_version': config.get('version'),
        })
        logger.info(
            'Created device {} for app {}'.format(config['uid'], app.name))
        return device


    @api.one
    def application_restart(self, one_way=False):
        self.ensure_one()
        try:
            mqtt_rpc_bridge = MqttRpcBridge(self, one_way=one_way)
            result = mqtt_rpc_bridge.application_restart(dst=self.uid,
                                                    timeout=30, reload=True)
        except ConnectionError:
            raise Warning('Cannot connect to the bridge')
        except RPCError as e:
            raise Warning('{}'.format(e))



    @api.model
    def application_build(self, uid):
        device = self.env['device_manager.device'].sudo().search(
            [('uid', 'in', uid)])
        if not device:
            logger.warning('Device {} not found'.format(uid))
            return {}
        device.last_online = fields.Datetime.now()
        # Add services
        logger.debug('App services: {}'.format(
            [k.name for k in device.application.services]))
        device_services = self.env['device_manager.service'].sudo().search(
            [('id', 'in', [k.service.id for k in device.services])])
        logger.debug('Device services: {}'.format([k.name for k in device_services]))
        services_to_add = device.application.services - device_services
        logger.debug('Services to add: {}'.format([s.name for s in services_to_add]))
        device_env = {}
        for s in services_to_add:
            logger.info('Adding service {} to {}'.format(s.name, device.uid))
            d_s = self.env['device_manager.device_service'].sudo().create({
                    'service': s.id, 
                    'device': device.id,
                })
            # Copy application ports to device service ports
            for port in s.ports:
                self.env['device_manager.device_port'].sudo().create({
                    'device': device.id,
                    'device_port': port.port,
                    'host_port': port.port,
                    'protocol': port.protocol,
                })
        # Now delete removed services
        services_to_del = device_services - device.application.services
        logger.debug('Services to del: {}'.format([s.name for s in services_to_del]))
        for s in services_to_del:
            logger.info('Removing service {} from {}'.format(s.name, device.uid))
            d_s = self.env['device_manager.device_service'].sudo().search([
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
            'name': self.service.name,
            'image': {
                'name': '{}:{}'.format(self.service.image, self.service.tag),
                },
            'container': {
                'Env': ['{}={}'.format(k,v) for k,v in env.items()]
                },
            }
        # Set image repository authentication
        if self.service.auth_type == 'user_pass':
            config['image']['auth'] = {
                'username': self.service.auth_username,
                'password': self.service.auth_password,
            }
        elif self.service.auth_type == 'token':
            config['image']['auth'] = self.service.auth_token
        else:
            config['image']['auth'] = None
        # Set repository address if present
        if self.service.repository:
            config['image'].update({
                'repository': self.service.repository if \
                    self.service.repository.endswith('/') else \
                        self.service.repository + '/'
            })
        for p in self.device.ports:
            config['container'].update({
                'PortBindings': {
                    '{}/{}'.format(p.device_port, p.protocol): [
                        {"HostPort": "{}".format(p.host_port)}]}})
        if self.service.cmd:
            config['container'].update({'Cmd': json.loads(self.service.cmd)})
        return config

    @api.one
    def status_get(self):
        self.ensure_one()
        try:
            mqtt_rpc_bridge = MqttRpcBridge(self)
            self.status = mqtt_rpc_bridge.service_status(dst=self.device.uid,
                                                     timeout=2,
                                                     service_id=self.service.id)
        except (RPCError, ConnectionError):
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

