import os
import pytest
from supervisor import Supervisor

CONTAINER_ID = os.environ.get('CONTAINER_ID')

test_app = {
    'services': {
        '1': {
            'id': 1,
            'name': 'busybox',
            'image': {
                'name': 'busybox:latest',
            },
            'container': {
                'Image': 'busybox:latest',
                'Cmd': '["echo", "hello"]',
                'Environment': [],
            },            
            'container_id': CONTAINER_ID,
        },
        '2': {
            'image': {
                'name': 'nginx:latest',
                'repository': 'registry.hub.docker.com/library/'
            },
            'id': 2,
            'container': {
                'Image': 'nginx:latest',
                'Env': ['GW_REGION=EU', 'GW_CONTACT_EMAIL=test@mail.com',
                        'GW_TYPE=rpi']},
            'name': 'nginx'
        }
    }
}


@pytest.mark.asyncio
async def test_service_restart(event_loop):
    s = Supervisor(loop=event_loop)
    s.application = test_app
    await s.service_start(service_id=2)
    res = await s.service_restart(service_id=2)    
    await s.stop()
    assert res


@pytest.mark.asyncio
async def test_service_start(event_loop):
    s = Supervisor(loop=event_loop)
    s.application = test_app
    res = await s.service_start(service_id=2)
    assert res
    await s.stop()


@pytest.mark.asyncio
async def test_service_stop(event_loop):
    s = Supervisor(loop=event_loop)
    s.application = test_app
    res = await s.service_stop(service_id=2)
    assert res
    await s.stop()


@pytest.mark.asyncio
async def test_service_status(event_loop):
    s = Supervisor(loop=event_loop)
    s.application = test_app
    res = await s.service_status(service_id=1)
    assert res == 'starting'
    await s.stop()


@pytest.mark.asyncio
async def test_register(event_loop):
    s = Supervisor(loop=event_loop)
    res = await s.device_register()
    assert res == True
    await s.stop()


@pytest.mark.asyncio
async def test_settings_load(event_loop):
    s = Supervisor(loop=event_loop)
    res = await s.settings_load()
    assert res == True
    await s.stop()


@pytest.mark.asyncio
async def test_settings_save(event_loop):
    s = Supervisor(loop=event_loop)
    res = await s.settings_save()
    assert res == True
    await s.stop()


@pytest.mark.asyncio
async def test_ip_address_get(event_loop):
    s = Supervisor(loop=event_loop)
    res = await s.ip_address_get()
    assert res
    await s.stop()
