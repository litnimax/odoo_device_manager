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
        token = http.request.jsonrequest.get('token')
        device_uid = http.request.jsonrequest.get('device_uid')
        app = http.request.env['device_manager.application'].sudo().search(
                                            [('token','=', token)])
        if not app:
            raise Warning('Application token not found')
        # Now check if the device is already registered
        device = http.request.env['device_manager.device'].sudo().search(
            [('device_uid','=',device_uid)])
        if device:
            # Check application
            if device.application.id != app.id:
                logger.warning('Device {} already registered with app {}'.format(
                    device_uid, device.application.name))
                raise Warning('Device {} already registered to app {}'.format(
                    device_uid, device.application.name))
            else:
                device.last_online = fields.Datetime.now()
                logger.debug(
                    'Device {} is already registered'.format(device_uid))
        else:
            # Create new device
            device = http.request.env['device_manager.device'].sudo().create({
                'device_uid': device_uid,
                'application': app.id,
                'username': device_uid,
                'state': 'online',
                'password': 'todo_gen_pass',
                'last_online': fields.Datetime.now(),
                'supervisor_version': http.request.jsonrequest.get('version'),
            })
            logger.info(
                'Created device {} for app {}'.format(device_uid, app.name))
        
        return {
            'device_id': device.id,
            'username': device.username,
            'password': device.password
        }

