"""Worker WhatsApp local, serializat și reluabil. HTTP-ul confirmă doar coada durabilă."""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import portalocker

from cyberpunks.channels.elevenlabs import runtime_root
from cyberpunks.channels.models import ChannelError
from cyberpunks.channels.whatsapp import Bindings, Inbox, WhatsAppAdapter
from cyberpunks.channels.whatsapp_config import confirmation_text, require_sending
from cyberpunks.channels.whatsapp_store import DeliveryStore
from cyberpunks.channels.whatsapp_transport import MetaTransport, voice_note

# Only model/provenance failures can produce a controlled terminal reply. Authorization,
# object scope, binding and transport failures never opt in through a string prefix.
CONVERSATION_FAILURES = {
    "provider_protocol",
    "provider_failed",
    "provider_tool_violation",
    "provider_incomplete",
    "provider_schema",
    "provider_output_limit",
    "provider_auth_missing",
    "provider_unavailable",
    "provider_timeout",
    "ungrounded_reply",
    "unverified_effect",
    "assessment_unavailable",
    "invalid_intention",
}


def failure_response(message: dict) -> dict:
    text = message.get("text", {}).get("body", "") if message.get("type") == "text" else ""
    romanian = re.search(
        r"[ăâîșşțţ]|\b(de ce|mergem|urmatoarea|oprire|vreau|unde|cum|care|detalii|sesizare|buna|salut)\b",
        text,
        re.IGNORECASE,
    )
    english = re.search(
        r"\b(what|why|where|when|how|please|could|help|next|stop|case|report|hello|hi)\b", text, re.IGNORECASE
    )
    language = "en" if english and not romanian else "ro"
    reply = (
        "Nu pot verifica acum răspunsul din datele disponibile. Încearcă din nou sau verifică detaliile în aplicație."
        if language == "ro"
        else "I can't verify an answer from the available data right now. Please try again or check the details in the app."
    )
    return {
        "reply": reply,
        "proposal": None,
        "provider": "server-fallback",
        "language": language,
        "provenance": {
            "provider": "server-fallback",
            "write_executed": False,
            "tools_enabled": False,
            "evidence": [],
            "evidence_values_checked": False,
        },
    }


