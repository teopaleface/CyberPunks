"""Simulated Meta HTTP and Codex; real scoped operations and durable queue/outbox."""

import asyncio
import hashlib
import hmac
import json
import time

import httpx
import pytest

from cyberpunks.channels.models import ChannelError
from cyberpunks.channels.whatsapp_config import confirmation_text
from cyberpunks.channels.whatsapp_queue import enqueue_payload
from cyberpunks.channels.whatsapp_store import DeliveryStore
from cyberpunks.channels.whatsapp_transport import MetaTransport
from cyberpunks.channels.whatsapp_worker import WhatsAppWorker

from .test_whatsapp import make_adapter


@pytest.fixture
def delivery(env, monkeypatch):
    import cyberpunks.channels.whatsapp as whatsapp_module
    from cyberpunks.channels.limits import Limits

    # Separate synthetic accounts in each test must not share a previous test's minute budget.
    monkeypatch.setattr(whatsapp_module, "limits", Limits())
    adapter, inbox, payload, message = make_adapter(env)
    destination = "123456789"
    config = json.loads(adapter.bindings.path.read_text())
    config["phone_number_id"] = destination
    adapter.bindings.path.write_text(json.dumps(config))
    message["timestamp"] = str(int(time.time()))
    payload["entry"][0]["changes"][0]["value"]["metadata"]["phone_number_id"] = destination
    for key, value in {
        "DAYBREAK_CHANNELS_RUNTIME": str(env["tmp"]),
        "DAYBREAK_WHATSAPP_ENABLED": "1",
        "DAYBREAK_WHATSAPP_SEND_ENABLED": "1",
        "DAYBREAK_META_PHONE_NUMBER_ID": destination,
        "DAYBREAK_META_ACCESS_TOKEN": "synthetic-meta-token",
        "DAYBREAK_META_GRAPH_VERSION": "v25.0",
        "DAYBREAK_META_APP_SECRET": "synthetic-signing-secret",
    }.items():
        monkeypatch.setenv(key, value)
    store = DeliveryStore(inbox.path)
    return adapter, store, payload, message


def incoming(delivery):
    adapter, store, payload, _ = delivery
    assert enqueue_payload(payload, adapter.bindings, store)["queued"] == 1
    return store.next()


def test_webhook_ack_is_durable_without_waiting_for_model(env, delivery):
    _adapter, _store, payload, _ = delivery
    # The HTTP handler must not call a provider, even when it would be unavailable for 55 seconds.
    env["provider"].error = ChannelError("provider_unavailable", "Synthetic unavailable provider")
    body = json.dumps(payload).encode()
    sig = "sha256=" + hmac.new(b"synthetic-signing-secret", body, hashlib.sha256).hexdigest()
    started = time.monotonic()
    r = env["client"].post("/api/conversation/whatsapp/webhook", content=body, headers={"x-hub-signature-256": sig})
    assert r.status_code == 200 and r.json()["queued"] == 1
    assert time.monotonic() - started < 1
    assert not env["provider"].prompts
    persisted = DeliveryStore(env["tmp"] / "channels-whatsapp.sqlite3")
    assert persisted.counts()["inbound_queue"] == {"queued": 1}


def test_queue_requires_current_bound_sender_destination_and_timestamp(delivery):
    adapter, store, payload, message = delivery
    message["from"] = "unbound-sender"
    with pytest.raises(ChannelError):
        enqueue_payload(payload, adapter.bindings, store)
    assert store.counts()["inbound_queue"] == {}


def test_persistent_duplicate_ack_never_runs_model_twice(delivery):
    adapter, store, payload, _ = delivery
    assert enqueue_payload(payload, adapter.bindings, store)["queued"] == 1
    after_restart = DeliveryStore(store.path)
    assert enqueue_payload(payload, adapter.bindings, after_restart)["duplicates"] == 1
    assert not adapter.conversation.provider.prompts


