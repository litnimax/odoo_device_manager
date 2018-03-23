import asyncio
from concurrent.futures import ThreadPoolExecutor
import tempfile
import os
import pytest
import json
from mqttrpc_supervisor import Supervisor


@pytest.mark.asyncio
async def test_build_agent(event_loop):
    s = Supervisor(loop=event_loop)
    res = await s.build_agent(image_name='busybox')
    assert res == True

