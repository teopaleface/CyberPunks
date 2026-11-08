"""Actual image outbox and worker, with explicitly simulated Meta and conversation."""

import asyncio
import io
import json
import shutil
import time
from hashlib import sha256

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


# --- PDF reports -------------------------------------------------------------------------------


def pdf_report(pages=1, label="synthetic"):
    from cyberpunks.agentic.pdf_renderer import describe_pdf

    body = f"%PDF-1.7\n% {label}\n/Type /Page\n" * pages + "%%EOF\n"
    return describe_pdf(body.encode(), source_pages=pages)


def prepare_pdf(delivery, env, event, report=None, case_versions=None):
    _, store, _, _ = delivery
    report = report or pdf_report()
    context = env["operations"].context(env["actors"]["customer"], "demo-vara")
    manifest = store.prepare_report_pdf(
        event["event_id"],
        event["destination"],
        event["sender"],
        "synthetic-case-report",
        context["plan"]["version"],
        report["pdf"],
        sha256=report["sha256"],
        page_count=report["page_count"],
        case_versions=case_versions,
    )
    return report, manifest


def test_pdf_manifest_and_exact_bytes_commit_atomically(env, delivery):
    _, store, _, _ = delivery
    event = incoming(delivery)
    report, manifest = prepare_pdf(delivery, env, event)
    assert manifest["mime"] == "application/pdf" and manifest["sha256"] == report["sha256"]
    assert manifest["filename"].startswith("daybreak-raport-synthetic-case-report-") and manifest["filename"].endswith(
        ".pdf"
    )
    assert store.report_manifest(event["event_id"]) == manifest
    [document] = store.prepared_documents(event["event_id"])
    assert bytes(document["payload"]) == report["pdf"] and document["payload_hash"] == report["sha256"]
    assert document["state"] == "prepared" and not store.prepared_images(event["event_id"])
    # An identical second preparation is a no-op that returns the first manifest and bytes.
    _, same = prepare_pdf(delivery, env, event, pdf_report(label="other bytes"))
    assert same == manifest
    assert [bytes(d["payload"]) for d in store.prepared_documents(event["event_id"])] == [report["pdf"]]


def test_pdf_preparation_refuses_tampering_and_leaves_no_partial_rows(env, delivery):
    from cyberpunks.channels.models import ChannelError

    _, store, _, _ = delivery
    event = incoming(delivery)
    report = pdf_report()
    version = env["operations"].context(env["actors"]["customer"], "demo-vara")["plan"]["version"]
    args = (event["event_id"], event["destination"], event["sender"], "synthetic-case-report", version)
    with pytest.raises(ChannelError, match="integrity"):
        store.prepare_report_pdf(*args, report["pdf"], sha256="0" * 64, page_count=1)
    with pytest.raises(ChannelError, match="integrity"):
        store.prepare_report_pdf(*args, b"not a pdf", sha256=sha256(b"not a pdf").hexdigest(), page_count=1)
    assert store.report_manifest(event["event_id"]) is None and store.report_version(event["event_id"]) is None
    assert not store.prepared_documents(event["event_id"])
    prepare_pdf(delivery, env, event, report)
    with pytest.raises(ChannelError, match="source changed"):
        store.prepare_report_pdf(
            event["event_id"],
            event["destination"],
            event["sender"],
            "synthetic-case-report",
            "another-version",
            report["pdf"],
            sha256=report["sha256"],
            page_count=1,
        )
    # A PNG report cannot silently replace the PDF report of the same message, or the reverse.
    image = png()
    with pytest.raises(ChannelError, match="source changed"):
        store.prepare_report(
            event["event_id"],
            event["destination"],
            event["sender"],
            "synthetic-case-report",
            version,
            [{"png": image, "sha256": sha256(image).hexdigest(), "page": 1}],
        )


def test_pdf_is_uploaded_as_application_pdf_with_filename_and_never_resent(env, delivery):
    adapter, store, _, _ = delivery
    event = incoming(delivery)
    report, manifest = prepare_pdf(delivery, env, event)
    calls = []

    async def handler(request):
        calls.append(request)
        if request.url.path.endswith("/media"):
            assert b'name="type"' in request.content and b"application/pdf" in request.content
            assert f'filename="{manifest["filename"]}"'.encode() in request.content
            assert report["pdf"] in request.content
            return httpx.Response(200, json={"id": "98765"})
        data = json.loads(request.content)
        assert data["type"] == "document" and data["to"] == event["sender"]
        assert data["document"] == {"id": "98765", "filename": manifest["filename"]}
        assert data["context"]["message_id"] == event["message"]["id"]
        return httpx.Response(200, json={"messages": [{"id": "wamid.pdf-1"}]})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            transport = MetaTransport(adapter.bindings, env["operations"], store, client=client)
            for _ in range(3):
                state = await transport.send(
                    event,
                    document=report["pdf"],
                    document_key="synthetic-case-report_pdf",
                    document_name=manifest["filename"],
                )
                assert state == "accepted"

    asyncio.run(run())
    assert len(calls) == 2


