"""Actual image outbox and worker, with explicitly simulated Meta and conversation."""

import asyncio
import io
import json

import httpx
import pytest
from PIL import Image

from cyberpunks.channels.whatsapp_transport import MetaTransport
from cyberpunks.channels.whatsapp_worker import WhatsAppWorker

from .conftest import intention
from .test_whatsapp_delivery import delivery as delivery_fixture
from .test_whatsapp_delivery import incoming


@pytest.fixture
def delivery(env, monkeypatch):
    return delivery_fixture.__wrapped__(env, monkeypatch)


def png():
    output = io.BytesIO()
    Image.new("RGB", (20, 20), "yellow").save(output, format="PNG")
    return output.getvalue()


def test_multiple_image_parts_are_durable_and_never_resent(delivery):
    adapter, store, _, _ = delivery
    event = incoming(delivery)
    calls = []

    async def handler(request):
        calls.append(request)
        if request.url.path.endswith("/media"):
            return httpx.Response(200, json={"id": "54321"})
        data = json.loads(request.content)
        assert data["type"] == "image" and data["to"] == event["sender"]
        return httpx.Response(200, json={"messages": [{"id": f"wamid.image-{len(calls)}"}]})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            transport = MetaTransport(adapter.bindings, adapter.conversation.operations, store, client=client)
            for key in ("report_001", "report_002", "report_001", "report_002"):
                assert await transport.send(event, image=png(), image_key=key) == "accepted"

    asyncio.run(run())
    assert len(calls) == 4
    pages = store.prepared_images(event["event_id"])
    assert len(pages) == 2 and all(bytes(p["payload"]) == png() for p in pages)


def test_unknown_image_send_is_not_retried(delivery):
    adapter, store, _, _ = delivery
    event = incoming(delivery)
    calls = []

    async def handler(request):
        calls.append(request)
        if request.url.path.endswith("/media"):
            return httpx.Response(200, json={"id": "54321"})
        raise httpx.ReadTimeout("synthetic timeout")

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            transport = MetaTransport(adapter.bindings, adapter.conversation.operations, store, client=client)
            assert await transport.send(event, image=png(), image_key="report_001") == "unknown"
            assert await transport.send(event, image=png(), image_key="report_001") == "unknown"

    asyncio.run(run())
    assert len(calls) == 2


@pytest.mark.parametrize("render_fails", [False, True])
def test_worker_generates_real_report_for_explicit_inbound_request(env, delivery, monkeypatch, render_fails):
    adapter, store, _payload, message = delivery
    if render_fails:

        def unavailable(_pages):
            raise RuntimeError("Synthetic renderer outage")

        monkeypatch.setattr("cyberpunks.agentic.png_renderer.render_pages", unavailable)
    operations = env["operations"]
    actor = env["actors"]["customer"]
    proposal = operations.prepare(
        actor,
        "create_case",
        {
            "connection_id": actor.connection_ids[0],
            "symptom": "Synthetic report acceptance inverter",
            "symptom_type": "voltage",
        },
        "demo-vara",
    )
    operations.confirm(actor, proposal["proposal_id"])
    env["provider"].output = intention(kind="task", reply="Preparing case report")
    env["provider"].output.task_goal = "case_brief"
    message["text"]["body"] = "Trimite un raport imagine pentru sesizarea mea"
    event = incoming(delivery)
    assert event
    store.queue_state(event["event_id"], "queued")
    calls = []

    async def handler(request):
        calls.append(request)
        if request.url.path.endswith("/media"):
            assert b"image/png" in request.content
            return httpx.Response(200, json={"id": "54321"})
        return httpx.Response(200, json={"messages": [{"id": f"wamid.report-{len(calls)}"}]})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            worker = WhatsAppWorker(adapter, store, MetaTransport(adapter.bindings, operations, store, client=client))
            assert await worker.step()

    asyncio.run(run())
    assert len(calls) == (1 if render_fails else 3)
    if render_fails:
        assert "image could not be prepared" in json.loads(calls[0].content)["text"]["body"]
        assert not store.prepared_images(event["event_id"])
        return
    pages = store.prepared_images(event["event_id"])
    assert len(pages) == 1 and bytes(pages[0]["payload"]).startswith(b"\x89PNG")
    assert store.report_version(event["event_id"])
    assert len(env["provider"].prompts) == 1


def test_report_case_version_is_rechecked_before_network(env, delivery, monkeypatch):
    from hashlib import sha256

    from cyberpunks.channels.models import ChannelError

    adapter, store, _, _ = delivery
    event = incoming(delivery)
    actor = env["actors"]["customer"]
    context = env["operations"].context(actor, "demo-vara")
    image = png()
    store.prepare_report(
        event["event_id"],
        event["destination"],
        event["sender"],
        "synthetic-case-report",
        context["plan"]["version"],
        [{"png": image, "sha256": sha256(image).hexdigest(), "page": 1}],
        case_versions={"synthetic-case": 1},
    )

    async def handler(_request):
        pytest.fail("A changed case must be refused before upload or send")

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            transport = MetaTransport(adapter.bindings, env["operations"], store, client=client)
            with pytest.raises(ChannelError, match="report source changed"):
                await transport.send(event, image=image, image_key="synthetic-case-report_001")

    asyncio.run(run())
