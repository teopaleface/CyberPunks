"""Validare și commit înainte de ACK. Funcția nu face apeluri de rețea sau inferență."""

from __future__ import annotations

import time

from cyberpunks.channels.models import ChannelError
from cyberpunks.channels.whatsapp_config import require_destination


def enqueue_payload(payload: dict, bindings, store) -> dict:
    if not isinstance(payload, dict) or payload.get("object") != "whatsapp_business_account":
        raise ChannelError("webhook_invalid", "Unsupported webhook object.", 422)
    entries = payload.get("entry", [])
    if not isinstance(entries, list) or len(entries) > 10:
        raise ChannelError("webhook_invalid", "Unsupported webhook batch.", 422)
    queued = duplicates = ignored = 0
    for entry in entries:
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("changes", []), list)
            or len(entry.get("changes", [])) > 10
        ):
            raise ChannelError("webhook_invalid", "Invalid webhook change.", 422)
        for change in entry.get("changes", []):
            if not isinstance(change, dict) or not isinstance(change.get("value"), dict):
                raise ChannelError("webhook_invalid", "Invalid webhook value.", 422)
            value = change["value"]
            destination = value.get("metadata", {}).get("phone_number_id", "")
            require_destination(destination)
            statuses = value.get("statuses", [])
            messages = value.get("messages", [])
            if (
                not isinstance(statuses, list)
                or not isinstance(messages, list)
                or len(statuses) > 100
                or len(messages) > 10
            ):
                raise ChannelError("webhook_limit", "The webhook batch exceeds its limit.", 422)
            for status in statuses:
                if not isinstance(status, dict):
                    raise ChannelError("webhook_invalid", "Invalid message status.", 422)
                store.reconcile(destination, status)
            for message in messages:
                if (
                    not isinstance(message, dict)
                    or not isinstance(message.get("from"), str)
                    or not 1 <= len(message["from"]) <= 150
                ):
                    raise ChannelError("webhook_invalid", "A signed sender is required.", 422)
                actor = bindings.resolve(destination, message["from"])
                if not isinstance(message.get("id"), str) or not 1 <= len(message["id"]) <= 250:
                    raise ChannelError("webhook_invalid", "A signed message identifier is required.", 422)
                try:
                    age = time.time() - int(message["timestamp"])
                except (ValueError, KeyError, TypeError):
                    raise ChannelError("inbound_timestamp_invalid", "A signed timestamp is required.", 422) from None
                if age < -60:
                    raise ChannelError("inbound_timestamp_invalid", "The inbound timestamp is in the future.", 422)
                if age >= 23 * 3600 or message.get("type") not in {"text", "audio"}:
                    ignored += 1
                    continue
                if message["type"] == "text":
                    text = message.get("text", {}).get("body", "")
                    if not isinstance(text, str) or not 1 <= len(text.strip()) <= 4000:
                        raise ChannelError("message_invalid", "The text message exceeds its supported limit.", 422)
                else:
                    media = message.get("audio", {}).get("id", "")
                    if not isinstance(media, str) or not media.isdigit() or len(media) > 80:
                        raise ChannelError("message_invalid", "A signed audio media identifier is required.", 422)
                if store.enqueue(destination, message["from"], message, actor):
                    queued += 1
                else:
                    duplicates += 1
    return {"queued": queued, "duplicates": duplicates, "ignored": ignored}
