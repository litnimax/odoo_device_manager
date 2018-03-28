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

    def generate_token(self):
        return uuid.uuid4().hex

