"""Răspunsuri Meta Graph doar către expeditorul autentificat al mesajului primit."""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import time

import httpx

from cyberpunks.channels.models import ChannelError
from cyberpunks.channels.whatsapp_config import require_destination, require_sending
from cyberpunks.channels.whatsapp_store import DeliveryStore, actor_key


async def _json_response(client, method: str, url: str, **kwargs) -> tuple[int, dict]:
    chunks, size = [], 0
    async with client.stream(method, url, **kwargs) as response:
        async for chunk in response.aiter_bytes():
            size += len(chunk)
            if size > 64_000:
                raise ChannelError("meta_response_limit", "Meta returned an oversized response.")
            chunks.append(chunk)
        try:
            body = json.loads(b"".join(chunks))
        except (ValueError, UnicodeError):
            raise ChannelError("meta_response_invalid", "Meta returned an invalid response.") from None
        if not isinstance(body, dict):
            raise ChannelError("meta_response_invalid", "Meta returned an invalid response.")
        return response.status_code, body


async def voice_note(mp3: bytes) -> bytes:
    """Meta voice=true requires OGG/Opus; never label an MP3 attachment as a voice note."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg or not mp3 or len(mp3) > 2_000_000:
        raise ChannelError("voice_encoding_unavailable", "Voice reply encoding is unavailable.")
    proc = await asyncio.create_subprocess_exec(
        ffmpeg,
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-protocol_whitelist",
        "pipe",
        "-f",
        "mp3",
        "-i",
        "pipe:0",
        "-t",
        "120",
        "-vn",
        "-ac",
        "1",
        "-ar",
        "48000",
        "-c:a",
        "libopus",
        "-b:a",
        "24k",
        "-f",
        "ogg",
        "pipe:1",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={"PATH": os.getenv("PATH", "/opt/homebrew/bin:/usr/bin:/bin")},
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(mp3), timeout=15)
        if proc.returncode or not out.startswith(b"OggS") or b"OpusHead" not in out[:200] or len(out) > 2_000_000:
            raise ChannelError("voice_encoding_failed", "The audio reply could not be encoded as a voice note.")
        return out
    except TimeoutError:
        raise ChannelError("voice_encoding_timeout", "Voice reply encoding timed out.") from None
    finally:
        if proc.returncode is None:
            proc.kill()
            await proc.wait()


class MetaTransport:
    def __init__(self, bindings, operations, ledger: DeliveryStore, *, client: httpx.AsyncClient | None = None):
        self.bindings, self.operations, self.ledger, self.client = bindings, operations, ledger, client

    def authorize(self, inbound: dict, *, audio=False) -> dict:
        config = require_sending()
        require_destination(inbound["destination"])
        actor, options = self.bindings.resolve(inbound["destination"], inbound["sender"], with_options=True)
        if actor_key(actor) != inbound["actor_signature"]:
            raise ChannelError(
                "sender_binding_changed", "The sender binding changed. A new authenticated message is required.", 403
            )
        self.operations.context(actor, "demo-vara")
        if audio and options.get("audio_replies_opted_in") is not True:
            raise ChannelError(
                "audio_reply_not_opted_in", "The verified sender has not opted in to voice replies.", 403
            )
        try:
            age = time.time() - int(inbound["message"]["timestamp"])
        except (ValueError, KeyError, TypeError):
            raise ChannelError("inbound_timestamp_invalid", "A verified inbound timestamp is required.", 422) from None
        if not -60 <= age < 23 * 3600:
            raise ChannelError(
                "reply_window_expired", "The reply window has expired. A new inbound message is required.", 409
            )
        return config

    def check_report_source(self, inbound: dict):
        frozen = self.ledger.report_version(inbound["event_id"])
        if not frozen:
            return
        actor = self.bindings.resolve(inbound["destination"], inbound["sender"])
        current = self.operations.context(actor, "demo-vara")
        current_cases = {case["case_id"]: case.get("version") for case in current.get("cases", [])}
        if current["plan"]["version"] != frozen or any(
            current_cases.get(key) != version for key, version in self.ledger.report_cases(inbound["event_id"]).items()
        ):
            raise ChannelError("report_stale", "The report source changed. Request a fresh report.", 409)

    async def send(
        self,
        inbound: dict,
        *,
        text: str | None = None,
        audio: bytes | None = None,
        image: bytes | None = None,
        image_key: str | None = None,
    ) -> str:
        if sum(x is not None for x in (text, audio, image)) != 1:
            raise ChannelError("outbound_invalid", "A reply must contain exactly one supported message type.", 422)
        if text is not None and not 1 <= len(text) <= 4096:
            raise ChannelError("outbound_invalid", "The text reply exceeds its supported limit.", 422)
        if audio is not None and (
            len(audio) > 2_000_000 or not audio.startswith(b"OggS") or b"OpusHead" not in audio[:200]
        ):
            raise ChannelError("outbound_invalid", "Voice replies must be bounded OGG/Opus audio.", 422)
        if image is not None and (
            len(image) > 4_000_000
            or not image.startswith(b"\x89PNG\r\n\x1a\n")
            or not image_key
            or not re.fullmatch(r"[A-Za-z0-9_-]{1,160}", image_key)
        ):
            raise ChannelError("outbound_invalid", "A bounded PNG and stable page identifier are required.", 422)
        config = self.authorize(inbound, audio=audio is not None)
        version = config["DAYBREAK_META_GRAPH_VERSION"] or "v25.0"
        if not re.fullmatch(r"v\d{2}\.0", version):
            raise ChannelError("whatsapp_unconfigured", "The configured Meta Graph version is invalid.")
        if image is not None:
            self.check_report_source(inbound)
        base = "https://graph.facebook.com/" + version + "/" + inbound["destination"]
        kind = "image" if image is not None else "audio" if audio is not None else "text"
        content = image if image is not None else audio if audio is not None else text.encode()
        part_kind = "image:" + image_key if image is not None else kind
        row = self.ledger.prepare(inbound["event_id"], inbound["destination"], inbound["sender"], part_kind, content)
        if row["state"] in {"accepted", "delivered", "read"}:
            return row["state"]
        if row["state"] != "prepared":
            # In-flight/unknown outcomes must be reconciled by a signed status callback or an operator.
            return row["state"]
        headers = {"Authorization": "Bearer " + config["DAYBREAK_META_ACCESS_TOKEN"]}

        async def deliver(client):
            media_id = row["media_id"]
            if (audio is not None or image is not None) and not media_id:
                # Uploading again cannot send a user message. Only the message POST is at-most-once.
                try:
                    status, data = await _json_response(
                        client,
                        "POST",
                        base + "/media",
                        headers=headers,
                        data={
                            "messaging_product": "whatsapp",
                            "type": "image/png" if image is not None else "audio/ogg",
                        },
                        files={
                            "file": ("daybreak-report.png", image, "image/png")
                            if image is not None
                            else ("daybreak-reply.ogg", audio, "audio/ogg")
                        },
                    )
                except httpx.HTTPError:
                    raise ChannelError("meta_upload_unavailable", "The voice reply upload did not finish.") from None
                media_id = data.get("id")
                if not 200 <= status < 300 or not isinstance(media_id, str) or not re.fullmatch(r"\d{1,80}", media_id):
                    raise ChannelError("meta_upload_rejected", "Meta did not accept the voice reply upload.")
                self.ledger.outbound_state(row["part_id"], "prepared", media_id=media_id)
            # Recheck flags, sender mapping and scope immediately before the irreversible network POST.
            self.authorize(inbound, audio=audio is not None)
            if image is not None:
                self.check_report_source(inbound)
            if not self.ledger.begin_send(row["part_id"]):
                return "unknown"
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": inbound["sender"],
                "context": {"message_id": inbound["message"]["id"]},
                "type": kind,
                "biz_opaque_callback_data": row["part_id"],
            }
            if text is not None:
                payload["text"] = {"preview_url": False, "body": text}
            elif image is not None:
                payload["image"] = {"id": media_id}
            else:
                payload["audio"] = {"id": media_id, "voice": True}
            try:
                status, data = await _json_response(client, "POST", base + "/messages", headers=headers, json=payload)
                messages = data.get("messages", [])
                message_id = (
                    messages[0].get("id")
                    if isinstance(messages, list) and messages and isinstance(messages[0], dict)
                    else None
                )
                if 200 <= status < 300 and isinstance(message_id, str) and message_id.startswith("wamid."):
                    return self.ledger.outbound_state(row["part_id"], "accepted", message_id=message_id)
                state = "rejected" if 400 <= status < 500 else "unknown"
                code = "meta_rejected" if state == "rejected" else "meta_outcome_unknown"
                graph_code = data.get("error", {}).get("code") if isinstance(data.get("error"), dict) else None
                if state == "rejected" and type(graph_code) is int and 0 < graph_code < 1_000_000:
                    code += "_" + str(graph_code)
                return self.ledger.outbound_state(row["part_id"], state, code=code)
            except (httpx.HTTPError, ChannelError):
                return self.ledger.outbound_state(row["part_id"], "unknown", code="meta_outcome_unknown")

        if self.client:
            return await deliver(self.client)
        async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
            return await deliver(client)
