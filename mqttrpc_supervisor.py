#!/usr/bin/env python3
import asyncio
import aiodocker
import json
import logging
import os
import sys
from aiodocker import Docker
from mqttrpc import MQTTRPC, OdooRPCProxy, dispatcher
from tinyrpc.exc import RPCError

ODOO_DB = 'test'
ODOO_USERNAME = 'admin'
ODOO_PASSWORD = 'admin'

class Supervisor(MQTTRPC):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.odoo = OdooRPCProxy(self, 'odoo')


    async def start(self):
        uid = await self.odoo.login(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)


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
        return True



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('hbmqtt').setLevel(level=logging.ERROR)    
    loop = asyncio.get_event_loop()
    s = Supervisor(loop=loop)
    loop.create_task(s.process_messages())
    loop.run_until_complete(s.start())
