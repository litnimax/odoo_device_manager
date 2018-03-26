#!/usr/bin/env python3
import aiojobs
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
LOG_INTERVAL = 1 # Every seconds lookup logs and send to the cloud

class Supervisor(MQTTRPC):
    version = '1.0.0'
    settings = {}
    application = {}
    scheduler = None

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
        # Run docker containers logger
        self.scheduler = await aiojobs.create_scheduler()        
        #await self.scheduler.spawn(self.services_log())


    async def services_log(self):
        docker = Docker()
        try:
            for service_id, service in self.application['services'].items():
                container = await docker.containers.get(service['container_id'])
                logs = await container.log(stdout=True)
                await self.device_log('\n'.join(logs))

        except Exception as e:
            logger.exception(e)

        finally:
            await docker.close()

        await asyncio.sleep(LOG_INTERVAL)
        await self.scheduler.spawn(self.services_log())


    @dispatcher.public
    async def service_restart(self, service_id=None):
        if await self.service_status_(service_id) == 'running':
            await self.service_stop_(service_id)
            await self.service_start_(service_id)
            return True
        else:
            return False


    @dispatcher.public
    async def service_start(self, service_id=None):
        if await self.service_status_(service_id) == 'running':
            return True
        else:
            return await self.service_start_(service_id)


    async def service_start_(self, service_id):
        service_id = str(service_id)
        docker = Docker()        
        try:
            service = self.application['services'][service_id]
            logger.debug('Start service: {}'.format(service['name']))
            container = await docker.containers.get(
                self.application['services'][service_id]['container_id'])
            await container.start()
            #logs = await container.log(stdout=True)
            #await self.device_log('\n'.join(logs))            
            return True
        except IndexError as e:
            logger.exception(e) # See error locally
            raise # Return back RPC error
        finally:
            await docker.close()


    @dispatcher.public
    async def service_stop(self, service_id=None):
        if await self.service_status_(service_id) != 'running':
            return True
        else:
            return await self.service_stop_(service_id)


    async def service_stop_(self, service_id):
        service_id = str(service_id)
        docker = Docker()        
        try:
            service = self.application['services'][service_id]
            logger.debug('Stop service: {}'.format(service['name']))
            container = await docker.containers.get(
                self.application['services'][service_id]['container_id'])
            await container.stop()
            #logs = await container.log(stdout=True)
            #await self.device_log('\n'.join(logs))            
            return True
        except IndexError as e:
            logger.exception(e) # See error locally
            raise # Return back RPC error
        finally:
            await docker.close()



    @dispatcher.public
    async def service_status(self, service_id=None):
        return await self.service_status_(service_id)


    async def service_status_(self, service_id):
        service_id = str(service_id) # JSON keys are always strings
        docker = Docker()
        begin = self.loop.time()
        try:
            logger.debug('Service status for {}'.format(
                self.application['services'][service_id]['name']))
            container = await docker.containers.get(
                    self.application['services'][service_id]['container_id'])
            data = await container.show()
            logger.debug('Service status took {}'.format(
                                                self.loop.time() - begin))
            return data['State']['Status']
        except IndexError:
            raise RPCError('Service not found')
        finally:
            await docker.close()



    async def application_load(self):
        application = await self.odoo.execute(
                                            'device_manager.application',
                                            'get_application_for_device', self.client_uid)
        logger.debug('Application: {}'.format(application))
        if not application:
            logger.error('Application is not set')
        else:
            logger.info('Application with {} service(s) loaded'.format(
                                        len(application['services'])))
            self.application = application
            return True


    @dispatcher.public
    async def application_start(self, reload=False):
        if reload:
            await self.application_load()
        await self._application_start()
        return True
        

    async def _application_start(self):
        docker = Docker()
        try:        
            for service_id, service in self.application['services'].items():
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
                self.application['services'][service_id][
                                        'container_id'] = container._id
                #logs = await container.log(stdout=True)
                #await self.device_log('\n'.join(logs))
                # TODO: cleanup deleted services
            return True

        except (DockerError, ValueError) as e:
            await self.device_log('{}'.format(e))

        except Exception as e:
            logger.exception(e)
            await self.device_log('{}'.format(e))

        finally:
            await docker.close()


    async def device_log(self, log):
        logger.debug('Device log: {}'.format(log))
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
        logger.info('Stopping')
        await super().stop()        
        sys.exit()



    async def register(self):
        logger.info('Register')
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    REGISTER_URL, json={
                        'version': self.version,
                        'token': REGISTER_TOKEN,
                        'uid': self.client_uid}) as resp:
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
    try:
        loop.run_forever()
    except SystemExit:
        pass
    finally:
        logger.info('Stopped')
        loop.stop()
