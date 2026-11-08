"""Explicit private-demo voice followups, grounded in a real WhatsApp receipt.

The caller verifies the configured private demo identity and explicit send intent.
``authorize_actor()`` must return the currently authorized effective Actor, or raise.
No inbound receipt, timestamp, binding or delivery outcome is fabricated here.
"""

from __future__ import annotations

import asyncio
import hashlib
import json

from cyberpunks.agentic.contracts import TaskRequest
from cyberpunks.agentic.coordinator import AgenticCoordinator
from cyberpunks.agentic.pdf_renderer import render_pdf
from cyberpunks.agentic.pdf_report import pdf_pages, report_filename
from cyberpunks.agentic.report_data import build_report_data
from cyberpunks.agentic.task_store import TaskStore
from cyberpunks.channels.models import ChannelError
from cyberpunks.channels.whatsapp_store import actor_key
from cyberpunks.channels.whatsapp_transport import MetaTransport
from cyberpunks.channels.whatsapp_worker import worker

SCENARIO = "demo-vara"
GOALS = {"technician": "route_brief", "dispatcher": "analyze_queue", "customer": "case_brief"}


class _DemoBindings:
    """Per-send adapter only; the durable WhatsApp binding stays untouched."""

    def __init__(self, instance, operations, actor, incoming, authorize_actor):
        self.instance, self.operations, self.actor = instance, operations, actor
        self.incoming, self.authorize_actor = incoming, authorize_actor

    def resolve(self, destination, sender, *, with_options=False):
        if (destination, sender) != (self.incoming["destination"], self.incoming["sender"]):
            raise ChannelError("sender_binding_changed", "The recipient changed.", 403)
        original, options = self.instance.adapter.bindings.resolve(destination, sender, with_options=True)
        if actor_key(original) != self.incoming["actor_signature"]:
            raise ChannelError("sender_binding_changed", "The original binding changed.", 403)
        self.instance.adapter.conversation.operations.context(original, SCENARIO)
        effective = self.authorize_actor()
        if effective is None or actor_key(effective) != actor_key(self.actor):
            raise ChannelError("demo_actor_changed", "The private demo authorization changed.", 403)
        self.operations.context(effective, SCENARIO)
        return (effective, options) if with_options else effective


def _result(state, *, code=None):
    replies = {
        "accepted": "WhatsApp a acceptat raportul PDF. Livrarea nu este încă confirmată.",
        "delivered": "Raportul PDF a fost livrat pe WhatsApp.",
        "read": "Raportul PDF a fost livrat și citit pe WhatsApp.",
        "unknown": "Nu pot confirma trimiterea raportului. Nu îl retrimit, ca să evit un duplicat.",
        "sending": "Trimiterea raportului este în curs. Nu îl retrimit.",
    }
    return {
        "status": state,
        "reply": replies.get(state, "Raportul PDF nu a fost trimis pe WhatsApp."),
        **({"error_code": code} if code else {}),
    }


