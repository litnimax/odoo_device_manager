from odoo import models, fields, api

class SysStats(model.Model):

    metric = fields.Char(required=True)
