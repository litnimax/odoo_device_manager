import logging
from odoo import models, fields, api, _
from odoo.exceptions import Warning
from requests import ConnectionError
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.transports.http import HttpPostClientTransport
from tinyrpc.exc import  RPCError
from tinyrpc import RPCClient


logger = logging.getLogger(__name__)

rpc_client = RPCClient(
    JSONRPCProtocol(),
    HttpPostClientTransport('http://http_bridge:8888')
)
http_bridge = rpc_client.get_proxy()


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
    variables = fields.Many2many(comodel_name='device_manager.variable')
    notes = fields.Text()
    logs = fields.One2many(comodel_name='device_manager.device_log',
                           inverse_name='device')

    @api.one
    def application_start(self):
        self.ensure_one()
        try:
            result = http_bridge.application_start(dst=self.uid,
                                                   timeout=30, reload=True)
        except ConnectionError:
            raise Warning('Cannot connect to the bridge')
        except RPCError as e:
            raise Warning('{}'.format(e))
        

class DeviceService(models.Model):
    _name = 'device_manager.device_service'

    device = fields.Many2one(comodel_name='device_manager.device')
    service = fields.Many2one(comodel_name='device_manager.service')
    service_name = fields.Char(related='service.name', readonly=True)
    status = fields.Char(#selection=(
                              #          ('created','Created'),
                              #          ('restarting', 'Restarting'),
                              #          ('running', 'Running'),
                              #          ('removing', 'removing'),
                              #          ('paused', 'paused'),
                              #          ('exited', 'exited'),
                              #          ('dead', 'dead')))
                              compute='status_get')

    _sql_constraints = [
        (
            'uniq',
            'UNIQUE(device,service)',
            _(u'This device already has this service!')
        )
    ]

    @api.one
    def status_get(self):
        self.ensure_one()
        try:
            self.status = http_bridge.service_status(dst=self.device.uid,
                                                     service_id=self.service.id)
        except RPCError:
            self.status = 'error'

    @api.one
    def start(self):
        try:
            http_bridge.service_start(dst=self.device.uid, timeout=30,
                                      service_id=self.service.id)
        except RPCError as e:
            raise Warning(str(e))

    @api.one
    def stop(self):
        try:
            http_bridge.service_stop(dst=self.device.uid, timeout=30,
                                      service_id=self.service.id)
        except RPCError as e:
            raise Warning(str(e))

    @api.one
    def restart(self):
        try:
            http_bridge.service_restart(dst=self.device.uid, timeout=60,
                                      service_id=self.service.id)
        except RPCError as e:
            raise Warning(str(e))

class DeviceLog(models.Model):
    _name = 'device_manager.device_log'
    _order = 'create_date desc'

    device = fields.Many2one(comodel_name='device_manager.device')
    log = fields.Char()