async def send_voice_report(
    operations, actor, *, caller: str, destination: str, event_key: str, authorize_actor: callable
) -> dict:
    """Send only after explicit voice consent, using the worker's durable ledger.

    An event freezes its real receipt and PDF. Unknown/in-flight outcomes are never
    retried; subsequent invocations reuse bytes and consult the same outbound row.
    """
    try:
        if not all(isinstance(v, str) and v.strip() for v in (caller, destination, event_key)):
            raise ChannelError("voice_report_invalid", "A verified event and recipient are required.", 422)
        if actor.role not in GOALS:
            raise ChannelError("voice_report_forbidden", "Unsupported role.", 403)
        instance = worker()
        store = instance.store
        eid = hashlib.sha256(("voice-report:" + event_key).encode()).hexdigest()
        signature = actor_key(actor)
        # This separate reference never enters the worker's inbound queue. It points
        # at an actual receipt and preserves that receipt even if newer messages arrive.
        with store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "CREATE TABLE IF NOT EXISTS voice_report_sources "
                "(event_id TEXT PRIMARY KEY, source_event_id TEXT NOT NULL, actor_signature TEXT NOT NULL)"
            )
            saved = db.execute("SELECT * FROM voice_report_sources WHERE event_id=?", (eid,)).fetchone()
            if saved:
                if saved["actor_signature"] != signature:
                    raise ChannelError("demo_actor_changed", "The report actor changed.", 403)
                row = db.execute(
                    "SELECT * FROM inbound_queue WHERE event_id=? AND sender=? AND destination=?",
                    (saved["source_event_id"], caller, destination),
                ).fetchone()
            else:
                row = db.execute(
                    "SELECT * FROM inbound_queue WHERE sender=? AND destination=? "
                    "ORDER BY created DESC,event_id DESC LIMIT 1",
                    (caller, destination),
                ).fetchone()
                if row:
                    db.execute("INSERT INTO voice_report_sources VALUES(?,?,?)", (eid, row["event_id"], signature))
            if row is None:
                raise ChannelError("real_inbound_required", "A real matching WhatsApp receipt is required.", 403)
        original = dict(row)
        original["message"] = json.loads(original["message"])
        bindings = _DemoBindings(instance, operations, actor, original, authorize_actor)
        bindings.resolve(destination, caller)
        incoming = {**original, "event_id": eid, "actor_signature": signature}
        transport = MetaTransport(bindings, operations, store, client=instance.transport.client)
        transport.authorize(incoming)
        manifest = store.report_manifest(eid)
        if not manifest:
            context = operations.context(actor, SCENARIO)
            if actor.role == "customer" and not context.get("cases"):
                return {"status": "no_case", "reply": "Nu ai o sesizare disponibilă pentru raport. Nu am trimis nimic."}
            case_id = None
            if actor.role == "customer":
                # A generic spoken request refers to the latest owned case.
                latest = max(context["cases"], key=lambda case: (case.get("created_at", ""), case["case_id"]))
                case_id = latest["case_id"]
            task = AgenticCoordinator(operations, TaskStore(operations.db_path.with_name("agentic-tasks.sqlite3"))).run(
                actor, TaskRequest(goal=GOALS[actor.role], case_id=case_id, request_key="voice-report:" + eid)
            )
            if task.status != "completed":
                return {
                    "status": "not_ready",
                    "reply": task.reply or "Raportul nu este disponibil. Nu am trimis nimic.",
                }
            context = operations.context(actor, SCENARIO)
            if context["plan"]["version"] != task.plan_version:
                raise ChannelError("report_stale", "The plan changed.", 409)
            cases = {c["case_id"]: c.get("version") for c in task.result.get("cases", [])}
            if actor.role == "technician":
                from cyberpunks.channels.voice_briefs import trusted_next_stop

                _, remaining, _, by_id = trusted_next_stop(context, actor)
                remaining_ids = {stop["work_item_id"] for stop in remaining}
                routes = []
                for route in task.result["routes"]:
                    stops = []
                    for stop in route["stops"]:
                        if stop["work_item_id"] not in remaining_ids:
                            continue
                        location = by_id[stop["work_item_id"]].get("location") or {}
                        stops.append(
                            {**stop, "title": location.get("address") or location.get("label") or stop["title"]}
                        )
                    routes.append({**route, "stops": stops})
                context = {**context, "plan": {**context["plan"], "routes": routes}}
            if actor.role == "customer":
                context = {**context, "cases": task.result["cases"]}
            data = build_report_data(context, task.result if actor.role == "dispatcher" else None, "ro")
            pages = pdf_pages(data)
            if not 1 <= len(pages) <= 32:
                raise ChannelError("report_too_large", "Report page limit exceeded.", 422)
            rendered = await asyncio.to_thread(render_pdf, pages)
            transport.authorize(incoming)
            fresh = operations.context(actor, SCENARIO)
            current_cases = {c["case_id"]: c.get("version") for c in fresh.get("cases", [])}
            if fresh["plan"]["version"] != task.plan_version or any(
                current_cases.get(k) != v for k, v in cases.items()
            ):
                raise ChannelError("report_stale", "The source changed.", 409)
            manifest = store.prepare_report_pdf(
                eid,
                destination,
                caller,
                "voice_" + eid,
                task.plan_version,
                rendered["pdf"],
                sha256=rendered["sha256"],
                page_count=rendered["page_count"],
                source_pages=rendered["source_pages"],
                filename=report_filename(data),
                case_versions=cases,
            )
        documents = store.prepared_documents(eid)
        if len(documents) != 1 or documents[0]["kind"] != manifest["part_kind"]:
            raise ChannelError("outbound_conflict", "Missing frozen report.", 409)
        part = documents[0]
        transport.authorize(incoming)
        if part["state"] != "prepared":
            return _result(part["state"])
        state = await transport.send(
            incoming, document=bytes(part["payload"]), document_key=part["kind"][9:], document_name=manifest["filename"]
        )
        return _result(state)
    except ChannelError as exc:
        result = _result("error", code=exc.code)
        if exc.code == "reply_window_expired":
            result["reply"] = (
                "Fereastra WhatsApp a expirat. Trimite un mesaj nou pe WhatsApp ca să pot răspunde cu raportul."
            )
        return result
    except Exception:  # noqa: BLE001 - private diagnostics never become speech.
        return _result("error", code="voice_report_unavailable")
