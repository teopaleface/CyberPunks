#!/usr/bin/env python3
"""Configure inbound-only WhatsApp SIP calls for the existing verified Daybreak sender."""

from __future__ import annotations

import argparse
import asyncio
import re
import secrets
import socket
import sqlite3
import ssl
from urllib.parse import urlparse

import httpx
from daybreak_whatsapp_setup import CONFIG, PHONE_ID, private_env

from cyberpunks.channels.elevenlabs import ElevenLabs, get_config, runtime_root
from cyberpunks.channels.models import ChannelError
from cyberpunks.channels.whatsapp import Bindings
from cyberpunks.channels.whatsapp_calls import call_agent_config, load_config, save_config, verify_public_tool

NUMBER = "+15551545755"
LABEL = "Daybreak WhatsApp incoming demo"


def prepare() -> None:
    config = load_config()
    bindings = Bindings(runtime_root() / "whatsapp-bindings.json")
    allowed = []
    with sqlite3.connect(f"file:{runtime_root() / 'channels-whatsapp.sqlite3'}?mode=ro", uri=True) as db:
        senders = db.execute("SELECT DISTINCT sender FROM inbound_queue WHERE destination=?", (PHONE_ID,)).fetchall()
    for (sender,) in senders:
        try:
            actor = bindings.resolve(PHONE_ID, sender)
        except ChannelError:
            continue
        if actor.role == "technician" and re.fullmatch(r"[0-9]{5,20}", sender):
            allowed.append(sender)
    if len(allowed) != 1:
        raise ChannelError("calling_sender_ambiguous", "The private call demo needs the one existing verified technician.")
    config["phone_number_id"] = PHONE_ID
    config["allowed_callers"] = allowed
    config.setdefault("tool_token", secrets.token_urlsafe(48))
    save_config(config)
    print("Private call authorization prepared for the one existing verified technician. No calls or messages sent.")


def check_agent(agent: dict, config: dict) -> None:
    c = agent["conversation_config"]
    prompt = c["agent"]["prompt"]
    tools = prompt.get("tools", [])
    expected = call_agent_config(get_config()["voice_id"], config["public_origin"], config["secret_id"])
    tool = expected["conversation_config"]["agent"]["prompt"]["tools"][0]
    if not (
        agent.get("name") == "Daybreak WhatsApp calls"
        and agent["platform_settings"]["auth"]["enable_auth"]
        and not agent["platform_settings"]["privacy"]["record_voice"]
        and c["conversation"]["max_duration_seconds"] == 600
        and c["tts"]["model_id"] == "eleven_v4_turbo"
        and c["vad"]["background_voice_detection"]
        and not prompt.get("mcp_server_ids") and not prompt.get("knowledge_base")
        and not prompt.get("native_mcp_server_ids") and not any(prompt.get("built_in_tools", {}).values())
        and len(tools) == 1 and tools[0]["type"] == "webhook"
        and tools[0]["name"] == tool["name"]
        and tools[0]["api_schema"]["url"] == tool["api_schema"]["url"]
        and tools[0]["api_schema"]["request_headers"] == tool["api_schema"]["request_headers"]
        and tools[0].get("follow_redirects") is False
        and all(
            tools[0]["api_schema"]["request_body_schema"]["properties"][key].get("dynamic_variable") == variable
            for key, variable in [("caller_id", "system__caller_id"), ("conversation_id", "system__conversation_id")]
        )
    ):
        raise ChannelError("calling_agent_mismatch", "The call agent did not pass scoped configuration checks.")


