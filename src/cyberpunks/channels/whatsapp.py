"""WhatsApp semnat, cu ACK după coada durabilă și procesare într-un worker separat."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import sqlite3
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from cyberpunks.channels.conversation import ConversationService
from cyberpunks.channels.elevenlabs import ElevenLabs, runtime_root
from cyberpunks.channels.limits import limits
from cyberpunks.channels.models import ChannelError, ChatRequest
from cyberpunks.channels.whatsapp_config import settings

router = APIRouter(prefix="/whatsapp", tags=["whatsapp-inbound-disabled-by-default"])
MAX_BODY = 128_000
MAX_AUDIO = 10_000_000
AUDIO_TYPES = {"audio/ogg", "audio/mpeg", "audio/mp4", "audio/aac", "audio/amr", "audio/wav", "audio/x-wav"}


def enabled() -> None:
    if settings()["DAYBREAK_WHATSAPP_ENABLED"] != "1":
        raise ChannelError("whatsapp_disabled", "WhatsApp is not enabled. Use the authenticated browser conversation.")


def verify_signature(body: bytes, signature: str | None, secret: str) -> None:
    if not secret:
        raise ChannelError("whatsapp_unconfigured", "The Meta webhook signing secret is not configured.")
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not signature or not hmac.compare_digest(signature.encode(), expected.encode()):
        raise ChannelError("invalid_signature", "A valid Meta webhook signature is required.", 401)


class Bindings:
    def __init__(self, path: Path):
        self.path = path

    def resolve(self, phone_number_id: str, sender: str, *, with_options=False):
        from cyberpunks.operations.models import Actor

        try:
            if self.path.stat().st_mode & 0o077:
                raise ValueError("bindings must be private")
            config = json.loads(self.path.read_text())
            if not phone_number_id or config["phone_number_id"] != phone_number_id:
                raise KeyError("wrong destination")
            binding = config["senders"][hashlib.sha256(sender.encode()).hexdigest()]
            if not binding.get("active") or not binding.get("verified_at") or not binding.get("verification_source"):
                raise KeyError("unverified sender")
            actor = Actor.model_validate(binding["actor"])
        except (OSError, ValueError, KeyError, TypeError):
            raise ChannelError("sender_unbound", "The WhatsApp sender has no verified account binding.", 403) from None
        return (actor, binding) if with_options else actor


class Inbox:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self.connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS inbox (event_id TEXT PRIMARY KEY, state TEXT NOT NULL, updated REAL NOT NULL, result TEXT, owner TEXT)"
            )
        path.chmod(0o600)

    def connect(self):
        return sqlite3.connect(self.path, timeout=5)

    def claim(self, event_id: str, owner: str = "") -> bool:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT state, updated FROM inbox WHERE event_id=?", (event_id,)).fetchone()
            if row and row[0] == "review_required":
                return False
            if row and row[1] > time.time() - 120:
                raise ChannelError("message_processing", "This message is still being processed. Retry later.", 429)
            db.execute(
                "INSERT INTO inbox(event_id,state,updated,owner) VALUES(?, 'processing', ?, ?) "
                "ON CONFLICT(event_id) DO UPDATE SET state='processing',updated=excluded.updated",
                (event_id, time.time(), owner),
            )
        return True

    def finish(self, event_id: str, result: dict):
        with self.connect() as db:
            db.execute(
                "UPDATE inbox SET state='review_required', result=?,updated=? WHERE event_id=?",
                (json.dumps(result, ensure_ascii=False), time.time(), event_id),
            )

    def history(self, owner: str) -> list[dict]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT result FROM inbox WHERE owner=? AND state='review_required' ORDER BY updated DESC LIMIT 4",
                (owner,),
            ).fetchall()
        history = []
        for row in reversed(rows):
            result = json.loads(row[0])
            history += [
                {"role": "user", "content": result["input_text"][:4000]},
                {"role": "assistant", "content": result["response"]["reply"][:4000]},
            ]
        return history

    def result(self, event_id: str) -> dict | None:
        with self.connect() as db:
            row = db.execute(
                "SELECT result FROM inbox WHERE event_id=? AND state='review_required'", (event_id,)
            ).fetchone()
        return json.loads(row[0]) if row and row[0] else None

    def outbound_status(self, event_id: str, status: str):
        value = self.result(event_id)
        if value:
            value["outbound_status"] = status
            self.finish(event_id, value)

    def failed(self, event_id: str):
        with self.connect() as db:
            db.execute(
                "UPDATE inbox SET state=CASE WHEN result IS NULL THEN 'retryable' ELSE 'review_required' END,updated=0 WHERE event_id=?",
                (event_id,),
            )


class MetaMedia:
    def __init__(self, token: str, phone_number_id: str, *, client: httpx.AsyncClient | None = None):
        self.token, self.phone_number_id, self.client = token, phone_number_id, client

    async def download(self, media_id: str) -> tuple[bytes, str]:
        if not self.token or not re.fullmatch(r"[0-9]{1,80}", media_id):
            raise ChannelError(
                "whatsapp_media_unconfigured", "Authorized WhatsApp media access is required for voice notes."
            )
        version = settings()["DAYBREAK_META_GRAPH_VERSION"] or "v25.0"
        if not re.fullmatch(r"v\d{2}\.0", version):
            raise ChannelError("whatsapp_media_unconfigured", "The Meta Graph version is invalid.")

        async def read(client):
            headers = {"Authorization": "Bearer " + self.token}
            try:
                metadata = await client.get(
                    f"https://graph.facebook.com/{version}/{media_id}",
                    params={"phone_number_id": self.phone_number_id},
                    headers=headers,
                )
                metadata.raise_for_status()
                data = metadata.json()
                if str(data.get("id")) != media_id:
                    raise ChannelError(
                        "media_mismatch", "The voice note did not match its signed media identifier.", 422
                    )
                mime = data.get("mime_type", "").split(";")[0]
                url = urlparse(data.get("url", ""))
                if (
                    url.scheme != "https"
                    or url.hostname not in {"lookaside.fbsbx.com", "lookaside.facebook.com"}
                    or url.username
                    or url.password
                    or url.port not in {None, 443}
                ):
                    raise ChannelError("media_url_rejected", "The media URL is not an authorized Meta media host.", 422)
                if mime not in AUDIO_TYPES or int(data.get("file_size", MAX_AUDIO + 1)) > MAX_AUDIO:
                    raise ChannelError("media_type_rejected", "The voice note type or size is unsupported.", 422)
                chunks, length = [], 0
                async with client.stream("GET", data["url"], headers=headers) as audio:
                    audio.raise_for_status()
                    if audio.headers.get("content-type", "").split(";")[0] not in AUDIO_TYPES:
                        raise ChannelError("media_type_rejected", "Meta returned an unsupported media type.", 422)
                    async for chunk in audio.aiter_bytes():
                        length += len(chunk)
                        if length > MAX_AUDIO:
                            raise ChannelError("audio_size", "The voice note exceeds 10 MB.", 422)
                        chunks.append(chunk)
                body = b"".join(chunks)
                expected = data.get("sha256")
                digest = hashlib.sha256(body).digest()
                if not isinstance(expected, str) or not any(
                    hmac.compare_digest(candidate, expected)
                    for candidate in (digest.hex(), base64.b64encode(digest).decode())
                ):
                    raise ChannelError("media_integrity", "The voice note failed its media integrity check.", 422)
                return body, mime
            except (httpx.HTTPError, ValueError, TypeError):
                raise ChannelError("media_unavailable", "The voice note could not be retrieved from Meta.") from None

        if self.client:
            return await read(self.client)
        async with httpx.AsyncClient(timeout=25, follow_redirects=False) as client:
            return await read(client)


class WhatsAppAdapter:
    def __init__(
        self,
        conversation: ConversationService,
        bindings: Bindings,
        inbox: Inbox,
        *,
        media_factory=None,
        transcriber=None,
    ):
        self.conversation, self.bindings, self.inbox = conversation, bindings, inbox
        self.media_factory = media_factory or (
            lambda destination: MetaMedia(settings()["DAYBREAK_META_ACCESS_TOKEN"], destination)
        )
        self.transcriber = transcriber or ElevenLabs()

    async def receive(self, payload: dict) -> dict:
        if payload.get("object") != "whatsapp_business_account":
            raise ChannelError("webhook_invalid", "Unsupported webhook object.", 422)
        processed = duplicates = 0
        changes = [change for entry in payload.get("entry", []) for change in entry.get("changes", [])]
        if len(changes) > 10:
            raise ChannelError("webhook_limit", "The webhook batch is too large.", 422)
        for change in changes:
            value = change.get("value", {})
            destination = value.get("metadata", {}).get("phone_number_id", "")
            messages = value.get("messages", [])
            if len(messages) > 10:
                raise ChannelError("webhook_limit", "The webhook batch is too large.", 422)
            for message in messages:
                sender = message.get("from", "")
                if not isinstance(sender, str) or not sender or len(sender) > 150:
                    raise ChannelError("webhook_invalid", "A signed sender identifier is required.", 422)
                actor, options = self.bindings.resolve(destination, sender, with_options=True)
                # Revalidate the mapped actor against operations before downloading any media.
                self.conversation.operations.context(actor, "demo-vara")
                identifier = message.get("id", "")
                if not isinstance(identifier, str) or not 1 <= len(identifier) <= 250:
                    raise ChannelError("webhook_invalid", "A message identifier is required.", 422)
                event_id = "wa:" + hashlib.sha256((destination + ":" + identifier).encode()).hexdigest()
                owner = hashlib.sha256((actor.organization_id + ":" + actor.user_id).encode()).hexdigest()
                if not self.inbox.claim(event_id, owner):
                    duplicates += 1
                    continue
                try:
                    async with limits.acquire((actor.organization_id, actor.user_id)):
                        if message.get("type") == "text":
                            text = message.get("text", {}).get("body", "")
                            input_type = "text"
                        elif message.get("type") == "audio":
                            # Never accept a URL provided by the sender or a webhook attachment.
                            media_id = message.get("audio", {}).get("id", "")
                            audio, mime = await self.media_factory(destination).download(media_id)
                            text = await self.transcriber.transcribe(audio, mime)
                            input_type = "voice_note"
                        else:
                            raise ChannelError(
                                "message_type_unsupported", "Only text and voice notes are supported.", 422
                            )
                        request = ChatRequest(message=text, history=self.inbox.history(owner))
                        result = await self.conversation.chat(actor, request, event_key=event_id)
                        wants_audio = options.get("audio_replies_opted_in") is True and input_type == "voice_note"
                        stored = {
                            "input_type": input_type,
                            "input_text": text,
                            "reply_type": "text",
                            "audio_reply_path": None,
                            "response": result,
                            "outbound_status": "not_sent",
                            "confirmation": "authenticated_app_ui",
                            "tts": "pending" if wants_audio else "disabled_no_audio_reply_opt_in",
                        }
                        # The verified text is durable before optional TTS. An audio outage or interruption
                        # must never discard the reply or make a retry invoke Codex again.
                        self.inbox.finish(event_id, stored)
                        if wants_audio:
                            try:
                                generated = await self.transcriber.synthesize(result["reply"])
                                target = self.inbox.path.parent / "channels-audio-replies" / (event_id[3:] + ".mp3")
                                target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                                temporary = target.with_suffix(".mp3.tmp")
                                temporary.touch(mode=0o600, exist_ok=True)
                                temporary.write_bytes(generated)
                                temporary.chmod(0o600)
                                temporary.replace(target)
                                stored.update(
                                    reply_type="voice_note", audio_reply_path=str(target), tts="generated_not_sent"
                                )
                            except Exception as exc:  # noqa: BLE001 - optional audio must not discard verified text; no raw diagnostics.
                                stored.update(
                                    tts="failed_text_fallback",
                                    audio_error_code=exc.code if isinstance(exc, ChannelError) else "tts_failed",
                                )
                            self.inbox.finish(event_id, stored)
                        processed += 1
                except Exception:
                    self.inbox.failed(event_id)
                    raise
        return {"accepted": processed, "duplicates": duplicates, "send_enabled": False}


@router.get("/webhook")
async def handshake(request: Request):
    try:
        enabled()
        configured = settings()["DAYBREAK_META_VERIFY_TOKEN"]
        provided = request.query_params.get("hub.verify_token", "")
        if (
            not configured
            or request.query_params.get("hub.mode") != "subscribe"
            or not hmac.compare_digest(provided.encode(), configured.encode())
        ):
            raise ChannelError("webhook_verification", "Webhook verification failed.", 403)
        challenge = request.query_params.get("hub.challenge", "")
        if not re.fullmatch(r"[0-9]{1,100}", challenge):
            raise ChannelError("webhook_verification", "Invalid webhook challenge.", 422)
        return PlainTextResponse(challenge)
    except ChannelError as exc:
        raise HTTPException(exc.status_code, detail={"code": exc.code, "message": exc.message}) from None


@router.post("/webhook")
async def webhook(request: Request):
    try:
        enabled()
        chunks, size = [], 0
        async for chunk in request.stream():
            size += len(chunk)
            if size > MAX_BODY:
                raise ChannelError("webhook_size", "The webhook body exceeds its size limit.", 413)
            chunks.append(chunk)
        body = b"".join(chunks)
        verify_signature(body, request.headers.get("x-hub-signature-256"), settings()["DAYBREAK_META_APP_SECRET"])
        try:
            payload = json.loads(body)
        except (ValueError, UnicodeError):
            raise ChannelError("webhook_invalid", "Invalid JSON webhook.", 422) from None
        from cyberpunks.channels.whatsapp_queue import enqueue_payload
        from cyberpunks.channels.whatsapp_store import DeliveryStore

        # No Codex, STT, TTS or network send in the HTTP request. SQLite commits before ACK.
        return enqueue_payload(
            payload,
            Bindings(runtime_root() / "whatsapp-bindings.json"),
            DeliveryStore(runtime_root() / "channels-whatsapp.sqlite3"),
        )

    except ChannelError as exc:
        raise HTTPException(exc.status_code, detail={"code": exc.code, "message": exc.message}) from None
    except Exception:  # noqa: BLE001 - sanitize private webhook/provider failures at the boundary.
        raise HTTPException(
            503,
            detail={
                "code": "whatsapp_unavailable",
                "message": "The inbound message was not processed. No reply was sent.",
            },
        ) from None