def test_unknown_pdf_send_is_not_retried_and_media_is_not_reuploaded(env, delivery):
    adapter, store, _, _ = delivery
    event = incoming(delivery)
    report, manifest = prepare_pdf(delivery, env, event)
    calls = []

    async def handler(request):
        calls.append(request)
        if request.url.path.endswith("/media"):
            return httpx.Response(200, json={"id": "98765"})
        raise httpx.ReadTimeout("synthetic timeout")

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            transport = MetaTransport(adapter.bindings, env["operations"], store, client=client)
            for _ in range(2):
                assert (
                    await transport.send(
                        event,
                        document=report["pdf"],
                        document_key="synthetic-case-report_pdf",
                        document_name=manifest["filename"],
                    )
                    == "unknown"
                )

    asyncio.run(run())
    assert len(calls) == 2


def test_pdf_send_refuses_invalid_documents_and_manifest_mismatch_before_network(env, delivery):
    from cyberpunks.channels.models import ChannelError

    adapter, store, _, _ = delivery
    event = incoming(delivery)
    report, manifest = prepare_pdf(delivery, env, event)

    async def handler(_request):
        pytest.fail("An invalid or mismatched PDF must be refused before any network call")

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            transport = MetaTransport(adapter.bindings, env["operations"], store, client=client)
            good = {"document_key": "synthetic-case-report_pdf", "document_name": manifest["filename"]}
            for document, extra, code in (
                (png(), good, "outbound_invalid"),
                (report["pdf"], {**good, "document_name": "../escape.pdf"}, "outbound_invalid"),
                (report["pdf"], {**good, "document_name": "report.png"}, "outbound_invalid"),
                (report["pdf"], {**good, "document_key": "bad key"}, "outbound_invalid"),
                (report["pdf"], {**good, "document_name": "daybreak-other.pdf"}, "outbound_conflict"),
                (pdf_report(label="changed")["pdf"], good, "outbound_conflict"),
            ):
                with pytest.raises(ChannelError) as caught:
                    await transport.send(event, document=document, **extra)
                assert caught.value.code == code
            with pytest.raises(ChannelError, match="exactly one"):
                await transport.send(event, text="x", document=report["pdf"], **good)

    asyncio.run(run())


def test_pdf_send_requires_a_prepared_report_manifest(env, delivery):
    from cyberpunks.channels.models import ChannelError

    adapter, store, _, _ = delivery
    event = incoming(delivery)
    report = pdf_report()
    assert store.report_manifest(event["event_id"]) is None

    async def handler(_request):
        pytest.fail("A PDF without a frozen report manifest must never reach the network")

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            transport = MetaTransport(adapter.bindings, env["operations"], store, client=client)
            with pytest.raises(ChannelError) as caught:
                await transport.send(
                    event, document=report["pdf"], document_key="loose_pdf", document_name="daybreak-loose.pdf"
                )
            assert caught.value.code == "outbound_conflict"
            # A prepared manifest still binds the document key, not only hash and filename.
            _, manifest = prepare_pdf(delivery, env, event, report)
            with pytest.raises(ChannelError) as caught:
                await transport.send(
                    event, document=report["pdf"], document_key="another_pdf", document_name=manifest["filename"]
                )
            assert caught.value.code == "outbound_conflict"

    asyncio.run(run())
    assert not store.prepared_documents(event["event_id"]) or all(
        d["state"] == "prepared" for d in store.prepared_documents(event["event_id"])
    )


def test_pdf_send_rechecks_binding_window_and_report_version_before_network(env, delivery):
    from cyberpunks.channels.models import ChannelError

    adapter, store, _, _ = delivery
    event = incoming(delivery)
    report, manifest = prepare_pdf(delivery, env, event, case_versions={"synthetic-case": 1})
    kwargs = {
        "document": report["pdf"],
        "document_key": "synthetic-case-report_pdf",
        "document_name": manifest["filename"],
    }

    async def handler(_request):
        pytest.fail("A stale report, expired window or changed binding must be refused before the network")

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            transport = MetaTransport(adapter.bindings, env["operations"], store, client=client)
            with pytest.raises(ChannelError, match="report source changed"):
                await transport.send(event, **kwargs)
            expired = {**event, "message": {**event["message"], "timestamp": str(int(time.time()) - 24 * 3600)}}
            with pytest.raises(ChannelError) as caught:
                await transport.send(expired, **kwargs)
            assert caught.value.code == "reply_window_expired"
            changed = {**event, "actor_signature": "0" * 64}
            with pytest.raises(ChannelError) as caught:
                await transport.send(changed, **kwargs)
            assert caught.value.code == "sender_binding_changed"

    asyncio.run(run())


def customer_report_request(env, delivery, text):
    _, store, _payload, message = delivery
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
    message["text"]["body"] = text
    event = incoming(delivery)
    assert event
    store.queue_state(event["event_id"], "queued")
    return event


def run_worker_step(delivery, env, handler):
    adapter, store, _, _ = delivery

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            worker = WhatsAppWorker(
                adapter, store, MetaTransport(adapter.bindings, env["operations"], store, client=client)
            )
            assert await worker.step()

    asyncio.run(run())