async def configure(origin: str) -> None:
    url = urlparse(origin)
    if not (
        url.scheme == "https" and url.hostname and url.hostname.endswith(".trycloudflare.com")
        and url.port in (None, 443) and not any((url.username, url.password, url.path.rstrip("/"), url.query, url.fragment))
    ):
        raise ChannelError("calling_origin_invalid", "Use the HTTPS origin of the dedicated call-tool tunnel.")
    config = load_config()
    if not config.get("tool_token") or len(config.get("allowed_callers", [])) != 1:
        raise ChannelError("calling_unprepared", "Prepare private call authorization before configuring the agent.")
    config["public_origin"] = origin.rstrip("/")
    save_config(config)
    api = ElevenLabs()
    if not config.get("secret_id"):
        # Do not repeat an uncertain create. Persist each returned resource immediately.
        if config.get("secret_creation_attempted"):
            raise ChannelError("calling_creation_unknown", "Inspect the previous call-secret creation before retrying.")
        config["secret_creation_attempted"] = True
        save_config(config)
        result = await api.request("POST", "/v1/convai/secrets", json={
            "type": "new", "name": "Daybreak WhatsApp calls authorization", "value": "Bearer " + config["tool_token"],
        })
        config["secret_id"] = result.get("secret_id") or result.get("id")
        if not config["secret_id"]:
            raise ChannelError("calling_creation_unknown", "The call secret returned no identifier; no retry was made.")
        save_config(config)
    desired = call_agent_config(get_config()["voice_id"], config["public_origin"], config["secret_id"])
    if not config.get("agent_id"):
        if config.get("agent_creation_attempted"):
            raise ChannelError("calling_creation_unknown", "Inspect the previous call-agent creation before retrying.")
        config["agent_creation_attempted"] = True
        save_config(config)
        result = await api.request("POST", "/v1/convai/agents/create", json=desired)
        config["agent_id"] = result.get("agent_id")
        if not config["agent_id"]:
            raise ChannelError("calling_creation_unknown", "The call agent returned no identifier; no retry was made.")
        save_config(config)
    else:
        current = await api.request("GET", f"/v1/convai/agents/{config['agent_id']}")
        if current.get("name") != desired["name"]:
            raise ChannelError("calling_agent_mismatch", "An unrelated agent was preserved.")
        # Update the tool itself, retaining its identity and avoiding duplicate inline tools.
        ids = current["conversation_config"]["agent"]["prompt"].get("tool_ids", [])
        if len(ids) != 1:
            raise ChannelError("calling_agent_mismatch", "The call agent has unexpected tools.")
        await api.request("PATCH", f"/v1/convai/tools/{ids[0]}", json={
            "tool_config": desired["conversation_config"]["agent"]["prompt"]["tools"][0],
        })
    check_agent(await api.request("GET", f"/v1/convai/agents/{config['agent_id']}"), config)
    if not config.get("elevenlabs_phone_id"):
        phones = await api.request("GET", "/v1/convai/phone-numbers")
        existing = [p for p in phones if p.get("phone_number") == NUMBER]
        if existing:
            if len(existing) != 1 or existing[0].get("label") != LABEL:
                raise ChannelError("calling_number_in_use", "An existing unrelated phone configuration was preserved.")
            config["elevenlabs_phone_id"] = existing[0]["phone_number_id"]
        else:
            if config.get("phone_creation_attempted"):
                raise ChannelError("calling_creation_unknown", "Inspect the previous SIP-number creation before retrying.")
            password = config["meta_settings"]["calling"]["sip"]["servers"][0]["sip_user_password"]
            config["phone_creation_attempted"] = True
            save_config(config)
            result = await api.request("POST", "/v1/convai/phone-numbers", json={
                "provider": "sip_trunk", "phone_number": NUMBER, "label": LABEL,
                "agent_id": config["agent_id"], "supports_inbound": True, "supports_outbound": False,
                "inbound_trunk_config": {
                    "media_encryption": "required", "allowed_addresses": ["0.0.0.0/0", "::/0"],
                    "allowed_numbers": ["+" + caller for caller in config["allowed_callers"]],
                    "credentials": {"username": NUMBER.removeprefix("+"), "password": password},
                    "remote_domains": ["wa.meta.vc"],
                },
            })
            config["elevenlabs_phone_id"] = result.get("phone_number_id")
        if not config.get("elevenlabs_phone_id"):
            raise ChannelError("calling_creation_unknown", "The SIP number returned no identifier; no retry was made.")
        save_config(config)
    await api.request("PATCH", f"/v1/convai/phone-numbers/{config['elevenlabs_phone_id']}", json={
        "agent_id": config["agent_id"], "store_sip_messages": False,
    })
    await verify()


