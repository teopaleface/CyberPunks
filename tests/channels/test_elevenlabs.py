import asyncio
import json

import httpx
import pytest

from cyberpunks.channels.elevenlabs import ElevenLabs, agent_config, get_key, verify_agent
from cyberpunks.channels.models import ChannelError


def test_agents_are_private_bounded_and_wait_for_actual_reply():
    for role in ["customer", "technician", "dispatcher"]:
        config = agent_config(role, "synthetic-voice-id")
        verify_agent(config)
        tool = config["conversation_config"]["agent"]["prompt"]["tools"][0]
        assert tool["name"] == "daybreak_turn" and tool["expects_response"] is True
        assert config["platform_settings"]["call_limits"]["bursting_enabled"] is False
        assert config["platform_settings"]["privacy"]["record_voice"] is False


@pytest.mark.parametrize("change", ["auth", "tool", "mcp", "duration"])
def test_unsafe_live_agent_fails_session_preflight(change):
    config = agent_config("customer", "synthetic-voice-id")
    if change == "auth":
        config["platform_settings"]["auth"]["enable_auth"] = False
    if change == "tool":
        config["conversation_config"]["agent"]["prompt"]["tools"][0]["expects_response"] = False
    if change == "mcp":
        config["conversation_config"]["agent"]["prompt"]["mcp_server_ids"] = ["unexpected"]
    if change == "duration":
        config["conversation_config"]["conversation"]["max_duration_seconds"] = 3600
    with pytest.raises(ChannelError):
        verify_agent(config)


def test_session_returns_only_short_lived_auth_for_server_selected_role(tmp_path, monkeypatch):
    monkeypatch.setenv("DAYBREAK_CHANNELS_RUNTIME", str(tmp_path))
    monkeypatch.setenv("ELEVENLABS_API_KEY", "synthetic-secret-never-in-browser")
    (tmp_path / "channels.json").write_text(json.dumps({"agents": {"technician": "agent_synthetictech"}}))
    calls = []

    async def handler(request):
        calls.append(request)
        assert request.headers["xi-api-key"] == "synthetic-secret-never-in-browser"
        if "/agents/" in request.url.path:
            return httpx.Response(200, json=agent_config("technician", "synthetic-voice-id"))
        assert request.url.params["agent_id"] == "agent_synthetictech"
        return httpx.Response(200, json={"token": "synthetic-temporary-token"})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            result = await ElevenLabs(client).session("technician")
            assert "synthetic-secret" not in json.dumps(result)
            assert result["conversation_token"] == "synthetic-temporary-token"
            assert result["role"] == "technician" and result["connection_type"] == "webrtc"

    asyncio.run(run())
    assert len(calls) == 2


def test_provider_rejection_never_echoes_secret(tmp_path, monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "synthetic-secret")

    async def run():
        async def handler(request):
            return httpx.Response(403, json={"detail": {"status": "ip_not_allowed", "message": "synthetic-secret"}})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            with pytest.raises(ChannelError, match="ip_not_allowed") as caught:
                await ElevenLabs(client).request("GET", "/v1/user/subscription")
            assert "synthetic-secret" not in str(caught.value)

    asyncio.run(run())


def test_key_file_requires_private_permissions(tmp_path, monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.setenv("DAYBREAK_CHANNELS_RUNTIME", str(tmp_path))
    path = tmp_path / "channels.env"
    path.write_text("ELEVENLABS_API_KEY=synthetic-secret")
    path.chmod(0o644)
    with pytest.raises(ChannelError, match="private"):
        get_key()
    path.chmod(0o600)
    assert get_key() == "synthetic-secret"


def test_private_existing_key_overrides_inherited_key_id(tmp_path, monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "synthetic-invalid-key-id")
    monkeypatch.setenv("DAYBREAK_CHANNELS_RUNTIME", str(tmp_path))
    path = tmp_path / "channels.env"
    path.write_text("ELEVENLABS_API_KEY=synthetic-valid-key")
    path.chmod(0o600)
    assert get_key() == "synthetic-valid-key"
