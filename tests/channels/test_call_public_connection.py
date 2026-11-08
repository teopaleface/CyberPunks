"""Synthetic network failures reproducing the physical call's HTTP 530."""
import asyncio

import httpx
import pytest

from cyberpunks.channels.models import ChannelError
from cyberpunks.channels.whatsapp_calls import verify_public_tool


@pytest.mark.parametrize("status", [530, 502, 404])
def test_dead_public_path_fails_even_when_sip_configuration_is_valid(status):
    with pytest.raises(ChannelError, match="public call-tool connection"):
        asyncio.run(verify_public_tool("https://synthetic.example", transport=httpx.MockTransport(lambda r: httpx.Response(status))))

def test_checks_service_identity_and_actual_auth_boundary():
    paths=[]
    def handle(request):
        paths.append(request.url.path)
        return httpx.Response(200,json={"service":"daybreak-whatsapp-call-tool"}) if request.url.path=="/healthz" else httpx.Response(401)
    asyncio.run(verify_public_tool("https://synthetic.example", transport=httpx.MockTransport(handle)))
    assert paths==["/healthz","/api/voice/turn"]
