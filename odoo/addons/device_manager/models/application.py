import collections
import logging
import uuid
from odoo import models, fields, api
from odoo.exceptions import Warning

logger = logging.getLogger(__name__)

class Application(models.Model):
    _name = 'device_manager.application'

    name = fields.Char(required=True)
    token = fields.Char(required=True, default=lambda self: self.generate_token())
    services = fields.Many2many(comodel_name='device_manager.service')


    def generate_token(self):
        return uuid.uuid4().hex


    @api.model
    def get_application_for_device(self, uid):
        device = self.env['device_manager.device'].search(
                                        [('uid','in', uid)])
        if not device:
            logger.warning('Device {} not found'.format(uid))
            return {}
        device.last_online = fields.Datetime.now()        
        # Add services
        service_tupple = collections.namedtuple('Service', ['service_id', 'name'])
        app_services = set([service_tupple(k.id, k.name) for k in device.application.services])
        logger.debug('App services: {}'.format(app_services))        
        device_services = set([service_tupple(
                    k.service.id, k.service_name) for k in device.services])
        logger.debug('Device services: {}'.format(device_services))
        services_to_add = app_services - device_services
        logger.debug('Services to add: {}'.format([s.name for s in services_to_add]))
        for s in services_to_add:
            logger.info('Adding service {} to {}'.format(s.name, device.uid))
            self.env['device_manager.device_service'].create({
                    'service': s.service_id, 
                    'device': device.id,
                })
        # Now delete removed services
        services_to_del = device_services - app_services
        logger.debug('Services to del: {}'.format([s.name for s in services_to_del]))
        for s in services_to_del:
            logger.info('Removing service {} from {}'.format(s.name, device.uid))
            d_s = self.env['device_manager.device_service'].search([
                ('device','=', device.id),('service','=', s.service_id)])
            d_s.unlink()
        # Prepare the result dict
        result = {'services': {}}
        for dev_service in device.services:
            result['services'][
                dev_service.service.id] = dev_service.service.get_service()[0]
        return result
