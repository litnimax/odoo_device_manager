# -*- coding: utf-8 -*-

from odoo import models, fields, api



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




class Device(models.Model):
    _name = 'device_manager.device'
    _rec_name = 'device_uid'

    device_uid = fields.Char(required=True, index=True, string="Device UID")
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
    ip_address = fields.Char(string='IP Address')
    commit = fields.Char()
    variables = fields.Many2many(comodel_name='device_manager.variable')
    notes = fields.Text()



class Variable(models.Model):
    _name = 'device_manager.variable'

    name = fields.Char(required=True)
    value = fields.Char()


class Image(models.Model):
     _name = 'device_manager.image'

     name = fields.Char()