async def verify() -> None:
    config = load_config()
    await verify_public_tool(config["public_origin"])
    api = ElevenLabs()
    check_agent(await api.request("GET", f"/v1/convai/agents/{config['agent_id']}"), config)
    phone = await api.request("GET", f"/v1/convai/phone-numbers/{config['elevenlabs_phone_id']}")
    inbound = phone.get("inbound_trunk", {})
    checks = (
        phone.get("phone_number") == NUMBER and phone.get("provider") == "sip_trunk",
        phone.get("assigned_agent", {}).get("agent_id") == config["agent_id"],
        inbound.get("has_auth_credentials") is True and inbound.get("media_encryption") == "required",
        set(inbound.get("allowed_numbers", [])) == {"+" + x for x in config["allowed_callers"]},
        not phone.get("outbound_trunk") and phone.get("store_sip_messages") is False,
    )
    if not all(checks):
        raise ChannelError("calling_route_mismatch", "The inbound SIP route did not pass reread checks.")
    values = private_env(CONFIG)
    async with httpx.AsyncClient(timeout=25, follow_redirects=False) as client:
        response = await client.get(
            "https://graph.facebook.com/" + values["DAYBREAK_META_GRAPH_VERSION"] + "/" + PHONE_ID + "/settings",
            headers={"Authorization": "Bearer " + values["DAYBREAK_META_ACCESS_TOKEN"]},
        )
    if not response.is_success:
        raise ChannelError("calling_meta_unavailable", "Meta calling configuration could not be verified.")
    calling = response.json().get("calling", {})
    sip = calling.get("sip", {})
    servers = sip.get("servers", [])
    if not (
        calling.get("status") == "ENABLED" and sip.get("status") == "ENABLED"
        and calling.get("srtp_key_exchange_protocol") == "SDES"
        and len(servers) == 1 and servers[0].get("hostname") == "sip.rtc.elevenlabs.io"
        and int(servers[0].get("port", 5061)) == 5061
        and {"PCMA", "PCMU"}.issubset(calling.get("audio", {}).get("additional_codecs", []))
    ):
        raise ChannelError("calling_meta_mismatch", "Meta SIP routing or audio configuration changed.")
    context = ssl.create_default_context()
    with (
        socket.create_connection(("sip.rtc.elevenlabs.io", 5061), timeout=10) as connection,
        context.wrap_socket(connection, server_hostname="sip.rtc.elevenlabs.io") as tls,
    ):
        if not tls.version():
            raise ChannelError("calling_tls_unavailable", "The SIP TLS handshake did not finish.")
    print("Meta SIP route, call agent, caller-bound server tool, digest authentication and encrypted media verified.")
    print("SIP TLS certificate verified. No WhatsApp call or message was started.")


def show_button() -> None:
    config = load_config()
    if not config.get("elevenlabs_phone_id"):
        raise ChannelError("calling_unconfigured", "Configure the inbound route before showing the call button.")
    values = private_env(CONFIG)
    with httpx.Client(timeout=25, follow_redirects=False) as client:
        url = "https://graph.facebook.com/" + values["DAYBREAK_META_GRAPH_VERSION"] + "/" + PHONE_ID + "/settings"
        headers = {"Authorization": "Bearer " + values["DAYBREAK_META_ACCESS_TOKEN"]}
        result = client.post(url, headers=headers, json={"calling": {"status": "ENABLED", "call_icon_visibility": "DEFAULT"}})
        if not result.is_success or result.json().get("success") is not True:
            raise ChannelError("calling_button_unconfirmed", "Meta did not confirm the call-button setting.")
        calling = client.get(url, headers=headers).json().get("calling", {})
        if calling.get("status") != "ENABLED" or calling.get("call_icon_visibility") != "DEFAULT":
            raise ChannelError("calling_button_unconfirmed", "The call-button setting did not persist.")
    print("WhatsApp incoming calling and call-button visibility confirmed by Meta API.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["prepare", "configure", "verify", "show-call-button"])
    parser.add_argument("--public-origin")
    args = parser.parse_args()
    try:
        if args.mode == "prepare":
            prepare()
        elif args.mode == "configure":
            if not args.public_origin:
                parser.error("--public-origin is required")
            asyncio.run(configure(args.public_origin))
        elif args.mode == "verify":
            asyncio.run(verify())
        else:
            asyncio.run(verify())
            show_button()
    except ChannelError as exc:
        parser.exit(1, f"{exc.code}: {exc.message}\n")
