# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Application(models.Model):
    _name = 'device_manager.application'

    name = fields.Char(required=True)
    token = fields.Char(required=True)



class Image(models.Model):
     _name = 'device_manager.image'

     name = fields.Char()


class Device(models.Model):
    _name = 'device_manager.device'
    _rec_name = 'device_uid'

    device_uid = fields.Char(required=True, index=True)
    application = fields.Many2one(comodel_name='device_manager.application')
    state = fields.Selection(selection=(
                                         ('online', 'Online'),
                                         ('offline', 'Offline'))
    )
    username = fields.Char()
    password = fields.Char()
    last_online = fields.Datetime()
    host_os_version = fields.Char()
    supervisor_version = fields.Char()
    ip_address = fields.Char()
    commit = fields.Char()
    variables = fields.Many2many(comodel_name='device_manager.variable')
    notes = fields.Text()


class Service(models.Model):
    _name = 'device_manager.service'

    name = fields.Char(required=True)
    status = fields.Selection(selection=(
                                         ('downloaded', 'Downloaded'),
                                         ('building', 'Building'))
    )


class Variable(models.Model):
    _name = 'device_manager.variable'

    name = fields.Char(required=True)
    value = fields.Char()

