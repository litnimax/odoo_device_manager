import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, Warning


logger = logging.getLogger(__name__)

PARAMS = ['mqtt_url', 'mqtt_rpc_bridge_url']

class DeviceManagerSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'device_manager.settings'


    mqtt_url = fields.Char(required=True, string='MQTT URL')
    mqtt_rpc_bridge_url = fields.Char(required=True,
                                      string='MQTT RPC Bridge URL')

    def set_params(self):
        for field_name in PARAMS:
            value = getattr(self, field_name, '')
            self.env['ir.config_parameter'].set_param(
                'device_manager.' + field_name, value)


    def get_default_params(self, fields):
        res = {}
        for field_name in PARAMS:
            res[field_name] = self.env[
                'ir.config_parameter'].get_param(
                    'device_manager.' + field_name, '')
        return res


    @api.model
    def _get_param(self, param):
        param = 'device_manager.' + param
        result = self.env['ir.config_parameter'].get_param(param)
        logger.debug('Param {} = {}'.format(param, result))
        return result


    @api.model
    def _set_param(self, param, value):
        # set_ method are deprecated and all wrapped to set_values so we use _set_
        return self.env['ir.config_parameter'].set_param(
                'device_manager.' + param, value)

