import logging
from odoo.modules.registry import RegistryManager
from odoo.api import Environment, SUPERUSER_ID
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.transports.http import HttpPostClientTransport
from tinyrpc.exc import RPCError
from tinyrpc import RPCClient

logger = logging.getLogger(__name__)

class MqttRpcBridge(object):
    def __init__(self, obj, one_way=False):
        url = obj.env['device_manager.settings']._get_param(
                                                    'mqtt_rpc_bridge_url')
        logger.debug('HTTP bridge url {}'.format(url))
        rpc_client = RPCClient(
            JSONRPCProtocol(),
            HttpPostClientTransport(url)
        )
        self.proxy = rpc_client.get_proxy(one_way=one_way)


    def __getattr__(self, name):
        return getattr(self.proxy, name)

