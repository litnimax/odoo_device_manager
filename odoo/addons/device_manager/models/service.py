import logging
from odoo import models, fields, api
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


class Service(models.Model):
    _name = 'device_manager.service'

    name = fields.Char(required=True)
    image = fields.Char(required=True)
    tag = fields.Char(required=True, default='latest')
    depends_on = fields.Many2many(comodel_name='device_manager.service',
                                  relation='device_manager_service_depends',
                                  column1='service1', column2='service2')
    environment = fields.Many2many(comodel_name='device_manager.variable')
    restart = fields.Selection(selection=(
                                        ('no', 'No'), ('always', 'Always'),
                                        ('on-failure', 'On Failure'),
                                        ('unless-stopped', 'Unless-stopped')),
                                default='on-failure')
    cmd = fields.Char(string='Command')
    devices = fields.One2many(comodel_name='device_manager.device_service',
                              inverse_name='service')
    device_count = fields.Integer(compute='_get_device_count', string="Devices")
    ports = fields.Char()


    @api.one
    def _get_device_count(self):
        self.device_count = self.env[
            'device_manager.device_service'].search_count(
                [('service', '=', self.id)])


    @api.one
    def get_service(self):
        service = self
        config = {
            'id': service.id,
            'Name': service.name,
            'Image': '{}:{}'.format(service.image, service.tag),
            'Env': ['{}={}'.format(v.name, v.value) for v in service.environment],
            #'PortBindings': [{'{}/tcp'.format(p):[{ "HostPort": "{}".format(p) }] } for p in ports]
        }
        if service.cmd:
            config.update({'Cmd': service.cmd})
        return config
