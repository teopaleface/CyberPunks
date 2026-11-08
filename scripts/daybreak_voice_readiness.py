"""Bounded, read-only presentation preflight. Never starts calls, jobs or sends.

Run: uv run python -B scripts/daybreak_voice_readiness.py [--provider]
Exit 2 means a blocking check failed; PDF-only limitations leave voice available.
The public helper's unauthenticated POST is only an expected-401 auth probe.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sqlite3
import time
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import httpx
from daybreak_runtime import environment
from daybreak_whatsapp_calls import check_agent, desired_agent

from cyberpunks.channels.elevenlabs import API, get_key, runtime_root
from cyberpunks.channels.voice_briefs import trusted_next_stop
from cyberpunks.channels.whatsapp import Bindings
from cyberpunks.channels.whatsapp_calls import _demo_profile, load_config, verify_public_tool
from cyberpunks.channels.whatsapp_config import require_destination, require_sending
from cyberpunks.channels.whatsapp_store import actor_key
from cyberpunks.operations.models import Actor

MAX_BYTES = 4_000_000
DEADLINE = 45


class Contexts:
    """Only cached responses from the running operations service, never a local service constructor."""

    def __init__(self):
        self.values = {}

    def context(self, actor, scenario):
        return self.values[actor.model_dump_json()]


async def get_json(client, url, **kwargs):
    async with client.stream("GET", url, **kwargs) as response:
        if response.status_code != 200:
            raise ValueError("unavailable")
        chunks, size = [], 0
        async for chunk in response.aiter_bytes():
            size += len(chunk)
            if size > MAX_BYTES:
                raise ValueError("response_limit")
            chunks.append(chunk)
        body = json.loads(b"".join(chunks))
        if not isinstance(body, dict):
            raise TypeError("invalid_response")
        return body


def read_rows(path, query, args=()):
    # mode=ro never creates a missing database; no store constructors/migrations.
    with closing(sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True, timeout=1)) as db:
        until = time.monotonic() + 1
        db.set_progress_handler(lambda: int(time.monotonic() > until), 1000)
        return db.execute(query, args).fetchall()


def receipt_status(path, caller, destination, actor, *, now=None):
    rows = read_rows(
        path,
        "SELECT message, actor_signature FROM inbound_queue WHERE sender=? AND destination=? "
        "ORDER BY created DESC,event_id DESC LIMIT 1",
        (caller, destination),
    )
    if not rows:
        return "real_receipt_missing"
    message, signature = rows[0]
    if signature != actor_key(actor):
        return "receipt_binding_changed"
    try:
        message = json.loads(message)
        if not isinstance(message.get("id"), str) or not message["id"]:
            return "real_receipt_invalid"
        age = (time.time() if now is None else now) - int(message["timestamp"])
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
        return "real_receipt_invalid"
    return "ready" if -60 <= age < 23 * 3600 else "pdf_window_unavailable"


def job_counts(path):
    counts = {"pending": 0, "running": 0, "needs_reconciliation": 0}
    for status, count in read_rows(path, "SELECT status,count(*) FROM voice_jobs GROUP BY status"):
        if status == "queued":
            counts["pending"] += count
        elif status in counts:
            counts[status] += count
    return counts


def matches(actual, expected):
    """Provider GET adds default fields; verify every explicitly intended value."""
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(k in actual and matches(actual[k], v) for k, v in expected.items())
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(
            matches(a, e) for a, e in zip(actual, expected, strict=True)
        )
    return actual == expected


async def preflight(*, provider=False, transport=None):
    report = {
        "readiness": "blocked", "voice_ready": False, "pdf_ready": False,
        "checks": {}, "errors": [],
        "limits": ["physical_audio_not_tested", "sending_not_tested", "snapshot_only"],
    }
    checks, errors, limits = report["checks"], report["errors"], report["limits"]
    if not provider:
        limits.append("provider_not_checked")
    try:
        async with asyncio.timeout(DEADLINE):
            await inspect(report, provider=provider, transport=transport)
    except TimeoutError:
        errors.append("preflight_deadline")
    except Exception:  # noqa: BLE001 - never expose private exception details
        # Never echo exception strings: they may include URLs, headers or identities.
        errors.append("preflight_unavailable")
    report["voice_ready"] = not errors
    report["pdf_ready"] = report["voice_ready"] and checks.get("pdf") == "ready"
    report["readiness"] = "blocked" if errors else ("ready" if report["pdf_ready"] else "voice_only")
    return report


async def inspect(report, *, provider, transport):
    checks, errors, limits = report["checks"], report["errors"], report["limits"]
    try:
        config = load_config()
    except Exception:  # noqa: BLE001 - never expose private exception details
        errors.append("private_config_unavailable")
        return
    async with httpx.AsyncClient(timeout=5, follow_redirects=False, transport=transport, trust_env=False) as client:
        try:
            health = await get_json(client, "http://127.0.0.1:8722/healthz")
            checks["local_health"] = health.get("service") == "daybreak-whatsapp-call-tool"
        except Exception:  # noqa: BLE001 - never expose private exception details
            checks["local_health"] = False
        if not checks["local_health"]:
            errors.append("local_health_unavailable")
        try:
            await verify_public_tool(config["public_origin"], transport=transport)
            checks["public_health_auth401"] = True
        except Exception:  # noqa: BLE001 - never expose private exception details
            checks["public_health_auth401"] = False
            errors.append("public_health_or_auth_unavailable")
        callers = config.get("allowed_callers", [])
        if len(callers) != 1 or not isinstance(callers[0], str):
            errors.append("current_caller_ambiguous")
            return
        caller = callers[0]
        entry = config.get("demo_callers", {}).get(caller, {})
        try:
            expiry = datetime.fromisoformat(entry["expires_at"])
            valid = expiry.utcoffset().total_seconds() == 0 and expiry > datetime.now(UTC)
        except (ValueError, KeyError, TypeError, AttributeError):
            valid = False
        checks["demo_unexpired"] = valid
        if not valid:
            errors.append("demo_expired_or_invalid")
            return
        contexts = Contexts()
        try:
            actors = {role: Actor.model_validate(value) for role, value in entry["actors"].items()}
            # Current operations GETs enforce current membership and scope.
            bound = Bindings(runtime_root() / "whatsapp-bindings.json").resolve(config["phone_number_id"], caller)
            token = os.environ["DAYBREAK_INTERNAL_TOKEN"]
            if not token:
                raise ValueError("missing_auth")
            for actor in [*actors.values(), bound]:
                key = actor.model_dump_json()
                if key not in contexts.values:
                    contexts.values[key] = await get_json(
                        client, "http://127.0.0.1:8720/api/operations/context", params={"scenario": "demo-vara"},
                        headers={"Authorization": "Bearer " + token, "X-Daybreak-Actor": key},
                    )
            profile = _demo_profile(config, caller, contexts)
            if not profile:
                raise ValueError("invalid_profile")
            bound_context = contexts.context(bound, "demo-vara")
            if bound_context.get("actor") != bound.model_dump() or bound_context.get("scenario") != "demo-vara":
                raise ValueError("invalid_binding_context")
            checks["roles_and_verified_binding"] = True
        except Exception:  # noqa: BLE001 - never expose private exception details
            checks["roles_and_verified_binding"] = False
            errors.append("roles_binding_or_operations_unavailable")
            return
        technician = actors["technician"]
        routes, remaining, _, _ = trusted_next_stop(contexts.context(technician, "demo-vara"), technician)
        checks["approved_route_count"] = len(routes)
        checks["approved_route_remaining_count"] = len(remaining)
        if not routes or not remaining:
            errors.append("no_approved_remaining_route")
        dispatcher = contexts.context(actors["dispatcher"], "demo-vara")
        checks["review_queue_count"] = sum(
            (item.get("decision") or {}).get("decision") == "human_review"
            for item in dispatcher["work_items"]
        )
        checks["work_item_count"] = len(dispatcher["work_items"])
        checks["demo_actions"] = {
            flag: entry.get(flag) is True
            for flag in ("allow_incident_actions", "allow_voice_reports", "allow_queue_actions")
        }
        try:
            db_path = Path(os.environ["DAYBREAK_OPERATIONS_DB"]).with_name("voice-jobs.sqlite3")
            checks["voice_jobs"] = job_counts(db_path)
            if checks["voice_jobs"]["needs_reconciliation"]:
                limits.append("voice_jobs_need_reconciliation_do_not_retry")
            if checks["voice_jobs"]["pending"] or checks["voice_jobs"]["running"]:
                limits.append("voice_jobs_in_progress")
        except Exception:  # noqa: BLE001 - never expose private exception details
            checks["voice_jobs"] = "unavailable"
            limits.append("voice_job_counts_unavailable")
        try:
            require_sending()
            require_destination(config["phone_number_id"])
            checks["meta_sending_gates"] = True
        except Exception:  # noqa: BLE001 - never expose private exception details
            checks["meta_sending_gates"] = False
        try:
            checks["messaging_receipt"] = receipt_status(
                runtime_root() / "channels-whatsapp.sqlite3", caller, config["phone_number_id"], bound,
            )
        except Exception:  # noqa: BLE001 - never expose private exception details
            checks["messaging_receipt"] = "receipt_unavailable"
        checks["pdf"] = "ready" if (
            checks["meta_sending_gates"] and checks["messaging_receipt"] == "ready"
            and entry.get("allow_voice_reports") is True
        ) else "unavailable"
        if checks["pdf"] != "ready":
            limits.append("pdf_unavailable_voice_can_continue")
        if provider:
            try:
                # Only this existing agent GET; no test/signed URL/token/PATCH endpoints.
                agent = await get_json(
                    client, API + f"/v1/convai/agents/{config['agent_id']}", headers={"xi-api-key": get_key()},
                )
                check_agent(agent, config)
                actual = agent["conversation_config"]
                expected = desired_agent(config)["conversation_config"]
                if not matches(actual["turn"], expected["turn"]):
                    raise ValueError("turn_mismatch")
                ap, ep = actual["agent"]["prompt"], expected["agent"]["prompt"]
                if not matches(ap, {k: v for k, v in ep.items() if k not in {"tools", "tool_ids"}}):
                    raise ValueError("prompt_mismatch")
                tool, wanted = ap["tools"][0], ep["tools"][0]
                if any(tool.get(k) != v for k, v in wanted.items() if k != "api_schema"):
                    raise ValueError("tool_mismatch")
                if not matches(tool["api_schema"], wanted["api_schema"]):
                    raise ValueError("schema_mismatch")
                checks["provider_config"] = True
            except Exception:  # noqa: BLE001 - never expose private exception details
                checks["provider_config"] = False
                errors.append("provider_config_unavailable_or_mismatch")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", action="store_true", help="Opt in to one official current-agent GET")
    args = parser.parse_args()
    try:
        os.environ.update(environment())
        result = asyncio.run(preflight(provider=args.provider))
    except Exception:  # noqa: BLE001 - never expose private exception details
        result = {"readiness": "blocked", "errors": ["private_environment_unavailable"], "limits": []}
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 2 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
