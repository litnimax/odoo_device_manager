# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Variable(models.Model):
    _name = 'device_manager.variable'
    _order = 'name'

    name = fields.Char(required=True)
    value = fields.Char()


class Image(models.Model):
     _name = 'device_manager.image'

     name = fields.Char()


