import logging
from odoo import models, fields, api
from odoo.exceptions import Warning
from requests import ConnectionError
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.transports.http import HttpPostClientTransport
from tinyrpc import RPCClient


logger = logging.getLogger(__name__)

rpc_client = RPCClient(
    JSONRPCProtocol(),
    HttpPostClientTransport('http://http_bridge:8888')
)
http_bridge = rpc_client.get_proxy()


class Device(models.Model):
    _name = 'device_manager.device'
    _rec_name = 'device_uid'

    device_uid = fields.Char(required=True, index=True, string="Device UID")
    application = fields.Many2one(comodel_name='device_manager.application')
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
            result = http_bridge.application_start(dst=self.device_uid)
        except ConnectionError:
            raise Warning('Cannot connect to the bridge')
        

class DeviceLog(models.Model):
    _name = 'device_manager.device_log'

    device = fields.Many2one(comodel_name='device_manager.device')
    log = fields.Char()

