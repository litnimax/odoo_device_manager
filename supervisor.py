#!/usr/bin/env python3
import aiofiles
import aiohttp
import asyncio
import aiodocker
import json
import logging
import os
import sys
from aiodocker import Docker
from mqttrpc import MQTTRPC, OdooRPCProxy, dispatcher
from tinyrpc.exc import RPCError

logger = logging.getLogger(__name__)
logging.getLogger('aiohttp-json-rpc.client').setLevel(level=logging.DEBUG)

ODOO_DB = 'test'
ODOO_USERNAME = 'admin'
ODOO_PASSWORD = 'admin'
REGISTER_HOST = 'localhost'
REGISTER_PORT = 8069
REGISTER_URL = 'http://localhost:8069/device_manager/register?db=test'
REGISTER_TOKEN = 'test'

class Supervisor(MQTTRPC):
    version = '1.0.0'
    settings = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.odoo = OdooRPCProxy(self, 'odoo')


    async def start(self):
        logger.info('Start')
        await self.settings_load()
        if not self.settings:
            # Empty settings, try to register
            if  not await self.register():
                logger.error('Cannot register device')
                await self.stop()
        #uid = await self.odoo.login(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)


    # === Agent exit ===
    async def stop(self):
        """
        We have to cancel all pending coroutines for clean exit.
        """
        await super().stop()
        logger.info('Stopped')
        sys.exit(0)



    async def register(self):
        logger.info('Register')
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    REGISTER_URL, json={
                        'version': self.version,
                        'token': REGISTER_TOKEN,
                        'device_uid': self.client_uid}) as resp:
                logger.debug('Register response status {}'.format(resp.status))
                data = await resp.json()
                if 'error' in data:
                    logger.error('Register error {}: {}'.format(
                            data['error']['message'], data['error']['data']))
                    return False
                else:
                    logger.debug('Register reponse {}'.format(data))
                    self.settings['username'] = data['result']['username']
                    self.settings['password'] = data['result']['password']
                    await self.settings_save()
                    return True


    async def settings_load(self):
        logger.debug('Load settings')
        try:
            async with aiofiles.open(
                            os.path.join(
                                os.path.dirname(__file__),
                                'settings.json')) as file:
                settings = json.loads(await file.read())
                logger.debug('Loaded {}'.format(settings))
                self.settings = settings.copy()
                return True
        except FileNotFoundError:
            logger.info('settings.json not found')



    async def settings_save(self):
        logger.debug('Save settings')
        async with aiofiles.open(
                        os.path.join(
                            os.path.dirname(__file__),
                            'settings.json'), 'w') as file:
            await file.write(json.dumps(self.settings))
            return True


    @dispatcher.public
    async def build_agent(self, image_name, version='latest'):
        docker = Docker()        
        image = await docker.images.pull(from_image=image_name, tag=version)
        print (dir(image))
        container = await docker.containers.create_or_replace(name='agent', config={
            'Image': '{}:{}'.format(image_name, version),
            'Command': ['ls /etc']
        })
        await container.start()
        logs = await container.log(stdout=True)
        print(''.join(logs))
        print(dir(container))
        await docker.close()
        return True



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('hbmqtt').setLevel(level=logging.ERROR)    
    loop = asyncio.get_event_loop()
    s = Supervisor(loop=loop)
    loop.create_task(s.process_messages())
    loop.run_until_complete(s.start())
