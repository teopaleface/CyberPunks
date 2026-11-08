"""Private, caller-bound HTTP tool for WhatsApp SIP calls. No outbound call or confirmation API."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import time
import unicodedata
from datetime import UTC, datetime, timedelta

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import Field, ValidationError

from cyberpunks.channels.elevenlabs import agent_config, runtime_root
from cyberpunks.channels.limits import Limits
from cyberpunks.channels.models import ChannelError, ChatRequest, StrictModel
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
        raise ChannelError("calling_tunnel_unavailable", "The public call-tool connection is unavailable. Repair the tunnel before testing a call.") from None


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
    if demo_enabled:
        config["conversation_config"]["agent"]["first_message"] = (
            "Salut! Testăm Daybreak, în demo."
        )
        prompt["prompt"] = prompt["prompt"].replace(
            "the Daybreak technician voice coordinator", "the Daybreak server-bound voice coordinator"
        ) + (
            "\nOnly the server can select an explicitly preauthorized, unexpired synthetic demo role. "
            "Forward role declarations unchanged to the tool. Never select a role yourself, "
            "infer authorization, or add identity fields. Speak the returned demo label exactly once as returned."
        )
    prompt["tools"] = [{
        "type": "webhook",
        "name": "daybreak_call_turn",
        "description": "Call for every complete user utterance. The server verifies the real caller and returns the exact reply.",
        "response_timeout_secs": 90,
        "pre_tool_speech": "force",
        "interruption_mode": "disable_during_tool_and_turn",
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
                    "message": {"type": "string", "description": "The complete original user utterance, unchanged."},
                    "caller_id": {"type": "string", "dynamic_variable": "system__caller_id"},
                    "conversation_id": {"type": "string", "dynamic_variable": "system__conversation_id"},
                },
            },
        },
    }]
    return config


class CallTurn(StrictModel):
    message: str = Field(min_length=1, max_length=4000)
    caller_id: str = Field(min_length=3, max_length=150)
    conversation_id: str = Field(min_length=3, max_length=150, pattern=r"^[A-Za-z0-9_.:-]+$")


DEMO_ROLES = {"client": "customer", "dispecer": "dispatcher", "tehnician": "technician"}
DEMO_LABELS = {"customer": "Demo client.", "dispatcher": "Demo dispecer.", "technician": "Demo tehnician."}
ROLE_QUESTION = "Ce rol alegi pentru demo: client PPC, dispecer PPC sau tehnician PPC?"
DECLARATION = re.compile(r"\b(?:sunt\s+)?(client|dispecer|tehnician)\s+ppc\b")
DECLARATIVE_PREFIX = re.compile(r"^\s*(?:acum\s+(?:sunt\s+)?|sunt\s+)(client|dispecer|tehnician)\s+ppc\b")


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
    tail = normalized[prefix.end():]
    # A question, quotation, hypothetical or immediate denial is not a declaration.
    if (
        tail and not (tail[0].isspace() or tail[0] in ".,;:!")
        or re.match(r"^[\s.,;:!]*(?:[?\"'«»„“”]|(?:poate|daca)\b|(?:nu|nici)\s+sunt\b|nu\s*[?.!]*$)", tail)
    ):
        return None, message, True
    remainder = message[positions[prefix.end() - 1]:].lstrip(" \t\r\n.,;:!")
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
                actor.crew_id or actor.connection_ids or not actor.permissions
                or not set(actor.permissions) <= {
                    "approve_plan", "review_work_item", "create_case", "recover_commands", "view_console",
                }
            ):
                return None
            context = operations.context(actor, "demo-vara")
            if context.get("actor") != actor.model_dump() or context.get("scenario") != "demo-vara" or not context.get("synthetic"):
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


def create_app(*, service=None, bindings=None, config_loader=load_config) -> FastAPI:
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
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    sessions: dict[str, dict] = {}
    limiter = Limits(per_minute=16, concurrency=1, max_actors=100)

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
            # Scope and binding are rechecked on every turn. Neither the model nor the request selects a role.
            service.operations.context(base_actor, "demo-vara")
            now = time.monotonic()
            for expired in [key for key, value in sessions.items() if value["expires"] < now]:
                del sessions[expired]
            base_signature = _fingerprint({
                "actor": base_actor.model_dump(), "caller": caller, "destination": config["phone_number_id"],
            })
            async with limiter.acquire((base_actor.organization_id, base_actor.user_id)):
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
                if profile:
                    actors, connection_id, demo_signature = profile
                    selected_role = existing.get("demo_role") if existing and existing.get("demo") == demo_signature else None
                    declared_role, remainder, ambiguous = _role_declaration(message)
                    if ambiguous:
                        return {"reply": ROLE_QUESTION}
                    if declared_role:
                        selected_role = declared_role
                        message = remainder or "Cu ce mă poți ajuta în acest rol demo?"
                    if selected_role:
                        actor = actors[selected_role]
                effective_signature = _fingerprint(actor.model_dump())
                switched = bool(selected_role) and (
                    not existing or existing.get("effective_actor") != effective_signature
                    or existing.get("demo") != demo_signature or existing.get("demo_role") != selected_role
                )
                same_identity = bool(existing) and (
                    existing.get("effective_actor") == effective_signature
                    and existing.get("demo") == demo_signature and existing.get("demo_role") == selected_role
                )
                history = existing["history"] if same_identity else []
                dedupe = "wa-call:" + hashlib.sha256(
                    (request.conversation_id + "\0" + effective_signature + "\0" + actor.role + "\0" + message).encode()
                ).hexdigest()
                replies = dict(existing.get("replies", {})) if existing else {}
                cached = replies.get(dedupe)
                reply = (
                    cached["reply"]
                    if cached and datetime.fromisoformat(cached["expires_at"]) > datetime.now(UTC)
                    else None
                )
                if reply is None:
                    result = None
                    if selected_role:
                        from cyberpunks.channels.voice_briefs import answer_demo

                        result = answer_demo(
                            service.operations, actor, message, event_key=dedupe, connection_id=connection_id,
                        )
                    if result is None:
                        result = await service.chat(
                            actor, ChatRequest(message=message, history=history), event_key=dedupe,
                        )
                    reply = result["reply"]
                    # Repeated reads must still see the current plan. Only prepared
                    # proposals are replayed, within their actual validity window.
                    if result.get("proposal"):
                        expires_at = datetime.fromisoformat(result["proposal"]["expires_at"])
                        replies[dedupe] = {"reply": reply, "expires_at": expires_at.isoformat()}
                    history = (history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": reply[:4000]},
                    ])[-12:]
                sessions[request.conversation_id] = {
                    "actor": base_signature,
                    "effective_actor": effective_signature,
                    "demo": demo_signature,
                    "demo_role": selected_role,
                    "expires": now + 660,
                    "history": history,
                    "replies": dict(list(replies.items())[-32:]),
                }
            return {"reply": (DEMO_LABELS[selected_role] + " " if switched else "") + reply}
        except ChannelError as exc:
            return JSONResponse({"error": exc.code, "message": exc.message}, status_code=exc.status_code)
        except Exception:  # noqa: BLE001 - public boundary must not expose provider/operational details.
            # Provider and operational errors can contain private objects. Never return their raw text.
            return JSONResponse({"error": "call_turn_unavailable", "message": "Please use text in the app."}, status_code=503)

    return app
