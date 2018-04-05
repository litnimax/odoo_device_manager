# -*- coding: utf-8 -*-
import json
import logging
from odoo import http, fields
from odoo.exceptions import Warning
from werkzeug.exceptions import NotFound
import sys

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Container(http.Controller):
     @http.route('/device_manager/register', auth='public', type='json')
     def register(self):
        uid = http.request.jsonrequest.get('uid')
        pw = http.request.jsonrequest.get('password')
        # Check if the device is already registered
        device = http.request.env['device_manager.device'].sudo().search(
            [('uid','=',uid)])
        if device:
            logger.debug('Device already registered')
            device.last_online = fields.Datetime.now()
            if pw:
                #Reset device password
                device.set_password = pw
                logger.info('Device {} password reset'.format(uid))
        else:
            # Device not found, try token registration
            token = http.request.jsonrequest.get('token')        
            app = http.request.env['device_manager.application'].sudo().search(
                                                [('token','=', token)])
            if not app:
                raise Warning('Application token not found')
            device = http.request.env['device_manager.device'].register(app,
                                                    http.request.jsonrequest)
                                                    
        mqtt_host = http.request.env[
                        'device_manager.settings']._get_param('mqtt_host')
        mqtt_port = http.request.env[
                        'device_manager.settings']._get_param('mqtt_port')
        cafile = http.request.env[
                        'device_manager.settings']._get_param('cafile')
        capath = http.request.env[
                        'device_manager.settings']._get_param('capath')
        cadata = http.request.env[
                        'device_manager.settings']._get_param('cadata')
        mqtt_scheme = 'mqtts' if cafile or capath or cadata else 'mqtt'
        if int(mqtt_port):
            mqtt_host = '{}:{}'.format(mqtt_host, mqtt_port)

        return {
            'broker' : {
                'uri' : '{}://{}:{}@{}'.format(mqtt_scheme, device.username,
                                                pw, mqtt_host),
                'cafile' : cafile,
                'cadata' : cadata,
                'capath' : capath
            },
            'device_id': device.id,
        }

