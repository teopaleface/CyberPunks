import asyncio
import json

import httpx
import pytest

from cyberpunks.channels.elevenlabs import (
    LIVE_VOICE_MODEL,
    VOICE_NOTE_MODEL,
    VOICE_SESSION_SECONDS,
    ElevenLabs,
    agent_config,
    get_key,
    verify_agent,
)
from cyberpunks.channels.models import ChannelError


def test_agents_are_private_bounded_and_wait_for_actual_reply():
    for role in ["customer", "technician", "dispatcher"]:
        config = agent_config(role, "synthetic-voice-id")
        verify_agent(config)
        tool = config["conversation_config"]["agent"]["prompt"]["tools"][0]
        assert tool["name"] == "daybreak_turn" and tool["expects_response"] is True
        assert config["platform_settings"]["call_limits"]["bursting_enabled"] is False
        assert config["platform_settings"]["privacy"]["record_voice"] is False
        conversation = config["conversation_config"]
        assert conversation["vad"]["background_voice_detection"] is True
        assert conversation["tts"]["model_id"] == LIVE_VOICE_MODEL
        assert conversation["conversation"]["max_duration_seconds"] == VOICE_SESSION_SECONDS
        assert tool["interruption_mode"] == "disable_during_tool_and_turn"


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


def test_voice_notes_use_current_models_and_preserve_the_verified_text(tmp_path, monkeypatch):
    monkeypatch.setenv("DAYBREAK_CHANNELS_RUNTIME", str(tmp_path))
    monkeypatch.setenv("ELEVENLABS_API_KEY", "synthetic-private-key")
    (tmp_path / "channels.json").write_text(json.dumps({"voice_id": "syntheticvoice123"}))
    text = "Verific informațiile despre oprirea următoare."

    async def handler(request):
        if request.url.path == "/v1/speech-to-text":
            body = request.content
            assert b"scribe_v2" in body and b"scribe_v1" not in body
            return httpx.Response(200, json={"text": text})
        body = json.loads(request.content)
        assert body["model_id"] == VOICE_NOTE_MODEL and body["text"] == text
        return httpx.Response(200, content=b"synthetic-audio")

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = ElevenLabs(client)
            assert await provider.transcribe(b"synthetic-input", "audio/ogg") == text
            assert await provider.synthesize(text) == b"synthetic-audio"

    asyncio.run(run())


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


def test_provider_test_cleanup_accepts_empty_success(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "synthetic-secret")

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(204))) as client:
            assert await ElevenLabs(client).request("DELETE", "/v1/convai/agent-testing/synthetic-test") == {}

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
