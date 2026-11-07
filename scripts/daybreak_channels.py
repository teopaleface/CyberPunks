#!/usr/bin/env python3
"""Agenți privați și worker pentru răspunsuri WhatsApp autorizate la mesaje primite.

.venv/bin/python scripts/daybreak_channels.py preflight
.venv/bin/python scripts/daybreak_channels.py provision
.venv/bin/python scripts/daybreak_channels.py verify
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import UTC, datetime

from cyberpunks.channels.elevenlabs import ROLES, ElevenLabs, agent_config, get_config, runtime_root, verify_agent
from cyberpunks.channels.models import ChannelError


def save(config: dict) -> None:
    root = runtime_root()
    root.mkdir(parents=True, exist_ok=True)
    path = root / "channels.json"
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(config, indent=2) + "\n")
    os.replace(temp, path)


async def run(mode: str) -> None:
    if mode in {"whatsapp-worker", "whatsapp-status"}:
        from cyberpunks.channels.whatsapp_store import DeliveryStore

        if mode == "whatsapp-status":
            print(json.dumps(DeliveryStore(runtime_root() / "channels-whatsapp.sqlite3").counts()))
        else:
            from cyberpunks.channels.whatsapp_worker import run_worker

            await run_worker()
        return
    api = ElevenLabs()
    if mode in {"preflight", "provision"}:
        # This must succeed before any creation. No billing/settings mutation.
        await api.request("GET", "/v1/user/subscription")
        print("ElevenLabs account authentication: OK")
        voices = await api.request("GET", "/v2/voices", params={"page_size": 30})
        candidates = voices.get("voices", [])
        if not candidates:
            raise ChannelError("voices_missing", "No available voice was returned by this account.")
        voice_id = next((v["voice_id"] for v in candidates if v.get("name") == "Sarah"), candidates[0]["voice_id"])
        wa = await api.request("GET", "/v1/convai/whatsapp-accounts")
        accounts = wa if isinstance(wa, list) else wa.get("items", wa.get("whatsapp_accounts", wa.get("accounts", [])))
        print("WhatsApp connected number count:", len(accounts))
        # Do not print phone numbers, account identifiers or quota/billing objects.
        if mode == "preflight":
            return
        try:
            config = get_config()
        except ChannelError:
            config = {"agents": {}, "created_at": datetime.now(UTC).isoformat(), "whatsapp_enabled": False}
        for role in ROLES:
            if role not in config["agents"]:
                # One creation attempt per role. On unknown transport failure do not blindly retry.
                result = await api.request("POST", "/v1/convai/agents/create", json=agent_config(role, voice_id))
                agent_id = result.get("agent_id")
                if not agent_id:
                    raise ChannelError(
                        "agent_creation_unknown", "Agent creation returned no ID. Inspect the account before retrying."
                    )
                config["agents"][role] = agent_id
                config["voice_id"] = voice_id
                save(config)  # Persist each ID immediately so successful creates are never repeated.
            await api.request("GET", f"/v1/convai/agents/{config['agents'][role]}")
        print("Three role agents created or recovered. Verifying live settings and temporary sessions.")
    if mode in {"verify", "provision"}:
        config = get_config()
        for role in ROLES:
            agent_id = config["agents"].get(role)
            if not agent_id:
                raise ChannelError("agent_missing", f"Agent for {role} is missing.")
            agent = await api.request("GET", f"/v1/convai/agents/{agent_id}")
            verify_agent(agent)
            session = await api.session(role)
            print(
                role,
                "private agent GET: OK; temporary WebRTC token:",
                "issued" if session.get("conversation_token") else "missing",
            )
        config["verified_at"] = datetime.now(UTC).isoformat()
        save(config)
        print("Session preflight complete. Microphone/speaker verification remains separate. No phone/message sends.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["preflight", "provision", "verify", "whatsapp-worker", "whatsapp-status"])
    args = parser.parse_args()
    try:
        asyncio.run(run(args.mode))
    except ChannelError as exc:
        parser.exit(1, f"{exc.code}: {exc.message}\n")
