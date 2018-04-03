import collections
import logging
import uuid
from odoo import models, fields, api
from odoo.exceptions import Warning

logger = logging.getLogger(__name__)


class Application(models.Model):
    _name = 'device_manager.application'

    name = fields.Char(required=True)
    token = fields.Char(required=True, default=lambda self: self.generate_token())
    services = fields.Many2many(comodel_name='device_manager.service')
    devices = fields.One2many(comodel_name='device_manager.device',
                              inverse_name='application')


    def generate_token(self):
        return uuid.uuid4().hex


    @api.multi
    def write(self, vals):
        if 'services' in vals:        
            for self in self:
                super(Application, self).write(vals)
                for device in self.devices:
                    device.application_restart()
        return True