from odoo import models, fields, api


class res_users(models.Model):
    _inherit = 'res.users'

    device = fields.One2many(comodel_name='device_manager.device',
                             inverse_name='user')

