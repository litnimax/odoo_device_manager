import asyncio
from concurrent.futures import ThreadPoolExecutor
import tempfile
import os
import pytest
import json
from supervisor import Supervisor


@pytest.mark.asyncio
async def test_build_agent(event_loop):
    s = Supervisor(loop=event_loop)
    res = await s.build_agent(image_name='busybox')
    assert res == True
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