class WhatsAppWorker:
    def __init__(self, adapter: WhatsAppAdapter, store: DeliveryStore, transport: MetaTransport):
        self.adapter, self.store, self.transport = adapter, store, transport

    def audio_fallback(self, eid: str, result: dict, exc: Exception):
        code = exc.code if isinstance(exc, ChannelError) else "audio_preparation_failed"
        result.update(reply_type="text", audio_delivery="failed_text_fallback", audio_error_code=code)
        self.adapter.inbox.finish(eid, result)
        self.store.skip_prepared_audio(eid, code)

    def record_delivery(self, eid: str, state: str):
        # The transport result may be stale. Queue decisions and callback updates serialize
        # against the same outbox rows in SQLite, including prepared audio awaiting resume.
        queue_state = self.store.record_delivery(eid)
        status = {
            "accepted": "meta_accepted",
            "queued": "meta_partial_pending",
            "needs_reconciliation": "unknown_do_not_resend",
            "failed": "not_accepted",
        }[queue_state]
        self.adapter.inbox.outbound_status(eid, status)

    async def terminal_feedback(self, incoming: dict, failure: ChannelError):
        eid = incoming["event_id"]
        try:
            # Recheck the current binding, membership, reply window and both gates. No send for a
            # revoked/changed identity, even though it was valid when the message was enqueued.
            self.transport.authorize(incoming)
            if self.store.has_unresolved_send(eid):
                self.record_delivery(eid, "unknown")
                return
            response = failure_response(incoming["message"])
            text = response["reply"]
            stored = {
                "input_type": "text" if incoming["message"].get("type") == "text" else "voice_note",
                "input_text": incoming["message"].get("text", {}).get("body", "[Voice note]"),
                "reply_type": "text",
                "audio_reply_path": None,
                "response": response,
                "delivery_text": text,
                "outbound_status": "not_sent",
                "tts": "disabled_server_fallback",
                "failure_code": failure.code,
            }
            # Exact controlled text persists before the usual at-most-once transport. It contains
            # neither model output nor the exception message and never creates a proposal.
            self.adapter.inbox.finish(eid, stored)
            state = await self.transport.send(incoming, text=text)
            if state in {"accepted", "delivered", "read"}:
                for page in self.store.prepared_images(eid):
                    # Every send reauthorizes the current sender and inbound response window.
                    image_state = await self.transport.send(
                        incoming, image=bytes(page["payload"]), image_key=page["kind"][6:]
                    )
                    if image_state not in {"accepted", "delivered", "read"}:
                        state = image_state
                        break
            self.record_delivery(eid, state)
        except ChannelError as exc:
            self.store.queue_state(eid, "queued" if exc.code == "whatsapp_sending_disabled" else "failed", exc.code)
        except Exception:  # noqa: BLE001 - private failure diagnostics must never become user messages.
            self.store.queue_state(eid, "failed", "feedback_unavailable")

    async def prepare_report(self, incoming: dict, result: dict):
        """Prepare exact private PNG pages only for an explicit inbound report request."""
        if result.get("image_report_prepared") is not None:
            return
        task = result.get("response", {}).get("task")
        if (
            not task
            or task.get("status") != "completed"
            or not re.search(
                r"\b(raport|report|imagine|image|poz[ăa]|png)\b", result.get("input_text", ""), re.IGNORECASE
            )
        ):
            return
        try:
            self.transport.authorize(incoming)
            actor = self.adapter.bindings.resolve(incoming["destination"], incoming["sender"])
            context = self.adapter.conversation.operations.context(actor, task["scenario"])
            if context["plan"]["version"] != task["plan_version"]:
                raise ChannelError("report_stale", "The report source changed.", 409)
            supported = {"dispatcher": "analyze_queue", "technician": "route_brief", "customer": "case_brief"}
            if supported.get(actor.role) != task["goal"]:
                return
            if self.store.report_version(incoming["event_id"]):
                result["image_report_prepared"] = True
                self.adapter.inbox.finish(incoming["event_id"], result)
                return
            from cyberpunks.agentic.png_renderer import render_pages
            from cyberpunks.agentic.report_data import build_report_data
            from cyberpunks.agentic.report_templates import render_report

            case_versions = {case["case_id"]: case.get("version") for case in task["result"].get("cases", [])}
            current_cases = {case["case_id"]: case.get("version") for case in context.get("cases", [])}
            if any(current_cases.get(key) != version for key, version in case_versions.items()):
                raise ChannelError("report_stale", "The case changed.", 409)
            if actor.role == "technician":
                context = {**context, "plan": {**context["plan"], "routes": task["result"].get("routes", [])}}
            if actor.role == "customer":
                context = {**context, "cases": task["result"].get("cases", [])}
            data = build_report_data(
                context,
                task["result"] if actor.role == "dispatcher" else None,
                result["response"].get("language", "ro"),
            )
            html = render_report(data)
            if len(html) > 32:
                raise ChannelError("report_too_large", "Use the full report in the application.", 422)
            pages = await asyncio.to_thread(render_pages, html)
            # Recheck the exact plan after rasterization and before making any page deliverable.
            self.transport.authorize(incoming)
            if (
                self.adapter.conversation.operations.context(actor, task["scenario"])["plan"]["version"]
                != task["plan_version"]
            ):
                raise ChannelError("report_stale", "The report source changed.", 409)
            self.store.prepare_report(
                incoming["event_id"],
                incoming["destination"],
                incoming["sender"],
                task["task_id"],
                task["plan_version"],
                pages,
                case_versions=case_versions,
            )
            result["image_report_prepared"] = True
        except Exception:  # noqa: BLE001 - optional image failure preserves the verified text, never exposes provider details.
            result["image_report_prepared"] = False
            result["image_report_error"] = (
                "The image report could not be prepared. The verified text remains available."
            )
        self.adapter.inbox.finish(incoming["event_id"], result)

    async def step(self) -> bool:
        # Nothing is claimed or processed while the local sending gate is closed.
        require_sending()
        incoming = self.store.next()
        if incoming is None:
            return False
        eid = incoming["event_id"]
        preparing_reply = False
        try:
            self.transport.authorize(incoming)
            result = self.adapter.inbox.result(eid)
            if result is None:
                payload = {
                    "object": "whatsapp_business_account",
                    "entry": [
                        {
                            "changes": [
                                {
                                    "value": {
                                        "metadata": {"phone_number_id": incoming["destination"]},
                                        "messages": [incoming["message"]],
                                    }
                                }
                            ]
                        }
                    ],
                }
                preparing_reply = True
                await self.adapter.receive(payload)
                preparing_reply = False
                result = self.adapter.inbox.result(eid)
            if result is None:
                raise ChannelError("reply_unavailable", "No verified reply was prepared.")
            await self.prepare_report(incoming, result)
            # The exact text is persisted before any send, so a restart cannot change an accepted reply.
            if "delivery_text" not in result:
                result["delivery_text"] = confirmation_text(result["response"])
                if result.get("image_report_error"):
                    result["delivery_text"] += (
                        " Imaginea nu a putut fi pregătită. Rezultatul verificat rămâne disponibil în aplicație."
                        if result["response"].get("language") == "ro"
                        else " The image could not be prepared. The verified result remains available in the application."
                    )
                self.adapter.inbox.finish(eid, result)
            text = result["delivery_text"]
            self.store.prepare(eid, incoming["destination"], incoming["sender"], "text", text.encode())
            audio = None
            if result.get("tts") == "pending":
                self.audio_fallback(
                    eid, result, ChannelError("tts_interrupted", "Optional speech generation was interrupted.")
                )
            if result.get("audio_reply_path") and result.get("audio_delivery") != "failed_text_fallback":
                try:
                    self.transport.authorize(incoming, audio=True)
                    directory = self.adapter.inbox.path.parent / "channels-audio-replies"
                    expected = directory / (eid[3:] + ".mp3")
                    if Path(result["audio_reply_path"]).resolve() != expected.resolve():
                        raise ChannelError("audio_path_invalid", "The stored voice reply path is invalid.")
                    target = expected.with_suffix(".ogg")
                    if not target.is_file():
                        encoded = await voice_note(expected.read_bytes())
                        temporary = target.with_suffix(".ogg.tmp")
                        temporary.touch(mode=0o600, exist_ok=True)
                        temporary.write_bytes(encoded)
                        temporary.chmod(0o600)
                        temporary.replace(target)
                    audio = target.read_bytes()
                    self.store.prepare(eid, incoming["destination"], incoming["sender"], "audio", audio)
                except Exception as exc:  # noqa: BLE001 - optional encoding failure preserves the durable text; no raw diagnostics.
                    audio = None
                    self.audio_fallback(eid, result, exc)
            state = await self.transport.send(incoming, text=text)
            if state in {"accepted", "delivered", "read"} and audio is not None:
                try:
                    audio_state = await self.transport.send(incoming, audio=audio)
                except (ChannelError, OSError) as exc:
                    # An upload/pre-send failure is safe for text fallback. A message POST with
                    # an unknown result returns 'unknown' instead and keeps reconciliation required.
                    self.audio_fallback(eid, result, exc)
                else:
                    if audio_state in {"rejected", "failed", "cancelled"}:
                        self.audio_fallback(
                            eid,
                            result,
                            ChannelError("audio_not_accepted", "The optional voice reply was not accepted."),
                        )
                    else:
                        state = audio_state
            if state in {"accepted", "delivered", "read"}:
                for page in self.store.prepared_images(eid):
                    # Every send reauthorizes the current sender and inbound response window.
                    image_state = await self.transport.send(
                        incoming, image=bytes(page["payload"]), image_key=page["kind"][6:]
                    )
                    if image_state not in {"accepted", "delivered", "read"}:
                        state = image_state
                        break
            self.record_delivery(eid, state)
        except ChannelError as exc:
            if exc.code == "whatsapp_sending_disabled":
                self.store.queue_state(eid, "queued")
            elif (
                preparing_reply
                and incoming["attempts"] >= 2
                and exc.code in CONVERSATION_FAILURES
                and exc.status_code not in {401, 403, 404, 409, 422}
            ):
                await self.terminal_feedback(incoming, exc)
            elif exc.status_code in {401, 403, 404, 409, 422} or incoming["attempts"] >= 2:
                self.store.queue_state(eid, "failed", exc.code)
            else:
                self.store.queue_state(eid, "retryable", exc.code, delay=30 * (incoming["attempts"] + 1))
        except Exception:  # noqa: BLE001 - never log tokens, phone numbers, prompts or raw provider exceptions.
            self.store.queue_state(eid, "failed", "worker_unavailable")
        return True


