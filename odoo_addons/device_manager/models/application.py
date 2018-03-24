import logging
from odoo import models, fields, api
from odoo.exceptions import Warning
from jinja2 import Environment

logger = logging.getLogger(__name__)

class Application(models.Model):
    _name = 'device_manager.application'

    name = fields.Char(required=True)
    token = fields.Char(required=True)
    services = fields.Many2many(comodel_name='device_manager.service')

    @api.one
    def build(self):
        self.ensure_one()
        result = {'services': {}}
        service = self.services[0]
        for service in self.services:
            result['services'][service.name] = {
                'image': service.image,
                'tag': service.tag,
                'environment': [(v.name, v.value) for v in service.environment],
            }
        return result


    @api.model
    def get_application_for_device(self, device_uid):
        device = self.env['device_manager.device'].search(
                                        [('device_uid','in', device_uid)])
        return device.application.build()