@pytest.mark.parametrize("request_text", ["Trimite raportul pentru sesizarea mea", "Send me the case report as PDF"])
def test_worker_defaults_explicit_report_requests_to_real_pdf(env, delivery, request_text):
    _, store, _, _ = delivery
    event = customer_report_request(env, delivery, request_text)
    calls = []

    async def handler(request):
        calls.append(request)
        if request.url.path.endswith("/media"):
            assert b"application/pdf" in request.content and b"image/png" not in request.content
            return httpx.Response(200, json={"id": "54321"})
        return httpx.Response(200, json={"messages": [{"id": f"wamid.report-{len(calls)}"}]})

    run_worker_step(delivery, env, handler)
    assert [c.url.path.rsplit("/", 1)[-1] for c in calls] == ["messages", "media", "messages"]
    assert json.loads(calls[0].content)["type"] == "text"
    document = json.loads(calls[2].content)
    manifest = store.report_manifest(event["event_id"])
    assert document["type"] == "document" and document["document"]["filename"] == manifest["filename"]
    [stored] = store.prepared_documents(event["event_id"])
    pdf = bytes(stored["payload"])
    assert pdf.startswith(b"%PDF-") and sha256(pdf).hexdigest() == manifest["sha256"] == stored["payload_hash"]
    assert manifest["bytes"] == len(pdf) and manifest["page_count"] >= 1 and manifest["format"] == "pdf"
    assert stored["state"] == "accepted" and not store.prepared_images(event["event_id"])
    assert store.report_version(event["event_id"])
    assert len(env["provider"].prompts) == 1
    if shutil.which("pdftotext"):
        import subprocess
        from pathlib import Path

        target = Path(env["tmp"]) / "worker-report.pdf"
        target.write_bytes(pdf)
        text = subprocess.run(["pdftotext", str(target), "-"], capture_output=True, text=True, check=True).stdout
        assert "Starea sesizării" in text and "Include date sintetice" in text


def test_worker_keeps_png_for_explicit_image_requests_even_with_the_word_raport(env, delivery):
    _, store, _, _ = delivery
    event = customer_report_request(env, delivery, "Trimite raportul ca imagine PNG")
    kinds = []

    async def handler(request):
        if request.url.path.endswith("/media"):
            assert b"image/png" in request.content
            return httpx.Response(200, json={"id": "54321"})
        kinds.append(json.loads(request.content)["type"])
        return httpx.Response(200, json={"messages": [{"id": f"wamid.png-{len(kinds)}"}]})

    run_worker_step(delivery, env, handler)
    assert kinds == ["text", "image"]
    assert len(store.prepared_images(event["event_id"])) == 1 and not store.prepared_documents(event["event_id"])


def test_worker_pdf_renderer_failure_keeps_verified_text_and_names_the_pdf(env, delivery, monkeypatch):
    _, store, _, _ = delivery

    def unavailable(_pages):
        raise RuntimeError("Synthetic renderer outage")

    monkeypatch.setattr("cyberpunks.agentic.pdf_renderer.render_pdf", unavailable)
    event = customer_report_request(env, delivery, "Trimite raportul")
    calls = []

    async def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"messages": [{"id": "wamid.text-only"}]})

    run_worker_step(delivery, env, handler)
    assert len(calls) == 1
    assert "PDF" in json.loads(calls[0].content)["text"]["body"]
    assert not store.prepared_documents(event["event_id"]) and store.report_manifest(event["event_id"]) is None


def test_worker_restart_resumes_the_frozen_pdf_without_rendering_again(env, delivery, monkeypatch):
    """The first document POST outcome is unknown; the next worker pass sends nothing and renders nothing."""
    _, store, _, _ = delivery
    event = customer_report_request(env, delivery, "Trimite raportul")
    calls = []

    async def handler(request):
        calls.append(request)
        if request.url.path.endswith("/media"):
            return httpx.Response(200, json={"id": "54321"})
        if json.loads(request.content)["type"] == "document":
            raise httpx.ReadTimeout("synthetic timeout")
        return httpx.Response(200, json={"messages": [{"id": "wamid.text"}]})

    run_worker_step(delivery, env, handler)
    assert len(calls) == 3
    [first] = store.prepared_documents(event["event_id"])
    assert first["state"] == "unknown"
    manifest = store.report_manifest(event["event_id"])

    def forbidden(_pages):
        raise AssertionError("A frozen PDF must not be rendered again")

    monkeypatch.setattr("cyberpunks.agentic.pdf_renderer.render_pdf", forbidden)
    store.recover()
    store.queue_state(event["event_id"], "queued")
    adapter = delivery[0]

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            worker = WhatsAppWorker(
                adapter, store, MetaTransport(adapter.bindings, env["operations"], store, client=client)
            )
            await worker.step()

    asyncio.run(run())
    assert len(calls) == 3
    [after] = store.prepared_documents(event["event_id"])
    assert bytes(after["payload"]) == bytes(first["payload"]) and store.report_manifest(event["event_id"]) == manifest
