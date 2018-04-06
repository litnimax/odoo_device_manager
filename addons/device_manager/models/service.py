import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError

logger = logging.getLogger(__name__)


class Service(models.Model):
    _name = 'device_manager.service'

    name = fields.Char(required=True)
    image = fields.Char(required=True)    
    tag = fields.Char(required=True, default='latest')
    repository = fields.Char()
    auth_type = fields.Selection(selection=(('none', 'None'),
                                            ('user_pass', 'User/Pass'),
                                            ('token', 'Token')),
                                default='none')
    auth_username = fields.Char(string='Username')
    auth_password = fields.Char(string='Password')
    auth_token = fields.Char(string='Token')
    depends_on = fields.Many2many(comodel_name='device_manager.service',
                                  relation='device_manager_service_depends',
                                  column1='service1', column2='service2')
    environment = fields.Many2many(
                            comodel_name='device_manager.service_environment')
    restart = fields.Selection(selection=(
        ('no', 'No'), ('always', 'Always'),
        ('on-failure', 'On Failure'),
        ('unless-stopped', 'Unless-stopped')),
        default='on-failure')
    cmd = fields.Char(string='Command')
    devices = fields.One2many(comodel_name='device_manager.device_service',
                              inverse_name='service')
    applications = fields.Many2many(comodel_name='device_manager.application')
    applications_count = fields.Integer(compute='_get_applications_count',
                                        string='Applications')
    device_count = fields.Integer(compute='_get_device_count', string="Devices")
    ports = fields.One2many(comodel_name='device_manager.service_port',
                            inverse_name='service')

    @api.one
    def _get_device_count(self):
        self.device_count = self.env[
            'device_manager.device_service'].search_count(
            [('service', '=', self.id)])

    @api.one
    def _get_applications_count(self):
        self.applications_count = self.env[
            'device_manager.application'].search_count(
            [('services', '=', self.id)])


    @api.constrains('cmd')
    def _check_cmd(self):
        if self.cmd:
            try:
                json.loads(self.cmd)
            except Exception as e:
                raise ValidationError(_('Cmd must be a json string!'))


    @api.multi
    def write(self, vals):
        res = super(Service, self).write(vals)
        if res:
            for self in self:
                try:
                    for d_s in self.devices:
                        d_s.device.application_restart(one_way=True)
                except Exception as e:
                    logger.exception(e)
        return res



class ServicePort(models.Model):
    _name = 'device_manager.service_port'
    _order = 'port'

    service = fields.Many2one(comodel_name='device_manager.service',
                              required=True, ondelete='cascade')
    port = fields.Integer(required=True, help="Port on docker container")
    protocol = fields.Selection(selection=(('udp', 'UDP'), ('tcp', 'TCP')),
                                default='tcp', required=True)



class ServiceEnvironment(models.Model):
    _name = 'device_manager.service_environment'
    _order = 'name'

    name = fields.Char(required=True)
    value = fields.Char()
    services = fields.Many2many('device_manager.service')


    @api.multi
    def write(self, vals):
        res = super(ServiceEnvironment, self).write(vals)
        if res:
            for self in self:
                if self.services:
                    for service in self.services:
                        for device_service in service.devices:
                            device_service.device.application_restart(
                                                                one_way=True)
        return res

