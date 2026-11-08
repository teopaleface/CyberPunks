"""Regressions from the real phone transcript: silence was forwarded as punctuation."""

import pytest
from fastapi.testclient import TestClient

from cyberpunks.channels.whatsapp_calls import call_agent_config, create_app


@pytest.mark.parametrize("message", ["...", "…", ".", "   ", "", "[silence]", "[inaudible]"])
def test_silence_is_quiet_and_never_sent_to_conversation(env, message):
    class Binding:
        def resolve(self, destination, sender):
            return env["actors"]["technician"]

    config = {"tool_token": "synthetic-token", "phone_number_id": "synthetic-phone", "allowed_callers": ["40700000000"]}
    client = TestClient(create_app(service=env["conversation"], bindings=Binding(), config_loader=lambda: config))
    response = client.post(
        "/api/voice/turn",
        headers={"authorization": "Bearer synthetic-token"},
        json={"message": message, "caller_id": "+40700000000", "conversation_id": "synthetic-silence"},
    )
    assert response.status_code == 200
    assert response.json() == {"reply": ""}
    assert not env["provider"].prompts
    assert (
        client.post(
            "/api/voice/turn",
            json={"message": message, "caller_id": "+40700000000", "conversation_id": "synthetic-silence"},
        ).status_code
        == 401
    )


def test_call_configuration_does_not_speak_preambles_or_reengage_after_five_seconds():
    config = call_agent_config(
        "syntheticvoice123", "https://synthetic.trycloudflare.com", "synthetic-secret", demo_enabled=True
    )
    conversation = config["conversation_config"]
    tool = conversation["agent"]["prompt"]["tools"][0]
    assert tool["pre_tool_speech"] == "off"
    assert tool["interruption_mode"] == "allow"
    assert conversation["turn"]["turn_timeout"] >= 60
    assert conversation["turn"]["retranscribe_on_turn_timeout"] is False
    assert {"PPC", "stâlp", "client", "dispecer", "tehnician"} <= set(conversation["asr"]["keywords"])


def test_microphone_check_has_an_immediate_reply_without_operational_inference(env):
    class Binding:
        def resolve(self, destination, sender):
            return env["actors"]["technician"]

    config = {"tool_token": "synthetic-token", "phone_number_id": "synthetic-phone", "allowed_callers": ["40700000000"]}
    client = TestClient(create_app(service=env["conversation"], bindings=Binding(), config_loader=lambda: config))
    r = client.post(
        "/api/voice/turn",
        headers={"authorization": "Bearer synthetic-token"},
        json={"message": "Mă auzi?", "caller_id": "+40700000000", "conversation_id": "synthetic-mic"},
    )
    assert r.status_code == 200 and r.json() == {"reply": "Te aud. Spune-mi întrebarea."}
    assert not env["provider"].prompts
