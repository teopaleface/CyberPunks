"""Private, caller-bound HTTP tool for WhatsApp SIP calls. No outbound call or confirmation API."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import time

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import Field

from cyberpunks.channels.elevenlabs import agent_config, runtime_root
from cyberpunks.channels.limits import Limits
from cyberpunks.channels.models import ChannelError, ChatRequest, StrictModel
from cyberpunks.channels.whatsapp import Bindings


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


def call_agent_config(voice_id: str, origin: str, secret_id: str) -> dict:
    config = agent_config("technician", voice_id)
    config["name"] = "Daybreak WhatsApp calls"
    config["tags"] = ["daybreak", "whatsapp-calls", "private-demo"]
    prompt = config["conversation_config"]["agent"]["prompt"]
    prompt["prompt"] = prompt["prompt"].replace("daybreak_turn", "daybreak_call_turn")
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
            actor = bindings.resolve(config["phone_number_id"], caller)
            # Scope and binding are rechecked on every turn. Neither the model nor the request selects a role.
            service.operations.context(actor, "demo-vara")
            now = time.monotonic()
            for expired in [key for key, value in sessions.items() if value["expires"] < now]:
                del sessions[expired]
            existing = sessions.get(request.conversation_id)
            actor_signature = hashlib.sha256(actor.model_dump_json().encode()).hexdigest()
            if existing and existing["actor"] != actor_signature:
                raise ChannelError("call_identity_changed", "The call identity changed. Start a new call.", 403)
            if not existing and len(sessions) >= 100:
                raise ChannelError("calling_busy", "The call service is busy.", 429)
            async with limiter.acquire((actor.organization_id, actor.user_id)):
                history = existing["history"] if existing else []
                dedupe = "wa-call:" + hashlib.sha256(
                    (request.conversation_id + "\0" + request.message).encode()
                ).hexdigest()
                result = await service.chat(actor, ChatRequest(message=request.message, history=history), event_key=dedupe)
                sessions[request.conversation_id] = {
                    "actor": actor_signature,
                    "expires": now + 660,
                    "history": (history + [
                        {"role": "user", "content": request.message},
                        {"role": "assistant", "content": result["reply"]},
                    ])[-12:],
                }
            return {"reply": result["reply"]}
        except ChannelError as exc:
            return JSONResponse({"error": exc.code, "message": exc.message}, status_code=exc.status_code)
        except Exception:  # noqa: BLE001 - public boundary must not expose provider/operational details.
            # Provider and operational errors can contain private objects. Never return their raw text.
            return JSONResponse({"error": "call_turn_unavailable", "message": "Please use text in the app."}, status_code=503)

    return app
