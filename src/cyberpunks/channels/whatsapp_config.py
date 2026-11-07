"""Configurare WhatsApp privată, fără diagnosticarea valorilor din fișiere."""

from __future__ import annotations

import ipaddress
import os
import re
from urllib.parse import quote, urlparse

from cyberpunks.channels.elevenlabs import runtime_root
from cyberpunks.channels.models import ChannelError

KEYS = {
    "DAYBREAK_META_ACCESS_TOKEN",
    "DAYBREAK_META_PHONE_NUMBER_ID",
    "DAYBREAK_META_MESSAGING_ACCOUNT_ID",
    "DAYBREAK_META_GRAPH_VERSION",
    "DAYBREAK_META_APP_SECRET",
    "DAYBREAK_META_VERIFY_TOKEN",
    "DAYBREAK_WHATSAPP_ENABLED",
    "DAYBREAK_WHATSAPP_SEND_ENABLED",
    "DAYBREAK_PUBLIC_APP_ORIGIN",
}


def settings() -> dict[str, str]:
    values = {key: os.getenv(key, "") for key in KEYS}
    path = runtime_root() / "meta-whatsapp.env"
    if path.is_file():
        if path.stat().st_mode & 0o077:
            raise ChannelError("whatsapp_config_permissions", "The Meta credential file must be private.")
        for line in path.read_text().splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() in KEYS:
                values[key.strip()] = value.strip().strip("\"'")
    return values


def require_destination(destination: str) -> None:
    configured = settings()["DAYBREAK_META_PHONE_NUMBER_ID"]
    if not configured:
        raise ChannelError("whatsapp_unconfigured", "The verified Meta phone identifier is not configured.")
    if destination != configured:
        raise ChannelError("destination_forbidden", "This webhook destination is not enabled.", 403)


def require_sending() -> dict:
    config = settings()
    if config["DAYBREAK_WHATSAPP_ENABLED"] != "1" or config["DAYBREAK_WHATSAPP_SEND_ENABLED"] != "1":
        raise ChannelError("whatsapp_sending_disabled", "WhatsApp reply sending is disabled.")
    if not config["DAYBREAK_META_ACCESS_TOKEN"] or not re.fullmatch(
        r"\d{1,80}", config["DAYBREAK_META_PHONE_NUMBER_ID"]
    ):
        raise ChannelError("whatsapp_unconfigured", "The Meta reply transport is not configured.")
    return config


def confirmation_text(response: dict) -> str:
    text = response["reply"]
    if not response.get("proposal"):
        return text
    ro = response.get("language") == "ro"
    # No public app origin is inferred from the webhook, the message or any model output.
    origin = settings()["DAYBREAK_PUBLIC_APP_ORIGIN"].rstrip("/")
    url = urlparse(origin)
    valid = (
        url.scheme == "https"
        and bool(url.hostname)
        and not url.username
        and not url.password
        and not url.query
        and not url.fragment
        and not url.path
        and url.port in {None, 443}
    )
    if valid:
        try:
            valid = ipaddress.ip_address(url.hostname).is_global
        except ValueError:
            valid = url.hostname != "localhost" and not url.hostname.endswith(".local")
    if valid:
        return (
            text
            + (
                " Deschide aplicația autentificată pentru verificare: "
                if ro
                else " Open the authenticated app to review the request: "
            )
            + origin
            + "/workspace?proposal="
            + quote(response["proposal"]["proposal_id"], safe="")
        )
    return text + (
        " Confirmarea rămâne în așteptare; nu există acum un link public configurat către aplicație."
        if ro
        else " Confirmation is still pending; no public app link is configured."
    )
