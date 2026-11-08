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


async def tune_presentation(api: ElevenLabs) -> None:
    """Update only the existing Daybreak agents; retain their identities and private access."""
    config = get_config()
    agents, tools = {}, {}
    allowed = set(config["agents"].values())
    for role in ROLES:
        agent_id = config["agents"][role]
        agent = await api.request("GET", f"/v1/convai/agents/{agent_id}")
        verify_agent(agent)
        if agent.get("name") != f"Daybreak private {role}":
            raise ChannelError("agent_identity_mismatch", "Presentation tuning requires the existing Daybreak agents.")
        agents[role] = agent
        for tool_id in agent["conversation_config"]["agent"]["prompt"].get("tool_ids", []):
            if tool_id in tools:
                continue
            dependent = await api.request("GET", f"/v1/convai/tools/{tool_id}/dependent-agents")
            dependencies = dependent.get("agents", [])
            if (
                not dependencies or dependent.get("has_more") or dependent.get("next_cursor")
                or any(a.get("id") not in allowed for a in dependencies)
                or any(b.get("agent_id") not in allowed for b in dependent.get("branches", []))
            ):
                raise ChannelError("shared_voice_tool", "This tool is used outside Daybreak; it was preserved.")
            tool = await api.request("GET", f"/v1/convai/tools/{tool_id}")
            if tool.get("tool_config", {}).get("name") != "daybreak_turn":
                raise ChannelError("unexpected_voice_tool", "An unexpected tool was preserved.")
            tools[tool_id] = tool
    # Contains configuration only, never API keys or temporary conversation tokens.
    root = runtime_root()
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    snapshot = root / f"voice-before-presentation-{stamp}.json"
    with os.fdopen(os.open(snapshot, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as handle:
        json.dump({"agents": agents, "tools": tools}, handle, ensure_ascii=False, indent=2)
    for tool_id, previous in tools.items():
        updated = dict(previous["tool_config"])
        for legacy in ("disable_interruptions", "force_pre_tool_speech"):
            updated.pop(legacy, None)
        updated.update({"pre_tool_speech": "force", "interruption_mode": "disable_during_tool_and_turn"})
        await api.request("PATCH", f"/v1/convai/tools/{tool_id}", json={
            "tool_config": updated, "response_mocks": previous.get("response_mocks"),
        })
    for role, previous in agents.items():
        agent_id = config["agents"][role]
        current = previous["conversation_config"]
        desired = agent_config(role, current["tts"]["voice_id"])
        voice = desired["conversation_config"]
        patch = {
            "conversation_config": {
                "asr": voice["asr"], "vad": voice["vad"], "turn": voice["turn"], "tts": voice["tts"],
                "conversation": {"max_duration_seconds": voice["conversation"]["max_duration_seconds"]},
                "agent": {
                    "first_message": voice["agent"]["first_message"],
                    "prompt": {"prompt": voice["agent"]["prompt"]["prompt"]},
                },
            },
            "platform_settings": {"call_limits": desired["platform_settings"]["call_limits"]},
        }
        await api.request("PATCH", f"/v1/convai/agents/{agent_id}", json=patch)
        persisted = await api.request("GET", f"/v1/convai/agents/{agent_id}")
        verify_agent(persisted)
        actual = persisted["conversation_config"]
        checks = (
            actual["vad"]["background_voice_detection"] is True,
            actual["tts"]["model_id"] == voice["tts"]["model_id"],
            actual["tts"]["expressive_mode"] is True,
            actual["turn"]["turn_eagerness"] == "eager",
            actual["turn"]["turn_timeout"] == 5,
            actual["conversation"]["max_duration_seconds"] == voice["conversation"]["max_duration_seconds"],
            actual["agent"]["prompt"]["prompt"] == voice["agent"]["prompt"]["prompt"],
            all(t.get("pre_tool_speech") == "force" and
                t.get("interruption_mode") == "disable_during_tool_and_turn"
                for t in actual["agent"]["prompt"]["tools"]),
            persisted["platform_settings"]["call_limits"]["daily_limit"] == 30,
            persisted["platform_settings"]["privacy"] == previous["platform_settings"]["privacy"],
        )
        if not all(checks):
            raise ChannelError("voice_tuning_not_persisted", "The presentation configuration did not pass reread checks.")
        print(role, "presentation configuration persisted; authentication, tools and privacy verified.")
    print("Three existing agents updated. No conversations started and no WhatsApp messages sent.")


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
    if mode == "tune-presentation":
        await tune_presentation(api)
        return
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
    parser.add_argument("mode", choices=[
        "preflight", "provision", "verify", "tune-presentation", "whatsapp-worker", "whatsapp-status",
    ])
    args = parser.parse_args()
    try:
        asyncio.run(run(args.mode))
    except ChannelError as exc:
        parser.exit(1, f"{exc.code}: {exc.message}\n")
