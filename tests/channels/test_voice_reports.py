"""Synthetic receipts and fake Meta network; complete fresh operational copy."""

import asyncio
import hashlib
import os
import shutil
import time
from html import escape
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from cyberpunks.channels import voice_reports as reports
from cyberpunks.channels.whatsapp_store import DeliveryStore
from cyberpunks.operations.models import Actor
from cyberpunks.operations.service import OperationsService
from cyberpunks.planner import feedback


@pytest.fixture
def demo(tmp_path, monkeypatch, full_run):
    source = Path(os.environ.get("DAYBREAK_OPERATIONS_TEST_DATA", full_run))
    target = tmp_path / "synthetic-full-copy"
    shutil.copytree(source, target)
    operations = OperationsService(target, tmp_path / "synthetic.sqlite3")
    b = operations.demo_bindings()
    base = {"organization_id": b["organization_id"]}
    actors = {
        "technician": Actor(user_id="synthetic-tech", role="technician", crew_id=b["crew_id"], **base),
        "dispatcher": Actor(user_id="synthetic-dispatch", role="dispatcher", permissions=b["permissions"], **base),
        "customer": Actor(user_id="synthetic-client", role="customer", connection_ids=b["connection_ids"], **base),
    }
    feedback.approve_route("demo-vara", b["crew_id"], "synthetic-reviewer", out_root=target)
    store = DeliveryStore(tmp_path / "synthetic-whatsapp.sqlite3")
    binding = [actors["technician"]]

    class Bindings:
        def resolve(self, destination, sender, *, with_options=False):
            return (binding[0], {}) if with_options else binding[0]

    posts = []

    def network(request):
        posts.append(request)
        if request.url.path.endswith("/media"):
            return httpx.Response(200, json={"id": "123"})
        return httpx.Response(200, json={"messages": [{"id": "wamid.synthetic"}]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(network))
    instance = SimpleNamespace(
        store=store,
        transport=SimpleNamespace(client=client),
        adapter=SimpleNamespace(bindings=Bindings(), conversation=SimpleNamespace(operations=operations)),
    )
    monkeypatch.setattr(reports, "worker", lambda: instance)
    monkeypatch.setattr(
        "cyberpunks.channels.whatsapp_transport.require_sending",
        lambda: {"DAYBREAK_META_GRAPH_VERSION": "v25.0", "DAYBREAK_META_ACCESS_TOKEN": "synthetic-not-a-secret"},
    )
    monkeypatch.setattr("cyberpunks.channels.whatsapp_transport.require_destination", lambda _: None)
    renders = []

    def render(pages):
        renders.append(pages)
        pdf = b"%PDF-1.4\nsynthetic-test-only\n%%EOF"
        return {"pdf": pdf, "sha256": hashlib.sha256(pdf).hexdigest(), "page_count": 1, "source_pages": len(pages)}

    monkeypatch.setattr(reports, "render_pdf", render)

    def receipt(sender="synthetic-caller", destination="synthetic-destination", age=1, key="synthetic-inbound"):
        message = {
            "id": key,
            "timestamp": str(int(time.time()) - age),
            "type": "text",
            "text": {"body": "Synthetic test receipt"},
        }
        store.enqueue(destination, sender, message, binding[0])
        return message

    def send(role="dispatcher", key="synthetic-call", authorize=None, caller="synthetic-caller"):
        return asyncio.run(
            reports.send_voice_report(
                operations,
                actors[role],
                caller=caller,
                destination="synthetic-destination",
                event_key=key,
                authorize_actor=authorize or (lambda: actors[role]),
            )
        )

    return SimpleNamespace(**locals())


@pytest.mark.parametrize("role", ["dispatcher", "technician"])
def test_role_report_frozen_resume_and_no_double(demo, role):
    receipt = demo.receipt()
    assert demo.send(role)["status"] == "accepted"
    assert len(demo.posts) == 2
    assert demo.binding[0].role == "technician"
    assert demo.send(role)["status"] == "accepted"
    assert len(demo.posts) == 2 and len(demo.renders) == 1
    with demo.store.connect() as db:
        rows = db.execute("SELECT message FROM inbound_queue").fetchall()
        assert len(rows) == 1
        assert receipt["timestamp"] in rows[0][0]
    assert "Livrarea nu este încă confirmată" in demo.send(role)["reply"]


def test_expired_receipt_never_extends_window(demo):
    demo.receipt(age=24 * 3600)
    result = demo.send()
    assert result["error_code"] == "reply_window_expired"
    assert not demo.posts and not demo.renders


def test_latest_matching_original_recipient_only(demo):
    demo.receipt(age=24 * 3600, key="synthetic-old")
    demo.receipt(sender="synthetic-other", key="synthetic-other")
    assert demo.send()["error_code"] == "reply_window_expired"
    demo.receipt(key="synthetic-new")
    assert demo.send(key="synthetic-next-call")["status"] == "accepted"


def test_missing_receipt_and_effective_actor_denied(demo):
    assert demo.send()["error_code"] == "real_inbound_required"
    demo.receipt()
    assert demo.send(authorize=lambda: demo.actors["customer"])["error_code"] == "demo_actor_changed"
    assert not demo.posts


def test_original_binding_revoked(demo):
    demo.receipt()
    demo.binding[0] = demo.actors["customer"]
    assert demo.send()["error_code"] == "sender_binding_changed"
    assert not demo.posts


def test_recheck_actor_after_upload_before_message_post(demo):
    demo.receipt()

    def authorize():
        return demo.actors["customer"] if demo.posts else demo.actors["dispatcher"]

    assert demo.send(authorize=authorize)["error_code"] == "demo_actor_changed"
    assert len(demo.posts) == 1 and demo.posts[0].url.path.endswith("/media")
    # Safe upload interruption resumes the saved bytes, without rendering again.
    assert demo.send()["status"] == "accepted"
    assert len(demo.renders) == 1


def test_unknown_outcome_never_reposted(demo):
    demo.receipt()

    async def broken(request):
        demo.posts.append(request)
        if request.url.path.endswith("/media"):
            return httpx.Response(200, json={"id": "123"})
        raise httpx.ReadTimeout("synthetic failure")

    demo.client._transport = httpx.MockTransport(broken)
    assert demo.send()["status"] == "unknown"
    assert demo.send()["status"] == "unknown"
    assert len(demo.posts) == 2 and len(demo.renders) == 1


def test_customer_without_case_explains_without_send(demo):
    demo.receipt()
    context = demo.operations.context(demo.actors["customer"])
    assert not context["cases"]
    assert demo.send("customer")["status"] == "no_case"
    assert not demo.posts


def test_customer_report_selects_latest_owned_persisted_case(demo):
    from cyberpunks.channels.voice_briefs import answer_demo

    actor = demo.actors["customer"]
    connection = actor.connection_ids[0]
    for event in ("synthetic-first-incident", "synthetic-latest-incident"):
        result = answer_demo(
            demo.operations,
            actor,
            "Am rămas fără curent.",
            event_key=event,
            connection_id=connection,
            execute_incident=True,
        )
        assert result["command"]["status"] == "succeeded"
    demo.receipt()
    assert demo.send("customer")["status"] == "accepted"
    assert len(demo.posts) == 2 and len(demo.renders) == 1
    latest = result["command"]["result"]["case"]["case_id"]
    assert latest in "".join(demo.renders[0])


def test_technician_pdf_matches_remaining_stops_and_includes_verified_place(demo):
    actor = demo.actors["technician"]
    before = demo.operations.context(actor)
    first = before["next_stop"]["work_item_id"]
    proposal = demo.operations.prepare(actor, "record_verdict", {"work_item_id": first, "outcome": "not_found"})
    demo.operations.confirm(actor, proposal["proposal_id"])
    current = demo.operations.context(actor)
    next_id = current["next_stop"]["work_item_id"]
    item = next(item for item in current["work_items"] if item["work_item_id"] == next_id)
    label = item["location"].get("address") or item["location"]["label"]
    demo.receipt()
    assert demo.send("technician")["status"] == "accepted"
    html = "".join(demo.renders[0])
    assert escape(label, quote=True) in html
    from cyberpunks.channels.voice_briefs import trusted_next_stop

    _, remaining, _, _ = trusted_next_stop(current, actor)
    assert f"{len(remaining)} opriri" in html


def test_window_expires_during_upload_no_post_or_fresh_receipt_reuse(demo, monkeypatch):
    demo.receipt()
    start = time.time()
    monkeypatch.setattr(
        "cyberpunks.channels.whatsapp_transport.time.time", lambda: start + (24 * 3600 if demo.posts else 0)
    )
    assert demo.send()["error_code"] == "reply_window_expired"
    assert len(demo.posts) == 1
    # A newer real receipt does not refresh a previously frozen voice event.
    demo.receipt(key="synthetic-newer")
    assert demo.send()["error_code"] == "reply_window_expired"
    assert len(demo.posts) == 1 and len(demo.renders) == 1
