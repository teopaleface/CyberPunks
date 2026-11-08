"""Private, caller-bound HTTP tool for WhatsApp SIP calls. No outbound call or confirmation API."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import re
import time
import unicodedata
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import Field, ValidationError

from cyberpunks.channels import voice_intents
from cyberpunks.channels.elevenlabs import agent_config, runtime_root
from cyberpunks.channels.limits import Limits
from cyberpunks.channels.models import ChannelError, ChatRequest, StrictModel
from cyberpunks.channels.voice_jobs import voice_job_reply
from cyberpunks.channels.whatsapp import Bindings
from cyberpunks.operations.models import Actor, OperationError


def load_config() -> dict:
    path = runtime_root() / "whatsapp-calling.json"
    try:
        if path.stat().st_mode & 0o077:
            raise ValueError("private configuration required")
        return json.loads(path.read_text())
    except (OSError, ValueError):
        raise ChannelError("calling_unconfigured", "WhatsApp calling is not configured.") from None


async def verify_public_tool(origin: str, *, transport=None) -> None:
    """Verify the actual public tool path, not just saved SIP configuration."""
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=False, transport=transport) as client:
            health = await client.get(origin.rstrip("/") + "/healthz")
            if health.status_code != 200 or health.json().get("service") != "daybreak-whatsapp-call-tool":
                raise ValueError("Unexpected call service")
            denied = await client.post(origin.rstrip("/") + "/api/voice/turn", json={})
            if denied.status_code != 401:
                raise ValueError("Call tool authentication unavailable")
    except (httpx.HTTPError, ValueError, TypeError):
        raise ChannelError(
            "calling_tunnel_unavailable",
            "The public call-tool connection is unavailable. Repair the tunnel before testing a call.",
        ) from None


def save_config(config: dict) -> None:
    path = runtime_root() / "whatsapp-calling.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    with os.fdopen(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w") as handle:
        json.dump(config, handle, ensure_ascii=False, indent=2)
    temporary.chmod(0o600)
    temporary.replace(path)


def call_agent_config(voice_id: str, origin: str, secret_id: str, *, demo_enabled: bool = False) -> dict:
    config = agent_config("technician", voice_id)
    config["name"] = "Daybreak WhatsApp calls"
    config["tags"] = ["daybreak", "whatsapp-calls", "private-demo"]
    prompt = config["conversation_config"]["agent"]["prompt"]
    prompt["prompt"] = prompt["prompt"].replace("daybreak_turn", "daybreak_call_turn")
    prompt["prompt"] = (
        prompt["prompt"]
        .replace(
            "For every complete user utterance, immediately INVOKE",
            "For every complete intelligible user utterance, immediately INVOKE",
        )
        .replace(
            "Never end a user turn with a standalone acknowledgement. When the tool requires pre-tool speech, use only\n"
            "'Verific informațiile.' in Romanian or 'Let me check.' in English. Always emit the tool invocation in the same turn.\n"
            "Never output that acknowledgement without invoking the tool.",
            "Invoke the tool immediately without an acknowledgement or preamble. Never say 'Verific informațiile'.\n"
            "Silence, punctuation-only input such as '...' or '…', and [silence]/[inaudible] are not user utterances.\n"
            "For those inputs remain silent and do not invoke the tool. Do not re-engage a quiet user.\n"
            "If the tool returns an empty reply string, remain silent and wait for intelligible speech.",
        )
    )
    config["conversation_config"]["asr"]["keywords"] = [
        "PPC",
        "client",
        "dispecer",
        "tehnician",
        "stâlp",
        "stâlpul",
        "curent",
        "tichete",
        "echipament",
    ]
    config["conversation_config"]["turn"].update(
        turn_timeout=120,
        silence_end_call_timeout=180,
        retranscribe_on_turn_timeout=False,
        turn_eagerness="eager",
        soft_timeout_config={"timeout_seconds": -1, "message": "Aștept.", "use_llm_generated_message": False},
    )
    if demo_enabled:
        config["conversation_config"]["agent"]["first_message"] = "Salut! Testăm Daybreak, în demo."
        prompt["prompt"] = prompt["prompt"].replace(
            "the Daybreak technician voice coordinator", "the Daybreak server-bound voice coordinator"
        ).replace(
            "All actions require Confirm in the application.",
            "The private demo server may execute an explicitly requested, preauthorized workflow, register an incident and send a requested PDF. Only its verified result establishes whether an action happened.",
        ).replace(
            "Do not provide electrical instructions or claim that an action was performed.",
            "Do not provide electrical instructions. Report an action as performed only when the server reply explicitly verifies that result.",
        ).replace(
            "You cannot call, email, send WhatsApp messages or transfer calls.",
            "You cannot call, email or transfer calls. Only the server can send a requested WhatsApp PDF; speak its exact delivery result.",
        ) + (
            "\nOnly the server can select an explicitly preauthorized, unexpired synthetic demo role. "
            "Forward role declarations unchanged to the tool. Never select a role yourself, "
            "infer authorization, or add identity fields. Speak the returned demo label exactly once as returned."
        )
    prompt["tools"] = [
        {
            "type": "webhook",
            "name": "daybreak_call_turn",
            "description": "Call for every complete user utterance. The server verifies the real caller and returns the exact reply.",
            "response_timeout_secs": 90,
            "pre_tool_speech": "off",
            "interruption_mode": "allow",
            "tool_error_handling_mode": "hide",
            "follow_redirects": False,
            "api_schema": {
                "url": origin.rstrip("/") + "/api/voice/turn",
                "method": "POST",
                "request_headers": {"Authorization": {"secret_id": secret_id}},
                "request_body_schema": {
                    "type": "object",
                    "required": ["message", "caller_id", "conversation_id"],
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The complete original user utterance, unchanged.",
                        },
                        "caller_id": {"type": "string", "dynamic_variable": "system__caller_id"},
                        "conversation_id": {"type": "string", "dynamic_variable": "system__conversation_id"},
                    },
                },
            },
        }
    ]
    return config


class CallTurn(StrictModel):
    message: str = Field(min_length=0, max_length=4000)
    caller_id: str = Field(min_length=3, max_length=150)
    conversation_id: str = Field(min_length=3, max_length=150, pattern=r"^[A-Za-z0-9_.:-]+$")


def is_silent_transcript(message: str) -> bool:
    text = "".join(c for c in unicodedata.normalize("NFKD", message.casefold()) if not unicodedata.combining(c)).strip()
    if not any(char.isalnum() for char in text):
        return True
    return bool(
        re.fullmatch(
            r"[\[(<]?\s*(?:silence|inaudible|unintelligible|no speech|background noise|tacere|neinteligibil)\s*[\])>]?",
            text,
        )
    )


def is_hearing_check(message: str) -> bool:
    return voice_intents.hearing_check(message)


def is_report_request(message: str) -> bool:
    return voice_intents.report_request(message)


def clarified_incident(message: str, history: list[dict]) -> str:
    if not history or history[-1] != {
        "role": "assistant",
        "content": "Te referi la un stâlp căzut sau la o întrerupere de curent?",
    }:
        return message
    plain = "".join(c for c in unicodedata.normalize("NFKD", message.casefold()) if not unicodedata.combining(c))
    if re.fullmatch(r"\s*(?:un\s+)?stalp(?:ul|u)?(?:\s+cazut)?[.!, ]*", plain):
        return "Raportez că a căzut un stâlp de curent."
    if re.fullmatch(r"\s*(?:o\s+)?intrerupere(?:\s+de\s+curent)?[.!, ]*", plain):
        return "Am rămas fără curent."
    return message


def is_dispatch_request(message: str, *, queue_context: bool = False) -> bool:
    return voice_intents.dispatch_request(message, queue_context=queue_context)


DEMO_ROLES = {"client": "customer", "dispecer": "dispatcher", "tehnician": "technician"}
DEMO_LABELS = {"customer": "Demo client.", "dispatcher": "Demo dispecer.", "technician": "Demo tehnician."}
ROLE_QUESTION = "Ce rol alegi pentru demo: client PPC, dispecer PPC sau tehnician PPC?"
DECLARATION = re.compile(r"\b(client|dispecer|tehnician)\b")
DECLARATIVE_PREFIX = re.compile(
    r"^\s*(?:(?:a+|e+|um|uh|hmm?|pai|deci|ok|okay|bun|bine|si|iar|apoi|acum|te\s+rog|hai(?:\s+sa)?|in\s+continuare)[\s,.!:;\-]+){0,6}"
    r"(?:(?:salut|buna(?:\s+ziua)?)[\s,.!:]+)?"
    r"(?:(?:acuma\s+)?(?:schimbam|schimb|schimba)\s+rolul[\s,.!:;]+)?"
    r"(?:(?:da[\s,]+)|(?:nu[\s,]+(?=eu\s+sunt\b)))?"
    r"(?:(?:acum\s+(?:eu\s+)?(?:sunt\s+)?|(?:eu\s+)?sunt\s+)|"
    r"(?:(?:aleg|selectez)\s+(?:rolul\s+(?:de\s+)?)?)|"
    r"(?:trec\s+(?:la|pe)\s+(?:rolul\s+(?:de\s+)?)?))?"
    r"(?:un\s+)?"
    r"(client|dispecer|tehnician)\b"
    r"(?:\s+(?:ppc|tpc|p[\s.\-]+p[\s.\-]+c|pe\s+pe\s+ce)\b)?"
)


def _fingerprint(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _role_declaration(message: str) -> tuple[str | None, str, bool]:
    """Only an unquoted affirmative prefix selects a privately provisioned role."""
    normalized, positions = "", []
    for index, char in enumerate(message):
        plain = "".join(c for c in unicodedata.normalize("NFKD", char.casefold()) if not unicodedata.combining(c))
        normalized += plain
        positions.extend([index + 1] * len(plain))
    mentions = list(DECLARATION.finditer(normalized))
    if not mentions:
        return None, message, False
    prefix = DECLARATIVE_PREFIX.match(normalized)
    if len(mentions) != 1 or prefix is None:
        return None, message, True
    tail = normalized[prefix.end() :]
    # A question, quotation, hypothetical or immediate denial is not a declaration.
    if (
        tail
        and not (tail[0].isspace() or tail[0] in ".,;:!")
        or re.match(
            r"^[\s.,;:!]*(?:[?\"'«»„“”]|(?:poate|daca|sau|oare|ipotetic|sa\s+zicem)\b|"
            r"(?:(?:dar|insa)\s+)?(?:nu|nici)\s+sunt\b|nu\s*[?.!]*$)",
            tail,
        )
    ):
        return None, message, True
    remainder = message[positions[prefix.end() - 1] :].lstrip(" \t\r\n.,;:!")
    return DEMO_ROLES[prefix[1]], remainder, False


def _demo_profile(config: dict, caller: str, operations) -> tuple[dict[str, Actor], str, str] | None:
    """Fail closed to the verified ordinary actor if any private demo profile is invalid."""
    try:
        entry = config.get("demo_callers", {})[caller]
        expiry = datetime.fromisoformat(entry["expires_at"])
        if expiry.utcoffset() != timedelta(0) or expiry <= datetime.now(UTC):
            return None
        if set(entry["actors"]) != set(DEMO_LABELS):
            return None
        actors = {role: Actor.model_validate(value) for role, value in entry["actors"].items()}
        connection_id = entry["customer_connection_id"]
        if not isinstance(connection_id, str) or not connection_id:
            return None
        for role, actor in actors.items():
            if actor.role != role or actor.organization_id != "daybreak-demo":
                return None
            if role == "customer":
                if actor.crew_id or actor.permissions or connection_id not in actor.connection_ids:
                    return None
            elif role == "technician":
                if not actor.crew_id or actor.connection_ids or actor.permissions:
                    return None
            elif (
                actor.crew_id
                or actor.connection_ids
                or not actor.permissions
                or not set(actor.permissions)
                <= {
                    "approve_plan",
                    "review_work_item",
                    "create_case",
                    "recover_commands",
                    "view_console",
                }
            ):
                return None
            context = operations.context(actor, "demo-vara")
            if (
                context.get("actor") != actor.model_dump()
                or context.get("scenario") != "demo-vara"
                or not context.get("synthetic")
            ):
                return None
            if role == "customer" and not set(actor.connection_ids) <= {
                c["connection_id"] for c in context["connections"] if c.get("synthetic")
            }:
                return None
            if role == "technician" and not any(
                route["crew_id"] == actor.crew_id for route in context["plan"]["routes"]
            ):
                return None
        return actors, connection_id, _fingerprint(entry)
    except (KeyError, TypeError, ValueError, OverflowError, AttributeError, ValidationError, OperationError):
        return None


def create_app(
    *, service=None, bindings=None, config_loader=load_config, report_sender=None, background_jobs=None, job_store=None
) -> FastAPI:
    background_jobs = service is None if background_jobs is None else background_jobs
    if service is None:
        # Import operations only after selecting the existing complete isolated runtime data.
        path = runtime_root() / "daybreak.env"
        if not path.is_file() or path.stat().st_mode & 0o077:
            raise ChannelError("runtime_config_permissions", "Private runtime configuration is required.")
        for line in path.read_text().splitlines():
            key, sep, value = line.partition("=")
            if sep and key in {"CYBERPUNKS_OUTPUT_ROOT", "DAYBREAK_OPERATIONS_OUTPUTS", "DAYBREAK_OPERATIONS_DB"}:
                os.environ[key] = value.strip().strip("\"'")
        from cyberpunks.channels.conversation import ConversationService
        from cyberpunks.operations.service import get_service

        service = ConversationService(get_service())
    bindings = bindings or Bindings(runtime_root() / "whatsapp-bindings.json")
    if background_jobs and job_store is None:
        from cyberpunks.channels.voice_jobs import VoiceJobs

        job_store = VoiceJobs(service.operations.db_path.with_name("voice-jobs.sqlite3"))

    def authorize_job(job):
        payload = job["payload"]
        current = config_loader()
        caller = payload["caller"]
        if caller not in current.get("allowed_callers", []) or current["phone_number_id"] != payload["destination"]:
            raise ChannelError("caller_forbidden", "The caller authorization changed.", 403)
        rebound = bindings.resolve(payload["destination"], caller)
        profile = _demo_profile(current, caller, service.operations)
        actor = Actor.model_validate(job["verifiedActor"])
        permission = "allow_voice_reports" if job["kind"] == "report" else "allow_queue_actions"
        if (
            not profile
            or profile[2] != payload["demo_signature"]
            or _fingerprint(rebound.model_dump()) != payload["base_actor_signature"]
            or profile[0].get(actor.role) != actor
            or current["demo_callers"][caller].get(permission) is not True
        ):
            raise ChannelError("demo_expired", "The private job authorization changed.", 403)
        return actor

    async def handle_job(job):
        actor = authorize_job(job)
        if job["kind"] == "report":
            from cyberpunks.channels.voice_reports import send_voice_report

            sender = report_sender or send_voice_report
            result = await sender(
                service.operations,
                actor,
                caller=job["payload"]["caller"],
                destination=job["payload"]["destination"],
                event_key=job["event_key"],
                authorize_actor=lambda: authorize_job(job),
            )
            return {**result, "status": "failed"} if result.get("status") == "error" else result
        from cyberpunks.channels.voice_dispatch import run_dispatch

        def execute():
            result = asyncio.run(
                run_dispatch(
                    service.operations,
                    actor,
                    event_key=job["event_key"],
                    authorize_actor=lambda requested_actor: authorize_job(job),
                )
            )
            if result.get("status") == "completed" and result.get("applied", 0) and "approve_plan" in actor.permissions:
                authorize_job(job)
                plan = service.operations.context(actor, "demo-vara")["plan"]
                proposal = service.operations.prepare(
                    actor,
                    "approve_plan",
                    {
                        "plan_id": plan["plan_id"],
                        "plan_version": plan["version"],
                        "idempotency_key": "voice-plan:" + hashlib.sha256(job["event_key"].encode()).hexdigest(),
                    },
                    "demo-vara",
                )
                authorize_job(job)
                command = service.operations.confirm(actor, proposal["proposal_id"])
                observed = service.operations.observe_effect(actor, proposal["proposal_id"], "demo-vara")
                if command.get("status") == "succeeded" and (observed.get("command") or {}).get(
                    "command_id"
                ) == command.get("command_id"):
                    result["plan_approval"] = command
                    result["reply"] += " Planul rezultat este aprobat pentru echipe."
                else:
                    result.update(
                        status="needs_reconciliation", reply=result["reply"] + " Aprobarea planului nu este confirmată."
                    )
            return result

        return await asyncio.to_thread(execute)

    @asynccontextmanager
    async def lifespan(app):
        async def drain():
            while True:
                try:
                    claimed = await job_store.drain_one(handle_job)
                except Exception:  # noqa: BLE001 - private job data must not enter public logs.
                    claimed = None
                if claimed is None:
                    await asyncio.sleep(0.2)

        worker = asyncio.create_task(drain()) if background_jobs else None
        try:
            yield
        finally:
            if worker:
                worker.cancel()
                await asyncio.gather(worker, return_exceptions=True)

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.state.voice_jobs = job_store
    app.state.voice_job_handler = handle_job
    sessions: dict[str, dict] = {}
    limiter = Limits(per_minute=40, concurrency=8, max_actors=100)
    inflight: dict[str, asyncio.Task] = {}
    provider_slots = asyncio.Semaphore(2)

    def reply_for_job(job):
        if job["kind"] == "report" and job["status"] == "done":
            from cyberpunks.channels.voice_reports import observe_voice_report

            observed = observe_voice_report(job["event_key"], runtime_root() / "channels-whatsapp.sqlite3")
            if observed:
                return observed["reply"]
        return voice_job_reply(job)

    @asynccontextmanager
    async def call_budget(key):
        # Count requests, but do not reserve the call's slot while awaiting a
        # provider. An interruption or a factual read must remain available.
        async with limiter.acquire(key):
            pass
        yield

    async def bounded_chat(actor, message, history, event_key):
        async with provider_slots:
            return await service.chat(actor, ChatRequest(message=message, history=history), event_key=event_key)

    def fast_job_turn(request, config, caller, base_actor):
        """Enqueue/read only, using a previously verified unchanged call identity.

        Long planner file locks must not delay acknowledgements. Every job still
        reauthorizes from current operational data before any effect or delivery.
        """
        if not background_jobs:
            return None
        existing = sessions.get(request.conversation_id)
        entry = config.get("demo_callers", {}).get(caller, {})
        signature = _fingerprint(
            {"actor": base_actor.model_dump(), "caller": caller, "destination": config["phone_number_id"]}
        )
        try:
            expiry = datetime.fromisoformat(entry["expires_at"])
            if (
                not existing
                or existing["actor"] != signature
                or existing["expires"] <= time.monotonic()
                or existing.get("demo") != _fingerprint(entry)
                or expiry.utcoffset() != timedelta(0)
                or expiry <= datetime.now(UTC)
            ):
                return None
            role, remainder, ambiguous = _role_declaration(request.message)
            if ambiguous:
                return None
            role = role or existing.get("demo_role")
            actor = Actor.model_validate(entry["actors"][role])
            message = remainder if _role_declaration(request.message)[0] else request.message
            kind = (
                "report"
                if is_report_request(message) and entry.get("allow_voice_reports") is True
                else "dispatch"
                if role == "dispatcher"
                and is_dispatch_request(message, queue_context=bool(existing.get("queue_context")))
                and entry.get("allow_queue_actions") is True
                else None
            )
            if kind:
                key = (
                    "wa-call:"
                    + hashlib.sha256(
                        (
                            request.conversation_id
                            + "\0"
                            + _fingerprint(actor.model_dump())
                            + "\0"
                            + role
                            + "\0"
                            + message
                        ).encode()
                    ).hexdigest()
                )
                job = job_store.submit(
                    actor,
                    kind,
                    {
                        "conversation_id": request.conversation_id,
                        "caller": caller,
                        "destination": config["phone_number_id"],
                        "demo_signature": existing["demo"],
                        "base_actor_signature": _fingerprint(base_actor.model_dump()),
                    },
                    key,
                    coalesce=True,
                )
                reply = reply_for_job(job)
            elif voice_intents.status_request(message):
                job = job_store.latest(actor, request.conversation_id) or job_store.latest(actor)
                if not job:
                    return None
                reply = reply_for_job(job)
            else:
                return None
            switched = existing.get("demo_role") != role
            existing.update(
                demo_role=role, effective_actor=_fingerprint(actor.model_dump()), expires=time.monotonic() + 660
            )
            if switched:
                existing.update(history=[], replies={})
            existing["queue_context"] = role == "dispatcher" and (
                kind == "dispatch" or bool(existing.get("queue_context"))
            )
            return {"reply": (DEMO_LABELS[role] + " " if switched else "") + reply}
        except (KeyError, TypeError, ValueError, ValidationError):
            return None

    @app.middleware("http")
    async def authorize(request: Request, call_next):
        if request.url.path != "/healthz":
            try:
                token = config_loader().get("tool_token", "")
            except ChannelError:
                token = ""
            supplied = request.headers.get("authorization", "")
            if not token or not hmac.compare_digest(supplied.encode(), ("Bearer " + token).encode()):
                return JSONResponse({"detail": "Authentication required."}, status_code=401)
            size = request.headers.get("content-length", "")
            if not size.isdigit() or int(size) > 20_000:
                return JSONResponse({"detail": "A bounded request is required."}, status_code=413)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/healthz")
    def health():
        return {"status": "ok", "service": "daybreak-whatsapp-call-tool"}

    @app.post("/api/voice/turn")
    async def turn(request: CallTurn):
        try:
            config = config_loader()
            caller = request.caller_id.removeprefix("+")
            if not re.fullmatch(r"[0-9]{5,20}", caller) or caller not in config.get("allowed_callers", []):
                raise ChannelError("caller_forbidden", "This caller is not enabled for the private demo.", 403)
            base_actor = bindings.resolve(config["phone_number_id"], caller)
            if is_silent_transcript(request.message):
                return {"reply": ""}
            if is_hearing_check(request.message):
                return {"reply": "Te aud. Spune-mi întrebarea."}
            previous = inflight.get(request.conversation_id)
            if previous and not previous.done():
                previous.cancel()
                await asyncio.gather(previous, return_exceptions=True)
            quick = fast_job_turn(request, config, caller, base_actor)
            if quick is not None:
                return quick
            # Scope and binding are rechecked on every turn. Neither the model nor the request selects a role.
            service.operations.context(base_actor, "demo-vara")
            now = time.monotonic()
            for expired in [key for key, value in sessions.items() if value["expires"] < now]:
                del sessions[expired]
            base_signature = _fingerprint(
                {
                    "actor": base_actor.model_dump(),
                    "caller": caller,
                    "destination": config["phone_number_id"],
                }
            )
            async with call_budget((base_actor.organization_id, base_actor.user_id, request.conversation_id)):
                existing = sessions.get(request.conversation_id)
                if existing and existing["actor"] != base_signature:
                    raise ChannelError("call_identity_changed", "The call identity changed. Start a new call.", 403)
                if not existing and len(sessions) >= 100:
                    raise ChannelError("calling_busy", "The call service is busy.", 429)
                profile = _demo_profile(config, caller, service.operations)
                selected_role = None
                demo_signature = None
                message = request.message
                actor = base_actor
                connection_id = None
                role_only = False
                if profile:
                    actors, connection_id, demo_signature = profile
                    selected_role = (
                        existing.get("demo_role")
                        if existing and existing.get("demo") == demo_signature
                        else base_actor.role
                        if base_actor.role in actors
                        else None
                    )
                    declared_role, remainder, ambiguous = _role_declaration(message)
                    if ambiguous:
                        return {"reply": ROLE_QUESTION}
                    if declared_role:
                        selected_role = declared_role
                        role_only = not remainder
                        message = (
                            remainder
                            or {
                                "customer": "Spune-mi ce s-a întâmplat la locul de consum.",
                                "dispatcher": "Câte tichete am și câte au risc de siguranță?",
                                "technician": "Ce am de făcut astăzi? Trebuie echipament?",
                            }[declared_role]
                        )
                    if selected_role:
                        actor = actors[selected_role]
                effective_signature = _fingerprint(actor.model_dump())
                switched = bool(selected_role) and (
                    not existing
                    or existing.get("effective_actor") != effective_signature
                    or existing.get("demo") != demo_signature
                    or existing.get("demo_role") != selected_role
                )
                same_identity = bool(existing) and (
                    existing.get("effective_actor") == effective_signature
                    and existing.get("demo") == demo_signature
                    and existing.get("demo_role") == selected_role
                )
                history = existing["history"] if same_identity else []
                queue_context = bool(same_identity and existing.get("queue_context"))
                # Preserve verified identity before any awaited provider call. An
                # interrupted request must not lose the role or poison the next call.
                sessions[request.conversation_id] = {
                    "actor": base_signature,
                    "effective_actor": effective_signature,
                    "demo": demo_signature,
                    "demo_role": selected_role,
                    "expires": now + 660,
                    "history": history,
                    "replies": dict(existing.get("replies", {})) if existing else {},
                    "queue_context": queue_context,
                }
                dedupe = (
                    "wa-call:"
                    + hashlib.sha256(
                        (
                            request.conversation_id + "\0" + effective_signature + "\0" + actor.role + "\0" + message
                        ).encode()
                    ).hexdigest()
                )
                replies = dict(existing.get("replies", {})) if existing else {}
                cached = replies.get(dedupe)
                reply = (
                    cached["reply"]
                    if cached
                    and (
                        cached.get("write_executed") or datetime.fromisoformat(cached["expires_at"]) > datetime.now(UTC)
                    )
                    else None
                )
                if cached and not cached.get("write_executed"):
                    current_version = service.operations.context(actor, "demo-vara")["plan"]["version"]
                    if reply is None or cached.get("plan_version") != current_version:
                        return {
                            "reply": "Propunerea anterioară nu mai este valabilă. Cere o evaluare nouă înainte de confirmare."
                        }
                if reply is None:
                    result = {"reply": message} if role_only and selected_role == "customer" else None
                    entry = config.get("demo_callers", {}).get(caller, {}) if selected_role else {}

                    def authorize_demo_actor():
                        current_config = config_loader()
                        rebound = bindings.resolve(current_config["phone_number_id"], caller)
                        if _fingerprint(rebound.model_dump()) != _fingerprint(base_actor.model_dump()):
                            raise ChannelError("sender_binding_changed", "The verified caller changed.", 403)
                        current_profile = _demo_profile(current_config, caller, service.operations)
                        if (
                            not current_profile
                            or current_profile[2] != demo_signature
                            or not current_config["demo_callers"][caller].get("allow_voice_reports")
                            or current_profile[0][selected_role] != actor
                        ):
                            raise ChannelError("demo_expired", "The private report session expired.", 403)
                        return actor

                    if selected_role and is_report_request(message) and entry.get("allow_voice_reports") is True:
                        if background_jobs:
                            job = job_store.submit(
                                actor,
                                "report",
                                {
                                    "conversation_id": request.conversation_id,
                                    "caller": caller,
                                    "destination": config["phone_number_id"],
                                    "demo_signature": demo_signature,
                                    "base_actor_signature": _fingerprint(base_actor.model_dump()),
                                },
                                dedupe,
                                coalesce=True,
                            )
                            result = {"reply": reply_for_job(job)}
                        sender = report_sender
                        if sender is None:
                            from cyberpunks.channels.voice_reports import send_voice_report

                            sender = send_voice_report
                        if result is None:
                            result = await sender(
                                service.operations,
                                actor,
                                caller=caller,
                                destination=config["phone_number_id"],
                                event_key=dedupe,
                                authorize_actor=authorize_demo_actor,
                            )
                    if (
                        selected_role == "dispatcher"
                        and is_dispatch_request(message, queue_context=queue_context)
                        and entry.get("allow_queue_actions") is True
                    ) and background_jobs:
                        job = job_store.submit(
                            actor,
                            "dispatch",
                            {
                                "conversation_id": request.conversation_id,
                                "caller": caller,
                                "destination": config["phone_number_id"],
                                "demo_signature": demo_signature,
                                "base_actor_signature": _fingerprint(base_actor.model_dump()),
                            },
                            dedupe,
                            coalesce=True,
                        )
                        result = {"reply": reply_for_job(job)}
                    if result is None and background_jobs and selected_role and voice_intents.status_request(message):
                        latest = job_store.latest(actor, request.conversation_id) or job_store.latest(actor)
                        if latest:
                            result = {"reply": reply_for_job(latest)}
                    if selected_role:
                        from cyberpunks.channels.voice_briefs import answer_demo

                        if result is None:
                            action_options = (
                                {"execute_incident": True} if entry.get("allow_incident_actions") is True else {}
                            )
                            result = answer_demo(
                                service.operations,
                                actor,
                                clarified_incident(message, history) if selected_role == "customer" else message,
                                event_key=dedupe,
                                connection_id=connection_id,
                                **action_options,
                            )
                    if result is None:
                        pending = asyncio.create_task(bounded_chat(actor, message, history, dedupe))
                        inflight[request.conversation_id] = pending
                        try:
                            result = await asyncio.wait_for(pending, timeout=15)
                        finally:
                            if inflight.get(request.conversation_id) is pending:
                                inflight.pop(request.conversation_id, None)
                    reply = result["reply"]
                    queue_context = selected_role == "dispatcher" and (
                        queue_context
                        or bool((result.get("provenance") or {}).get("queue_scope"))
                        or is_dispatch_request(message, queue_context=queue_context)
                    )
                    # Repeated reads must still see the current plan. Only prepared
                    # proposals are replayed, within their actual validity window.
                    if result.get("proposal"):
                        expires_at = datetime.fromisoformat(result["proposal"]["expires_at"])
                        replies[dedupe] = {
                            "reply": reply,
                            "expires_at": expires_at.isoformat(),
                            "plan_version": result["proposal"].get("plan_version"),
                            "write_executed": bool((result.get("provenance") or {}).get("write_executed")),
                        }
                    history = (
                        history
                        + [
                            {"role": "user", "content": message},
                            {"role": "assistant", "content": reply[:4000]},
                        ]
                    )[-12:]
                sessions[request.conversation_id] = {
                    "actor": base_signature,
                    "effective_actor": effective_signature,
                    "demo": demo_signature,
                    "demo_role": selected_role,
                    "expires": now + 660,
                    "history": history,
                    "replies": dict(list(replies.items())[-32:]),
                    "queue_context": queue_context,
                }
            return {"reply": (DEMO_LABELS[selected_role] + " " if switched else "") + reply}
        except ChannelError as exc:
            if exc.status_code >= 500 or exc.status_code == 429:
                return {
                    "reply": "Nu am reușit să verific acea cerere acum. Poți cere traseul, situația tichetelor sau raportul."
                }
            return JSONResponse({"error": exc.code, "message": exc.message}, status_code=exc.status_code)
        except TimeoutError:
            return {"reply": "Răspunsul durează prea mult. Poți cere direct traseul, situația tichetelor sau raportul."}
        except Exception:  # noqa: BLE001 - public boundary must not expose provider/operational details.
            # Provider and operational errors can contain private objects. Never return their raw text.
            return JSONResponse(
                {"error": "call_turn_unavailable", "message": "Please use text in the app."}, status_code=503
            )

    return app
