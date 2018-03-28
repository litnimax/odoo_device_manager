import asyncio
from concurrent.futures import ThreadPoolExecutor
import tempfile
import os
import pytest
import json
from supervisor import Supervisor

CONTAINER_ID = os.environ.get('CONTAINER_ID')

test_app = {
    'services': {
        '1': {
            'Name': 'busybox',
            'Image': 'busybox',
            'Cmd': '["echo", "hello"]',
            'Environment': [],
            'Tag': 'latest',
            'id': 1,
            'container_id': CONTAINER_ID,
        }
    }
}

@pytest.mark.asyncio
async def test_service_status(event_loop):
    s = Supervisor(loop=event_loop)
    s.application = test_app
    res = await s.service_status(service_id=1)
    assert res == 'starting'
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
