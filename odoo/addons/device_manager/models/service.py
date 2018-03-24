import logging
from odoo import models, fields, api

logger = logging.getLogger(__name__)


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

