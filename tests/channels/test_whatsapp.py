import asyncio
import hashlib
import hmac
import json

import httpx
import pytest

from cyberpunks.channels.models import ChannelError
from cyberpunks.channels.whatsapp import Bindings, Inbox, MetaMedia, WhatsAppAdapter, verify_signature

from .conftest import intention


def make_adapter(env, *, audio=False):
    sender = "synthetic-verified-sender"
    binding = env["tmp"] / "whatsapp-bindings.json"
    binding.write_text(
        json.dumps(
            {
                "phone_number_id": "synthetic-business-number-id",
                "senders": {
                    hashlib.sha256(sender.encode()).hexdigest(): {
                        "active": True,
                        "verified_at": "2026-11-07T00:00:00Z",
                        "verification_source": "synthetic-test-provisioning",
                        "actor": env["actors"]["customer"].model_dump(),
                    }
                },
            }
        )
    )
    binding.chmod(0o600)

    class SimulatedMedia:
        async def download(self, media_id):
            assert media_id == "12345"
            return b"synthetic-audio-not-real-speech", "audio/ogg"

    class SimulatedSTT:
        async def transcribe(self, body, mime):
            assert body == b"synthetic-audio-not-real-speech"
            return "My inverter stops at noon"

        async def synthesize(self, text):
            raise AssertionError("Audio replies must not run without verified opt-in")

    inbox = Inbox(env["tmp"] / "inbox.sqlite3")
    adapter = WhatsAppAdapter(
        env["conversation"],
        Bindings(binding),
        inbox,
        media_factory=lambda destination: SimulatedMedia(),
        transcriber=SimulatedSTT(),
    )
    msg = {
        "from": sender,
        "id": "synthetic-message-1",
        "type": "audio" if audio else "text",
        "text": {"body": "My inverter stops at noon"},
        "audio": {"id": "12345", "url": "http://127.0.0.1/private-do-not-fetch"},
        "role": "dispatcher",
    }
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {"value": {"metadata": {"phone_number_id": "synthetic-business-number-id"}, "messages": [msg]}}
                ]
            }
        ],
    }
    return adapter, inbox, payload, msg


def test_signature_verification_uses_raw_body_before_json_parse(env, monkeypatch):
    monkeypatch.setenv("DAYBREAK_WHATSAPP_ENABLED", "1")
    monkeypatch.setenv("DAYBREAK_META_APP_SECRET", "synthetic-meta-secret")
    response = env["client"].post(
        "/api/conversation/whatsapp/webhook", content=b"invalid-json", headers={"x-hub-signature-256": "sha256=bad"}
    )
    assert response.status_code == 401 and response.json()["detail"]["code"] == "invalid_signature"
    body = b'{"messages":[]}'
    signature = "sha256=" + hmac.new(b"synthetic-meta-secret", body, hashlib.sha256).hexdigest()
    verify_signature(body, signature, "synthetic-meta-secret")
    with pytest.raises(ChannelError):
        verify_signature(body + b" ", signature, "synthetic-meta-secret")


def test_whatsapp_disabled_by_default(env, monkeypatch):
    monkeypatch.delenv("DAYBREAK_WHATSAPP_ENABLED", raising=False)
    r = env["client"].post("/api/conversation/whatsapp/webhook", json={})
    assert r.status_code == 503 and r.json()["detail"]["code"] == "whatsapp_disabled"


@pytest.mark.parametrize("audio", [False, True])
def test_text_and_transcribed_voice_notes_use_same_service_without_sends(env, audio):
    adapter, inbox, payload, _message = make_adapter(env, audio=audio)
    env["provider"].output = intention(
        kind="prepare",
        action="create_case",
        connection_id=env["binding"]["connection_ids"][0],
        symptom="Inverter stops at noon",
        symptom_type="voltage",
    )

    async def run():
        assert (await adapter.receive(payload))["accepted"] == 1
        assert (await adapter.receive(payload))["duplicates"] == 1

    asyncio.run(run())
    with inbox.connect() as db:
        result = json.loads(db.execute("SELECT result FROM inbox").fetchone()[0])
    assert result["input_type"] == ("voice_note" if audio else "text")
    assert result["response"]["proposal"]["proposal_id"]
    assert result["outbound_status"] == "not_sent"
    assert result["tts"] == "disabled_no_audio_reply_opt_in"
    assert env["operations"].context(env["actors"]["customer"])["cases"] == []
    prompt_payload = json.loads(env["provider"].prompts[-1].split("INPUT JSON:\n")[1])
    assert prompt_payload["role"] == "customer"
    assert '"role": "dispatcher"' not in env["provider"].prompts[-1]


def test_unknown_sender_and_wrong_destination_do_not_call_model(env):
    adapter, _inbox, payload, message = make_adapter(env)
    message["from"] = "unverified-attacker"
    with pytest.raises(ChannelError, match="verified account"):
        asyncio.run(adapter.receive(payload))
    assert not env["provider"].prompts


def test_retry_after_provider_failure_and_persistent_dedupe(env):
    adapter, inbox, payload, _message = make_adapter(env)
    env["provider"].error = ChannelError("provider_timeout", "Simulated provider timeout", 504)
    with pytest.raises(ChannelError):
        asyncio.run(adapter.receive(payload))
    env["provider"].error = None
    result = asyncio.run(adapter.receive(payload))
    assert result["accepted"] == 1
    adapter.inbox = Inbox(inbox.path)
    assert asyncio.run(adapter.receive(payload))["duplicates"] == 1


def test_in_progress_duplicate_requires_retry_instead_of_success_ack(env):
    inbox = Inbox(env["tmp"] / "inprogress.sqlite3")
    assert inbox.claim("synthetic-event") is True
    with pytest.raises(ChannelError) as e:
        inbox.claim("synthetic-event")
    assert e.value.status_code == 429


@pytest.mark.parametrize(
    "url",
    [
        "http://lookaside.fbsbx.com/audio",
        "https://127.0.0.1/private",
        "https://attacker.test/audio",
        "https://lookaside.fbsbx.com@attacker.test/audio",
    ],
)
def test_voice_note_metadata_cannot_redirect_to_arbitrary_hosts(url):
    calls = []

    async def run():
        async def handler(request):
            calls.append(request)
            return httpx.Response(
                200, json={"id": "12345", "url": url, "mime_type": "audio/ogg", "file_size": 10, "sha256": "x"}
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False) as client:
            with pytest.raises(ChannelError, match="authorized Meta media host"):
                await MetaMedia("synthetic-token", "synthetic-number", client=client).download("12345")

    asyncio.run(run())
    assert len(calls) == 1


def test_media_integrity_and_fixed_meta_access_token():
    body = b"synthetic-audio-not-real-speech"

    async def run():
        async def handler(request):
            assert request.headers["authorization"] == "Bearer synthetic-token"
            if request.url.host == "graph.facebook.com":
                assert request.url.params["phone_number_id"] == "synthetic-number"
                return httpx.Response(
                    200,
                    json={
                        "id": "12345",
                        "url": "https://lookaside.fbsbx.com/audio",
                        "mime_type": "audio/ogg",
                        "file_size": len(body),
                        "sha256": hashlib.sha256(body).hexdigest(),
                    },
                )
            return httpx.Response(200, headers={"content-type": "audio/ogg"}, content=body)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False) as client:
            result, mime = await MetaMedia("synthetic-token", "synthetic-number", client=client).download("12345")
            assert result == body and mime == "audio/ogg"

    asyncio.run(run())