def test_text_reply_only_to_verified_inbound_sender_and_only_once(delivery):
    adapter, store, _, message = delivery
    event = incoming(delivery)
    calls = []

    async def handler(request):
        calls.append(request)
        body = json.loads(request.content)
        assert str(request.url) == "https://graph.facebook.com/v25.0/123456789/messages"
        assert request.headers["authorization"] == "Bearer synthetic-meta-token"
        assert body["to"] == message["from"] and body["context"]["message_id"] == message["id"]
        assert body["type"] == "text" and not body["text"]["preview_url"]
        return httpx.Response(200, json={"messages": [{"id": "wamid.synthetic-text"}]})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            transport = MetaTransport(adapter.bindings, adapter.conversation.operations, store, client=client)
            assert await transport.send(event, text="Verified reply") == "accepted"
            assert await transport.send(event, text="Verified reply") == "accepted"

    asyncio.run(run())
    assert len(calls) == 1
    assert store.counts()["outbound"] == {"accepted": 1}


@pytest.mark.parametrize("failure", ["timeout", "server_error", "missing_message_id"])
def test_unknown_send_outcome_never_blindly_resends(delivery, failure):
    adapter, store, _, _ = delivery
    event = incoming(delivery)
    calls = []

    async def handler(request):
        calls.append(request)
        if failure == "timeout":
            raise httpx.ReadTimeout("synthetic timeout", request=request)
        if failure == "server_error":
            return httpx.Response(502, json={"error": {}})
        return httpx.Response(200, json={"messages": []})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            transport = MetaTransport(adapter.bindings, adapter.conversation.operations, store, client=client)
            assert await transport.send(event, text="Verified reply") == "unknown"
            store.recover()
            assert await transport.send(event, text="Verified reply") == "unknown"

    asyncio.run(run())
    assert len(calls) == 1
    assert store.counts()["outbound"] == {"unknown": 1}


def test_inflight_send_recovers_to_unknown_after_worker_crash(delivery):
    _, store, _, _ = delivery
    event = incoming(delivery)
    row = store.prepare(event["event_id"], event["destination"], event["sender"], "text", b"reply")
    assert store.begin_send(row["part_id"])
    store.recover()
    assert store.counts()["outbound"] == {"unknown": 1}
    assert not store.begin_send(row["part_id"])


def test_signed_status_reconciles_unknown_without_another_send(delivery):
    adapter, store, payload, _ = delivery
    event = incoming(delivery)
    row = store.prepare(event["event_id"], event["destination"], event["sender"], "text", b"reply")
    store.outbound_state(row["part_id"], "unknown")
    store.queue_state(event["event_id"], "needs_reconciliation")
    value = payload["entry"][0]["changes"][0]["value"]
    value["messages"] = []
    value["statuses"] = [
        {
            "id": "wamid.synthetic-known",
            "recipient_id": event["sender"],
            "status": "delivered",
            "biz_opaque_callback_data": row["part_id"],
        }
    ]
    enqueue_payload(payload, adapter.bindings, store)
    assert store.counts()["outbound"] == {"delivered": 1}
    assert store.counts()["inbound_queue"] == {"accepted": 1}
    # A delayed network timeout cannot erase a delivery callback that already arrived.
    assert store.outbound_state(row["part_id"], "unknown") == "delivered"


def test_wrong_recipient_status_cannot_reconcile(delivery):
    _, store, _, _ = delivery
    event = incoming(delivery)
    row = store.prepare(event["event_id"], event["destination"], event["sender"], "text", b"reply")
    store.outbound_state(row["part_id"], "unknown")
    store.reconcile(
        event["destination"],
        {
            "id": "wamid.fake",
            "recipient_id": "another-sender",
            "status": "delivered",
            "biz_opaque_callback_data": row["part_id"],
        },
    )
    assert store.counts()["outbound"] == {"unknown": 1}


