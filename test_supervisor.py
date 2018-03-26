import asyncio
from concurrent.futures import ThreadPoolExecutor
import tempfile
import os
import pytest
import json
from supervisor import Supervisor

test_app = {
    'services': {
        '1': {
            'name': 'busybox',
            'image': 'busybox',
            'cmd': '["echo", "hello"]',
            'environment': [],
            'tag': 'latest',
            'id': 1,
            'container_id': 'fa86df75d855fd99a0dd504552c343791decb10b20186c63132dd6a2d6ad6344',
        }
    }
}

@pytest.mark.asyncio
async def test_service_status(event_loop):
    s = Supervisor(loop=event_loop)
    s.application = test_app
    res = await s.service_status(service_id=1)
    assert res == 'exited'
    await s.stop()


@pytest.mark.asyncio
async def test_settings_save(event_loop):
    s = Supervisor(loop=event_loop)
    res = await s.settings_save()
    assert res == True
    await s.stop()


@pytest.mark.asyncio
async def test_settings_load(event_loop):
    s = Supervisor(loop=event_loop)
    res = await s.settings_load()
    assert res == True
    await s.stop()


@pytest.mark.asyncio
async def test_register(event_loop):
    s = Supervisor(loop=event_loop)
    res = await s.register()
    assert res == True
    await s.stop()
