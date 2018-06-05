from odoo import models, fields, api

class SysStats(models.Model):

    metric = fields.Char(required=True)
