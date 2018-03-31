# -*- coding: utf-8 -*-

from odoo import models, fields


class Image(models.Model):
    _name = 'device_manager.image'

    name = fields.Char()