def test_audio_is_opt_in_upload_then_true_voice_note(delivery):
    adapter, store, _, _ = delivery
    event = incoming(delivery)
    cfg = json.loads(adapter.bindings.path.read_text())
    for b in cfg["senders"].values():
        b["audio_replies_opted_in"] = True
    adapter.bindings.path.write_text(json.dumps(cfg))
    audio = b"OggS-synthetic-OpusHead-not-real-speech"
    calls = []

    async def handler(request):
        calls.append(request)
        if request.url.path.endswith("/media"):
            assert b"audio/ogg" in request.content
            return httpx.Response(200, json={"id": "987654"})
        body = json.loads(request.content)
        assert body["audio"] == {"id": "987654", "voice": True}
        assert body["to"] == event["sender"]
        return httpx.Response(200, json={"messages": [{"id": "wamid.synthetic-audio"}]})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            transport = MetaTransport(adapter.bindings, adapter.conversation.operations, store, client=client)
            assert await transport.send(event, audio=audio) == "accepted"
            assert await transport.send(event, audio=audio) == "accepted"

    asyncio.run(run())
    assert len(calls) == 2


def test_audio_without_opt_in_and_disabled_send_never_hit_network(delivery, monkeypatch):
    adapter, store, _, _ = delivery
    event = incoming(delivery)

    async def handler(request):
        raise AssertionError("No network request is allowed")

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            transport = MetaTransport(adapter.bindings, adapter.conversation.operations, store, client=client)
            with pytest.raises(ChannelError):
                await transport.send(event, audio=b"OggS-OpusHead")
            monkeypatch.setenv("DAYBREAK_WHATSAPP_SEND_ENABLED", "0")
            with pytest.raises(ChannelError):
                await transport.send(event, text="reply")

    asyncio.run(run())
    assert store.counts()["outbound"] == {}


def test_revoked_or_changed_binding_blocks_queued_reply(delivery):
    adapter, store, _, _ = delivery
    event = incoming(delivery)
    cfg = json.loads(adapter.bindings.path.read_text())
    for b in cfg["senders"].values():
        b["actor"]["role"] = "dispatcher"
    adapter.bindings.path.write_text(json.dumps(cfg))
    transport = MetaTransport(adapter.bindings, adapter.conversation.operations, store)
    with pytest.raises(ChannelError) as caught:
        transport.authorize(event)
    assert caught.value.code == "sender_binding_changed"


def test_worker_restart_reuses_prepared_reply_without_model_or_send_duplicate(delivery):
    adapter, store, payload, _ = delivery
    enqueue_payload(payload, adapter.bindings, store)
    calls = []

    async def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"messages": [{"id": "wamid.synthetic-worker"}]})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            transport = MetaTransport(adapter.bindings, adapter.conversation.operations, store, client=client)
            w = WhatsAppWorker(adapter, store, transport)
            assert await w.step()
            assert not await w.step()
            store.recover()
            assert not await w.step()

    asyncio.run(run())
    assert len(calls) == 1 and len(adapter.conversation.provider.prompts) == 1
    assert store.counts()["inbound_queue"] == {"accepted": 1}


def test_confirmation_link_only_comes_from_explicit_trusted_origin(monkeypatch):
    response = {"reply": "Your report is ready.", "language": "en", "proposal": {"proposal_id": "synthetic"}}
    monkeypatch.delenv("DAYBREAK_PUBLIC_APP_ORIGIN", raising=False)
    assert "Confirmation is still pending" in confirmation_text(response)
    for bad in ["http://evil.test", "https://evil.test/path", "https://user:pass@evil.test"]:
        monkeypatch.setenv("DAYBREAK_PUBLIC_APP_ORIGIN", bad)
        assert bad not in confirmation_text(response)
    monkeypatch.setenv("DAYBREAK_PUBLIC_APP_ORIGIN", "https://trusted.example")
    assert confirmation_text(response).endswith("https://trusted.example/workspace?proposal=synthetic")


