#!/usr/bin/env python3
import aiofiles
import aiohttp
import asyncio
import aiodocker
from aiodocker.exceptions import DockerError
import json
import logging
import os
import sys
import yaml
from aiodocker import Docker
from mqttrpc import MQTTRPC, OdooRPCProxy, dispatcher
from tinyrpc.exc import RPCError


logger = logging.getLogger(__name__)
logging.getLogger('aiohttp-json-rpc.client').setLevel(level=logging.DEBUG)

REGISTER_URL = 'http://localhost:8069/device_manager/register?db=test'
REGISTER_TOKEN = 'test'
ODOO_DB = 'test'

class Supervisor(MQTTRPC):
    version = '1.0.0'
    settings = {}
    application = {}

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
        # Init odoo connector
        try:
            uid = await self.odoo.login(ODOO_DB, 'admin', 'admin') #self.settings['username'],
                                                 #self.settings['password'])
            if await self.application_load():
                await self._application_start()                
        except RPCError as e:
            logger.error(e)


    async def application_load(self):
        application = await self.odoo.execute(
                                            'device_manager.application',
                                            'get_application_for_device', self.client_uid)
        logger.debug(application)
        if not application:
            logger.error('Application is not set')
        else:
            logger.info('Application with {} service(s) loaded'.format(
                                        len(application[0]['services'])))
            self.application = application[0]
            return True


    @dispatcher.public
    def application_start(self):
        t = self.loop.create_task(self._application_start())
        return 'Started'
        #done, _ = asyncio.wait([t])
        #for t in done:
        #    print (t.result())


    async def _application_start(self):
        docker = Docker()
        try:
            for service in self.application['services']:            
                image = await docker.images.pull(from_image=service['image'],
                                                 tag=service['tag'])
                config = {
                    'Image': '{}:{}'.format(service['image'], service['tag']),                
                }
                if service['cmd']:
                    json_cmd = json.loads(service['cmd'])
                    config.update({'Cmd': json_cmd})
                container = await docker.containers.create_or_replace(
                                name=service['name'], config=config)
                await container.start()
                logs = await container.log(stdout=True)
                await self.device_log('\n'.join(logs))
            return True

        except (DockerError, ValueError) as e:
            await self.device_log('{}'.format(e))

        except Exception as e:
            logger.exception(e)
            await self.device_log('{}'.format(e))

        finally:
            await docker.close()


    async def device_log(self, log):
        if not log:
            return
        await self.odoo.create('device_manager.device_log', {
            'device': self.settings['device_id'],
            'log': log,
        })


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
                    self.settings = data['result']
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



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('hbmqtt').setLevel(level=logging.ERROR)    
    loop = asyncio.get_event_loop()
    s = Supervisor(loop=loop)
    loop.create_task(s.process_messages())
    loop.create_task(s.start())
    loop.run_forever()
