"""Opt-in real voice QA using synthetic audio, never a microphone or an operational write.

One bounded session per invocation. Run only with explicit provider-test authorization.
Secrets, cookies, signed URLs and raw provider events are never logged or saved.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import re
import subprocess
import time
import unicodedata
import wave
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

import httpx
import websockets
from daybreak_runtime import read_private_env

from cyberpunks.channels.codex import PROVIDER
from cyberpunks.channels.elevenlabs import ElevenLabs, get_config, verify_agent

BASE = "http://127.0.0.1:3870"
OUT = Path("/tmp/daybreak-voice-qa")
UTTERANCE = "Salut! Ce informații vezi despre sesizările mele?"


class ProbeError(Exception):
    """Only locally authored, secret-free messages may be attached."""


def check_http(response: httpx.Response, step: str) -> dict:
    if response.status_code != 200:
        raise ProbeError(f"{step}: HTTP {response.status_code}")
    return response.json()


def context_digest(context: dict) -> str:
    snapshot = {key: context.get(key) for key in ("cases", "plan", "connections", "work_items")}
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def normalized(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).split())


def audio_rate(audio_format: str) -> int:
    match = re.fullmatch(r"pcm_(\d+)", audio_format)
    if not match or not 8000 <= int(match[1]) <= 48000:
        raise ProbeError("Unsupported audio format; no format assumptions applied")
    return int(match[1])


def save_wav(path: Path, chunks: list[bytes], rate: int) -> None:
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(b"".join(chunks))


def media_info(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=codec_name,sample_rate,channels,bits_per_sample:format=duration,size", "-of", "json", str(path)],
        capture_output=True, check=True,
    )
    return json.loads(result.stdout)


async def run_session(client: httpx.AsyncClient, provider: ElevenLabs, pcm: bytes, report: dict, output: Path):
    agent_id = get_config()["agents"]["customer"]
    agent = await provider.request("GET", f"/v1/convai/agents/{agent_id}")
    verify_agent(agent)
    report["private_agent_verified"] = True
    signed = await provider.request("GET", "/v1/convai/conversation/get-signed-url", params={"agent_id": agent_id})
    url = signed.get("signed_url", "")
    parsed = urlsplit(url)
    if parsed.scheme != "wss" or parsed.hostname != "api.elevenlabs.io":
        raise ProbeError("Provider did not return an official signed WebSocket URL")

    started = time.monotonic()
    timing = report["timing_seconds"] = {}
    counts = Counter()
    report["event_counts"] = counts
    audio = {"greeting": [], "response": []}
    tool_tasks = []
    sender = None
    response_audio_at = None
    metadata = asyncio.Event()
    tool_done = asyncio.Event()

    def stamp(name: str):
        timing.setdefault(name, round(time.monotonic() - started, 3))

    async def feed(ws):
        await metadata.wait()
        # Let the configured first greeting finish before presenting the user audio.
        await asyncio.sleep(6)
        stamp("input_start")
        chunk_size = 3200  # 100 ms, PCM signed 16-bit little endian, mono 16 kHz.
        offset = 0
        next_send = time.monotonic()
        while True:
            chunk = pcm[offset:offset + chunk_size]
            if chunk:
                offset += len(chunk)
            else:
                stamp("input_end")
                chunk = bytes(chunk_size)
            await ws.send(json.dumps({"user_audio_chunk": base64.b64encode(chunk).decode()}))
            if offset >= len(pcm) and "input_last_chunk_sent" not in timing:
                stamp("input_last_chunk_sent")
            next_send += len(chunk) / 32000
            await asyncio.sleep(max(0, next_send - time.monotonic()))

    async def answer_tool(ws, call: dict):
        stamp("tool_requested")
        if call.get("tool_name") != "daybreak_turn" or report.get("tool"):
            raise ProbeError("Unexpected or repeated client tool call; no second chat request sent")
        message = call.get("parameters", {}).get("message")
        if not isinstance(message, str) or not 1 <= len(message) <= 4000:
            raise ProbeError("Invalid client tool message")
        report["tool"] = {"name": "daybreak_turn", "message": message, "expects_response": call.get("expects_response")}
        result = check_http(await client.post("/api/conversation/chat", json={
            "message": message, "history": [], "scenario": "demo-vara",
        }), "Authenticated real chat")
        stamp("chat_returned")
        report["chat_result"] = result
        if result.get("proposal") is not None or result.get("provenance", {}).get("write_executed") is not False:
            raise ProbeError("Read-only probe received a proposal or invalid write provenance")
        if result.get("provider") != PROVIDER:
            raise ProbeError("The chat result did not identify the real Codex CLI provider")
        # Match the browser client tool's JSON result contract.
        await ws.send(json.dumps({
            "type": "client_tool_result", "tool_call_id": call["tool_call_id"],
            "result": json.dumps(result, ensure_ascii=False), "is_error": False,
        }))
        stamp("tool_result_sent")
        tool_done.set()

    try:
        # Includes the entire established session. Transport exceptions never expose their URL.
        async with asyncio.timeout(115):
            async with websockets.connect(url, open_timeout=15, close_timeout=3, max_size=4_000_000) as ws:
                stamp("websocket_connected")
                await ws.send(json.dumps({"type": "conversation_initiation_client_data"}))
                sender = asyncio.create_task(feed(ws))
                while True:
                    for task in tool_tasks:
                        if task.done() and task.exception():
                            raise task.exception()
                    if sender.done():
                        sender.result()
                    if (tool_done.is_set() and report.get("agent_responses") and audio["response"]
                            and response_audio_at is not None and time.monotonic() - response_audio_at >= 3):
                        report["session_stop"] = "Response audio quiet for three seconds after tool result"
                        break
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=0.5)
                    except TimeoutError:
                        continue
                    event = json.loads(raw)
                    kind = event.get("type", "unknown")
                    counts[kind] += 1
                    if kind == "ping":
                        await ws.send(json.dumps({"type": "pong", "event_id": event["ping_event"]["event_id"]}))
                    elif kind == "conversation_initiation_metadata":
                        meta = event["conversation_initiation_metadata_event"]
                        report["audio_formats"] = {
                            key: meta[key] for key in ("agent_output_audio_format", "user_input_audio_format")
                        }
                        audio_rate(meta["agent_output_audio_format"])
                        if meta["user_input_audio_format"] != "pcm_16000":
                            raise ProbeError("Agent did not negotiate PCM 16 kHz input")
                        stamp("metadata")
                        metadata.set()
                    elif kind == "user_transcript":
                        stamp("user_transcript")
                        report.setdefault("user_transcripts", []).append(event["user_transcription_event"]["user_transcript"])
                    elif kind == "client_tool_call":
                        tool_tasks.append(asyncio.create_task(answer_tool(ws, event["client_tool_call"])))
                    elif kind == "agent_response":
                        text = event["agent_response_event"]["agent_response"]
                        if tool_done.is_set():
                            stamp("agent_response")
                            report.setdefault("agent_responses", []).append(text)
                        else:
                            report.setdefault("greeting_responses", []).append(text)
                    elif kind == "audio":
                        chunk = base64.b64decode(event["audio_event"]["audio_base_64"], validate=True)
                        group = "response" if tool_done.is_set() else "greeting"
                        audio[group].append(chunk)
                        if group == "response":
                            stamp("first_response_audio")
                            response_audio_at = time.monotonic()
                            timing["last_response_audio"] = round(response_audio_at - started, 3)
                    elif kind in {"client_error", "error", "guardrail_triggered"}:
                        raise ProbeError(f"Provider emitted {kind}; raw payload deliberately not recorded")
    finally:
        for task in [sender, *tool_tasks]:
            if task:
                task.cancel()
        await asyncio.gather(*(task for task in [sender, *tool_tasks] if task), return_exceptions=True)
        timing["session_elapsed"] = round(time.monotonic() - started, 3)
        output_format = report.get("audio_formats", {}).get("agent_output_audio_format")
        if output_format:
            for group, chunks in audio.items():
                if chunks:
                    path = output / f"agent-{group}.wav"
                    save_wav(path, chunks, audio_rate(output_format))
                    report.setdefault("media", {})[path.name] = media_info(path)
        for name, left, right in (
            ("chat_duration", "tool_requested", "chat_returned"),
            ("input_end_to_transcript", "input_end", "user_transcript"),
            ("input_end_to_first_response_audio", "input_end", "first_response_audio"),
            ("tool_result_to_first_response_audio", "tool_result_sent", "first_response_audio"),
        ):
            if left in timing and right in timing:
                timing[name] = round(timing[right] - timing[left], 3)


async def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Never overwrite evidence, and never auto-retry a paid conversation.
    existing = list(OUT.glob("session-*/report.json"))
    if len(existing) >= 2:
        raise ProbeError("Two-session budget already used; no additional session started")
    output = OUT / datetime.now(ZoneInfo("Europe/Bucharest")).strftime("session-%Y%m%d-%H%M%S-%f")
    output.mkdir(mode=0o700)
    report = {
        "synthetic": True, "role": "customer", "environment": "local authenticated app + real ElevenLabs",
        "created_at": datetime.now(ZoneInfo("Europe/Bucharest")).isoformat(),
        "input_text": UTTERANCE, "hardware_microphone_tested": False, "hardware_speaker_tested": False,
        "listened": False, "operational_confirm_requests": 0, "status": "incomplete",
    }
    try:
        env = read_private_env()
        async with httpx.AsyncClient(base_url=BASE, headers={"origin": BASE}, timeout=70, follow_redirects=False) as client:
            check_http(await client.post("/api/cont/intrare", json={
                "email": env["DAYBREAK_DEMO_CUSTOMER_EMAIL"], "password": env["DAYBREAK_DEMO_CUSTOMER_PASSWORD"],
            }), "Private customer login")
            before = check_http(await client.get("/api/operations/context", params={"scenario": "demo-vara"}), "Before context")
            if before.get("actor", {}).get("role") != "customer":
                raise ProbeError("Authenticated account is not a customer")
            report["context_before_sha256"] = context_digest(before)
            report["context_counts"] = {key: len(before.get(key, [])) for key in ("cases", "connections", "work_items")}
            report["case_status_snapshot"] = [{
                key: case.get(key) for key in ("case_id", "status", "symptom", "next_step", "human_requested", "verdict")
            } for case in before.get("cases", [])]
            provider = ElevenLabs()
            mp3 = output / "synthetic-user-input.mp3"
            mp3.write_bytes(await provider.synthesize(UTTERANCE))
            pcm_path = output / "synthetic-user-input.pcm"
            await asyncio.to_thread(
                subprocess.run,
                ["ffmpeg", "-nostdin", "-v", "error", "-i", str(mp3), "-ac", "1", "-ar", "16000",
                 "-c:a", "pcm_s16le", "-f", "s16le", str(pcm_path)], capture_output=True, check=True,
            )
            pcm = pcm_path.read_bytes()
            save_wav(output / "synthetic-user-input.wav", [pcm], 16000)
            report["media"] = {path.name: media_info(path) for path in (mp3, output / "synthetic-user-input.wav")}
            report["input_pcm_bytes"] = len(pcm)
            await run_session(client, provider, pcm, report, output)
            after = check_http(await client.get("/api/operations/context", params={"scenario": "demo-vara"}), "After context")
            report["context_after_sha256"] = context_digest(after)
            report["operational_context_unchanged"] = context_digest(before) == context_digest(after)
            reply = report.get("chat_result", {}).get("reply", "")
            spoken = " ".join(report.get("agent_responses", []))
            report["tool_reply_equals_agent_response_exact"] = bool(reply) and reply == spoken
            report["tool_reply_equals_agent_response_whitespace_normalized"] = bool(reply) and normalized(reply) == normalized(spoken)
            report["functional_voice_path_completed"] = bool(
                report.get("user_transcripts") and report.get("tool") and report.get("chat_result")
                and (output / "agent-response.wav").exists()
            )
            report["status"] = "passed" if (report["functional_voice_path_completed"]
                and report["tool_reply_equals_agent_response_exact"] and report["operational_context_unchanged"]
            ) else "failed"
            if not report["tool_reply_equals_agent_response_exact"]:
                report["failure"] = "Agent response did not exactly match the real client tool reply; inspect both texts"
    except ProbeError as exc:
        report["status"] = "failed"
        report["failure"] = str(exc)
    except Exception as exc:  # noqa: BLE001 -- never expose credentials in transport exception strings.
        # Exception messages can contain signed URLs or auth headers. Save only the class.
        report["status"] = "failed"
        report["failure"] = f"{type(exc).__name__}; raw exception deliberately suppressed"
    finally:
        (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"status": report["status"], "report": str(output / "report.json"), "failure": report.get("failure")}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