def test_prepared_reply_survives_crash_before_network_send(delivery):
    adapter, store, payload, _ = delivery
    enqueue_payload(payload, adapter.bindings, store)
    event = store.next()
    asyncio.run(adapter.receive(payload))
    assert len(adapter.conversation.provider.prompts) == 1
    # Previous process died after inference committed its result but before any POST to Meta.
    store.recover()
    calls = []

    async def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"messages": [{"id": "wamid.recovered-reply"}]})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            worker = WhatsAppWorker(
                adapter,
                DeliveryStore(store.path),
                MetaTransport(adapter.bindings, adapter.conversation.operations, store, client=client),
            )
            assert await worker.step()

    asyncio.run(run())
    assert len(calls) == 1 and len(adapter.conversation.provider.prompts) == 1
    assert adapter.inbox.result(event["event_id"])["outbound_status"] == "meta_accepted"


def test_worker_bootstraps_isolated_paths_before_operations_import(env, monkeypatch):
    import os
    import subprocess
    import sys

    path = env["tmp"] / "daybreak.env"
    selected = env["tmp"] / "isolated-output-path"
    path.write_text(
        "CYBERPUNKS_OUTPUT_ROOT="
        + str(selected)
        + "\nDAYBREAK_OPERATIONS_OUTPUTS="
        + str(env["operations"].outputs)
        + "\nDAYBREAK_OPERATIONS_DB="
        + str(env["tmp"] / "bootstrap.sqlite3")
        + "\n"
    )
    path.chmod(0o600)
    code = "from cyberpunks.channels.whatsapp_worker import worker; w=worker(); from cyberpunks.common.paths import OUTPUTS; import os; assert str(OUTPUTS)==os.environ['CYBERPUNKS_OUTPUT_ROOT']; assert str(w.adapter.conversation.operations.outputs)==os.environ['DAYBREAK_OPERATIONS_OUTPUTS']; print('isolated imports OK')"
    result = subprocess.run(
        [sys.executable, "-c", code],
        env={"PATH": os.getenv("PATH", ""), "HOME": str(env["tmp"]), "DAYBREAK_CHANNELS_RUNTIME": str(env["tmp"])},
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "isolated imports OK"


def opt_in_voice(delivery):
    adapter, store, payload, message = delivery
    config = json.loads(adapter.bindings.path.read_text())
    for binding in config["senders"].values():
        binding["audio_replies_opted_in"] = True
    adapter.bindings.path.write_text(json.dumps(config))
    message["type"] = "audio"
    return adapter, store, payload, message


@pytest.mark.parametrize("failure", ["provider_error", "unexpected_error"])
def test_optional_tts_failure_keeps_text_and_one_codex_call(delivery, monkeypatch, failure):
    adapter, store, payload, _ = opt_in_voice(delivery)
    enqueue_payload(payload, adapter.bindings, store)
    calls = []
    tts_calls = []

    async def synthesize(text):
        # The verified response is already committed while optional TTS is still pending.
        with adapter.inbox.connect() as db:
            saved = json.loads(db.execute("SELECT result FROM inbox").fetchone()[0])
        assert saved["response"]["reply"] == text and saved["tts"] == "pending"
        tts_calls.append(text)
        if failure == "provider_error":
            raise ChannelError("tts_unavailable", "Synthetic optional TTS failure")
        raise RuntimeError("Synthetic unexpected TTS failure")

    monkeypatch.setattr(adapter.transcriber, "synthesize", synthesize)

    async def handler(request):
        body = json.loads(request.content)
        calls.append(body)
        assert body["type"] == "text"
        return httpx.Response(200, json={"messages": [{"id": "wamid.text-after-tts-failure"}]})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            w = WhatsAppWorker(
                adapter, store, MetaTransport(adapter.bindings, adapter.conversation.operations, store, client=client)
            )
            assert await w.step()
            store.recover()
            assert not await w.step()

    asyncio.run(run())
    assert len(adapter.conversation.provider.prompts) == len(tts_calls) == len(calls) == 1
    assert store.counts()["inbound_queue"] == {"accepted": 1}
    assert store.counts()["outbound"] == {"accepted": 1}


@pytest.mark.parametrize("failure", ["conversion", "upload"])
def test_optional_voice_conversion_or_upload_failure_falls_back_without_repeat(delivery, monkeypatch, failure):
    import cyberpunks.channels.whatsapp_worker as worker_module

    adapter, store, payload, _ = opt_in_voice(delivery)
    enqueue_payload(payload, adapter.bindings, store)

    async def synthesize(text):
        return b"synthetic-mp3-not-real-speech"

    async def encode(mp3):
        if failure == "conversion":
            raise ChannelError("voice_encoding_failed", "Synthetic conversion failure")
        return b"OggS-synthetic-OpusHead-not-real-speech"

    monkeypatch.setattr(adapter.transcriber, "synthesize", synthesize)
    monkeypatch.setattr(worker_module, "voice_note", encode)
    text_calls = []
    uploads = []

    async def handler(request):
        if request.url.path.endswith("/media"):
            uploads.append(request)
            return httpx.Response(503, json={"error": {"code": 1}})
        body = json.loads(request.content)
        text_calls.append(body)
        assert body["type"] == "text"
        return httpx.Response(200, json={"messages": [{"id": "wamid.text-after-audio-failure"}]})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            w = WhatsAppWorker(
                adapter, store, MetaTransport(adapter.bindings, adapter.conversation.operations, store, client=client)
            )
            assert await w.step()
            store.recover()
            assert not await w.step()

    asyncio.run(run())
    assert len(text_calls) == len(adapter.conversation.provider.prompts) == 1
    assert len(uploads) == (1 if failure == "upload" else 0)
    assert store.counts()["inbound_queue"] == {"accepted": 1}
    expected = {"accepted": 1, "cancelled": 1} if failure == "upload" else {"accepted": 1}
    assert store.counts()["outbound"] == expected
    with adapter.inbox.connect() as db:
        result = json.loads(db.execute("SELECT result FROM inbox").fetchone()[0])
    assert result["audio_delivery"] == "failed_text_fallback"


def test_failed_callback_before_http_200_remains_failed(delivery):
    adapter, store, payload, _ = delivery
    enqueue_payload(payload, adapter.bindings, store)
    calls = []

    async def handler(request):
        body = json.loads(request.content)
        calls.append(body)
        store.reconcile(
            "123456789",
            {
                "id": "wamid.failed-before-response",
                "recipient_id": body["to"],
                "status": "failed",
                "biz_opaque_callback_data": body["biz_opaque_callback_data"],
            },
        )
        assert store.counts()["outbound"] == {"failed": 1}
        return httpx.Response(200, json={"messages": [{"id": "wamid.failed-before-response"}]})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            w = WhatsAppWorker(
                adapter, store, MetaTransport(adapter.bindings, adapter.conversation.operations, store, client=client)
            )
            assert await w.step()
            assert not await w.step()

    asyncio.run(run())
    assert len(calls) == 1
    assert store.counts()["outbound"] == {"failed": 1}
    assert store.counts()["inbound_queue"] == {"failed": 1}


def test_audio_fallback_cannot_clear_unknown_send(delivery, monkeypatch):
    adapter, store, payload, _ = opt_in_voice(delivery)
    event = incoming(delivery)
    asyncio.run(adapter.receive(payload))  # Existing simulated TTS fails; text is now durable.
    row = store.prepare(event["event_id"], event["destination"], event["sender"], "audio", b"old-audio")
    store.outbound_state(row["part_id"], "unknown")
    store.recover()

    async def handler(request):
        body = json.loads(request.content)
        assert body["type"] == "text"
        return httpx.Response(200, json={"messages": [{"id": "wamid.text-with-unknown-audio"}]})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            w = WhatsAppWorker(
                adapter, store, MetaTransport(adapter.bindings, adapter.conversation.operations, store, client=client)
            )
            assert await w.step()

    asyncio.run(run())
    assert store.counts()["inbound_queue"] == {"needs_reconciliation": 1}
    assert store.counts()["outbound"] == {"accepted": 1, "unknown": 1}


@pytest.mark.parametrize(
    "message,language", [("De ce mergem la următoarea oprire?", "ro"), ("Why are we going to the next stop?", "en")]
)
def test_terminal_grounding_error_sends_one_controlled_reply_without_actions(delivery, monkeypatch, message, language):
    adapter, store, payload, inbound = delivery
    inbound["text"]["body"] = message
    adapter.conversation.provider.error = ChannelError(
        "ungrounded_reply", "PRIVATE MODEL ERROR THAT MUST NOT BE RELAYED"
    )
    enqueue_payload(payload, adapter.bindings, store)
    calls = []

    async def synthesize(text):
        raise AssertionError("Server feedback must not use optional TTS")

    monkeypatch.setattr(adapter.transcriber, "synthesize", synthesize)

    async def handler(request):
        body = json.loads(request.content)
        calls.append(body)
        assert body["type"] == "text" and "PRIVATE" not in body["text"]["body"]
        return httpx.Response(200, json={"messages": [{"id": "wamid.controlled-feedback"}]})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            w = WhatsAppWorker(
                adapter, store, MetaTransport(adapter.bindings, adapter.conversation.operations, store, client=client)
            )
            for attempt in range(3):
                assert await w.step()
                if attempt < 2:
                    assert calls == []
                    with store.connect() as db:
                        db.execute("UPDATE inbound_queue SET retry_at=0 WHERE state='retryable'")
            store.recover()
            assert not await w.step()

    asyncio.run(run())
    assert len(adapter.conversation.provider.prompts) == 3 and len(calls) == 1
    assert store.counts()["inbound_queue"] == {"accepted": 1}
    assert store.counts()["outbound"] == {"accepted": 1}
    with adapter.inbox.connect() as db:
        result = json.loads(db.execute("SELECT result FROM inbox").fetchone()[0])
    response = result["response"]
    assert response["provider"] == "server-fallback" and response["proposal"] is None
    assert response["language"] == language and response["provenance"]["write_executed"] is False
    assert result["delivery_text"] == calls[0]["text"]["body"] == response["reply"]
    assert result["tts"] == "disabled_server_fallback" and result["audio_reply_path"] is None
    actor = next(iter(json.loads(adapter.bindings.path.read_text())["senders"].values()))["actor"]
    from cyberpunks.operations.models import Actor

    assert adapter.conversation.operations.context(Actor.model_validate(actor))["cases"] == []
    with adapter.conversation.operations.db.connect() as db:
        assert db.execute("SELECT count(*) FROM proposals").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM commands").fetchone()[0] == 0


def test_revocation_during_final_provider_error_prevents_feedback(delivery, monkeypatch):
    adapter, store, payload, _ = delivery
    enqueue_payload(payload, adapter.bindings, store)
    attempts = []

    async def unavailable(prompt):
        attempts.append(prompt)
        if len(attempts) == 3:
            config = json.loads(adapter.bindings.path.read_text())
            for binding in config["senders"].values():
                binding["active"] = False
            adapter.bindings.path.write_text(json.dumps(config))
        raise ChannelError("provider_unavailable", "Synthetic unavailable model")

    monkeypatch.setattr(adapter.conversation.provider, "turn", unavailable)

    async def handler(request):
        raise AssertionError("Revoked sender must not receive feedback")

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            w = WhatsAppWorker(
                adapter, store, MetaTransport(adapter.bindings, adapter.conversation.operations, store, client=client)
            )
            for _ in range(3):
                assert await w.step()
                with store.connect() as db:
                    db.execute("UPDATE inbound_queue SET retry_at=0 WHERE state='retryable'")

    asyncio.run(run())
    assert len(attempts) == 3
    assert store.counts()["outbound"] == {}
    assert store.counts()["inbound_queue"] == {"failed": 1}


def test_terminal_feedback_timeout_is_unknown_without_auto_resend(delivery):
    adapter, store, payload, _ = delivery
    adapter.conversation.provider.error = ChannelError("provider_timeout", "Synthetic timeout", 504)
    enqueue_payload(payload, adapter.bindings, store)
    calls = []

    async def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout("Synthetic ambiguous send", request=request)

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            w = WhatsAppWorker(
                adapter, store, MetaTransport(adapter.bindings, adapter.conversation.operations, store, client=client)
            )
            for _ in range(3):
                assert await w.step()
                with store.connect() as db:
                    db.execute("UPDATE inbound_queue SET retry_at=0 WHERE state='retryable'")
            store.recover()
            assert not await w.step()

    asyncio.run(run())
    assert len(calls) == 1 and len(adapter.conversation.provider.prompts) == 3
    assert store.counts()["outbound"] == {"unknown": 1}
    assert store.counts()["inbound_queue"] == {"needs_reconciliation": 1}


@pytest.mark.parametrize(
    "code,status", [("sender_unbound", 403), ("selection_not_found", 404), ("provider_unavailable", 403)]
)
def test_authorization_or_scope_failure_never_becomes_user_feedback(delivery, code, status):
    adapter, store, payload, _ = delivery
    adapter.conversation.provider.error = ChannelError(code, "Synthetic private access failure", status)
    enqueue_payload(payload, adapter.bindings, store)

    async def handler(request):
        raise AssertionError("Access failures must stay silent")

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            w = WhatsAppWorker(
                adapter, store, MetaTransport(adapter.bindings, adapter.conversation.operations, store, client=client)
            )
            assert await w.step()
            assert not await w.step()

    asyncio.run(run())
    assert store.counts()["outbound"] == {} and store.counts()["inbound_queue"] == {"failed": 1}


@pytest.mark.parametrize("callback_order", ["before_decision", "after_snapshot"])
def test_callback_and_delivery_decision_resume_prepared_audio_after_restart(delivery, monkeypatch, callback_order):
    import threading
    from concurrent.futures import ThreadPoolExecutor

    import cyberpunks.channels.whatsapp_worker as worker_module
    from cyberpunks.channels.whatsapp import Inbox, WhatsAppAdapter

    adapter, store, payload, _ = opt_in_voice(delivery)
    enqueue_payload(payload, adapter.bindings, store)

    async def synthesize(text):
        return b"synthetic-mp3-not-real-speech"

    async def encode(mp3):
        return b"OggS-synthetic-OpusHead-not-real-speech"

    monkeypatch.setattr(adapter.transcriber, "synthesize", synthesize)
    monkeypatch.setattr(worker_module, "voice_note", encode)
    text_posts = []
    audio_posts = []
    uploads = []

    async def handler(request):
        if request.url.path.endswith("/media"):
            uploads.append(request)
            return httpx.Response(200, json={"id": "987654"})
        body = json.loads(request.content)
        if body["type"] == "text":
            text_posts.append(body)
            raise httpx.ReadTimeout("Synthetic initial text response lost", request=request)
        audio_posts.append(body)
        return httpx.Response(200, json={"messages": [{"id": "wamid.resumed-audio"}]})

    callback_store = DeliveryStore(store.path)
    callback_attempted = threading.Event()
    callback_finished = threading.Event()
    original_callback_connect = callback_store.connect

    def callback_connect():
        connection = original_callback_connect()
        connection.set_trace_callback(lambda sql: callback_attempted.set() if sql == "BEGIN IMMEDIATE" else None)
        return connection

    monkeypatch.setattr(callback_store, "connect", callback_connect)

    def callback():
        try:
            body = text_posts[0]
            callback_store.reconcile(
                "123456789",
                {
                    "id": "wamid.text-delivered-after-timeout",
                    "recipient_id": body["to"],
                    "status": "delivered",
                    "biz_opaque_callback_data": body["biz_opaque_callback_data"],
                },
            )
        finally:
            callback_finished.set()

    original_connect = store.connect
    original_decision = store.record_delivery
    decision_active = False
    fired = []
    snapshot_locks = []
    completed_while_locked = []
    futures = []
    with ThreadPoolExecutor(max_workers=1) as pool:

        def traced_connect():
            connection = original_connect()
            if decision_active:

                def trace(sql):
                    if fired:
                        return
                    if callback_order == "before_decision" and sql == "BEGIN IMMEDIATE":
                        fired.append(True)
                        future = pool.submit(callback)
                        futures.append(future)
                        # Callback commits while the worker has not acquired its write lock yet.
                        future.result(timeout=3)
                    elif (
                        callback_order == "after_snapshot"
                        and sql.startswith("UPDATE inbound_queue SET state=")
                        and "needs_reconciliation" in sql
                    ):
                        fired.append(True)
                        snapshot_locks.append(connection.in_transaction)
                        future = pool.submit(callback)
                        futures.append(future)
                        callback_attempted.wait(timeout=3)
                        # Force the old vulnerable gap: the status snapshot has been read, but
                        # the queue UPDATE has not executed. The callback must wait on this lock.
                        completed_while_locked.append(callback_finished.wait(timeout=0.15))

                connection.set_trace_callback(trace)
            return connection

        def traced_decision(eid):
            nonlocal decision_active
            decision_active = True
            try:
                return original_decision(eid)
            finally:
                decision_active = False

        monkeypatch.setattr(store, "connect", traced_connect)
        monkeypatch.setattr(store, "record_delivery", traced_decision)

        async def run():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                first = WhatsAppWorker(
                    adapter,
                    store,
                    MetaTransport(adapter.bindings, adapter.conversation.operations, store, client=client),
                )
                assert await first.step()
                assert len(fired) == 1
                for future in futures:
                    future.result(timeout=3)
                assert store.counts()["outbound"] == {"delivered": 1, "prepared": 1}
                assert store.counts()["inbound_queue"] == {"queued": 1}
                # New objects read only persisted results after an actual connection restart.
                restarted_store = DeliveryStore(store.path)
                restarted_store.recover()
                restarted_adapter = WhatsAppAdapter(
                    adapter.conversation,
                    adapter.bindings,
                    Inbox(store.path),
                    media_factory=adapter.media_factory,
                    transcriber=adapter.transcriber,
                )
                restarted = WhatsAppWorker(
                    restarted_adapter,
                    restarted_store,
                    MetaTransport(adapter.bindings, adapter.conversation.operations, restarted_store, client=client),
                )
                assert await restarted.step()
                assert not await restarted.step()
                assert restarted_store.counts()["outbound"] == {"delivered": 1, "accepted": 1}
                assert restarted_store.counts()["inbound_queue"] == {"accepted": 1}

        asyncio.run(run())
    assert len(text_posts) == len(audio_posts) == len(uploads) == 1
    assert len(adapter.conversation.provider.prompts) == 1
    if callback_order == "after_snapshot":
        assert snapshot_locks == [True] and completed_while_locked == [False]
        assert callback_attempted.is_set() and callback_finished.is_set()


def test_restart_rechecks_waiting_queue_but_does_not_retry_unknown_parts(delivery):
    _, store, _, _ = delivery
    event = incoming(delivery)
    text = store.prepare(event["event_id"], event["destination"], event["sender"], "text", b"text")
    store.prepare(event["event_id"], event["destination"], event["sender"], "audio", b"audio")
    store.outbound_state(text["part_id"], "unknown")
    store.queue_state(event["event_id"], "needs_reconciliation")
    store.recover()
    assert store.counts()["inbound_queue"] == {"needs_reconciliation": 1}
    assert store.next() is None
    # A previous version could leave this resolved snapshot waiting forever. Restart repairs
    # only the scheduling decision; it neither sends nor rewrites the provider outcome.
    store.outbound_state(text["part_id"], "delivered", message_id="wamid.persisted-delivery")
    store.recover()
    assert store.counts()["inbound_queue"] == {"queued": 1}
    assert store.counts()["outbound"] == {"delivered": 1, "prepared": 1}