def worker() -> WhatsAppWorker:
    from cyberpunks.channels.conversation import ConversationService

    root = runtime_root()
    # Only the isolated operational data paths are needed; do not load demo passwords or tokens.
    runtime_env = root / "daybreak.env"
    if runtime_env.is_file():
        if runtime_env.stat().st_mode & 0o077:
            raise ChannelError("runtime_config_permissions", "The local runtime configuration must be private.")
        import os

        for line in runtime_env.read_text().splitlines():
            key, sep, value = line.partition("=")
            if sep and key in {"CYBERPUNKS_OUTPUT_ROOT", "DAYBREAK_OPERATIONS_OUTPUTS", "DAYBREAK_OPERATIONS_DB"}:
                os.environ[key] = value.strip().strip("\"'")
    # common.paths reads CYBERPUNKS_OUTPUT_ROOT at import time; import operations only afterward.
    from cyberpunks.operations.service import get_service

    inbox = Inbox(root / "channels-whatsapp.sqlite3")
    store = DeliveryStore(inbox.path)
    bindings = Bindings(root / "whatsapp-bindings.json")
    operations = get_service()
    adapter = WhatsAppAdapter(ConversationService(operations), bindings, inbox)
    return WhatsAppWorker(adapter, store, MetaTransport(bindings, operations, store))


async def run_worker(*, once=False):
    root = runtime_root()
    root.mkdir(parents=True, exist_ok=True)
    lock = root / "channels-whatsapp-worker.lock"
    with lock.open("a") as handle:
        try:
            portalocker.lock(handle, portalocker.LOCK_EX | portalocker.LOCK_NB)
        except portalocker.exceptions.LockException:
            raise ChannelError("worker_already_running", "Another WhatsApp worker already owns this queue.") from None
        instance = worker()
        instance.store.recover()
        with instance.adapter.inbox.connect() as db:
            db.execute("UPDATE inbox SET state='retryable',updated=0 WHERE state='processing'")
        print("WhatsApp worker ready; one worker, durable queue, inbound replies only.", flush=True)
        while True:
            try:
                busy = await instance.step()
            except ChannelError as exc:
                if once:
                    raise
                if exc.code != "whatsapp_sending_disabled":
                    print(json.dumps({"worker_error_code": exc.code}), flush=True)
                busy = False
            if once:
                print(json.dumps(instance.store.counts()), flush=True)
                return
            if not busy:
                await asyncio.sleep(1)
