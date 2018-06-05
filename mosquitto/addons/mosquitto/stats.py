from odoo import models, fields, api

class SysStats(models.Model):
    _name = 'mosquitto.sys_stats'

    metric = fields.Char(required=True)
