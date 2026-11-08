"""Preflight uses fake HTTP/config only; never invokes a demo action or provider test."""
import asyncio
import importlib.util
import json
import sys
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("voice_readiness", SCRIPTS / "daybreak_voice_readiness.py")
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


@pytest.fixture
def fake(monkeypatch):
    from cyberpunks.operations.models import Actor
    actors = {
        "customer": Actor(user_id="private-customer", organization_id="daybreak-demo", role="customer", connection_ids=["private-connection"]),
        "technician": Actor(user_id="private-technician", organization_id="daybreak-demo", role="technician", crew_id="private-crew"),
        "dispatcher": Actor(user_id="private-dispatcher", organization_id="daybreak-demo", role="dispatcher", permissions=["view_console"]),
    }
    config = {
        "agent_id": "private-agent", "phone_number_id": "private-destination", "allowed_callers": ["private-caller"],
        "public_origin": "https://private.example", "secret_id": "private-secret",
        "demo_callers": {"private-caller": {
            "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
            "actors": {k: a.model_dump() for k, a in actors.items()},
            "customer_connection_id": "private-connection", "allow_voice_reports": True,
        }},
    }
    contexts = {}
    for role, actor in actors.items():
        contexts[role] = {
            "actor": actor.model_dump(), "scenario": "demo-vara", "synthetic": True,
            "connections": [{"connection_id": "private-connection", "synthetic": True}],
            "plan": {"approved": True, "routes": [{"crew_id": "private-crew", "stops": [{"work_item_id": "private-work"}]}]},
            "work_items": [{"work_item_id": "private-work", "decision": {"decision": "human_review"}}],
        }
    state = {"config": config, "contexts": contexts, "local": 200, "public": 200, "auth": 401, "calls": []}
    def handler(request):
        state["calls"].append((request.method, request.url.path))
        if request.url.path == "/healthz":
            return httpx.Response(state["local"] if request.url.host == "127.0.0.1" else state["public"], json={"service": "daybreak-whatsapp-call-tool"})
        if request.url.path == "/api/voice/turn":
            assert request.method == "POST" and json.loads(request.content) == {}
            assert "authorization" not in request.headers
            return httpx.Response(state["auth"])
        assert request.method == "GET"
        if request.url.path.startswith("/v1/convai/agents/"):
            return httpx.Response(200, json=state["agent"])
        assert request.url.path == "/api/operations/context"
        role = json.loads(request.headers["X-Daybreak-Actor"])["role"]
        return httpx.Response(200, json=contexts[role])
    state["transport"] = httpx.MockTransport(handler)
    monkeypatch.setattr(r, "load_config", lambda: config)
    monkeypatch.setattr(r.Bindings, "resolve", lambda *a, **kw: actors["technician"])
    monkeypatch.setattr(r, "require_sending", dict)
    monkeypatch.setattr(r, "require_destination", lambda d: None)
    monkeypatch.setattr(r, "receipt_status", lambda *a, **kw: state.get("receipt", "ready"))
    monkeypatch.setattr(r, "job_counts", lambda p: {"pending": 0, "running": 0, "needs_reconciliation": 0})
    monkeypatch.setenv("DAYBREAK_INTERNAL_TOKEN", "private-token")
    monkeypatch.setenv("DAYBREAK_OPERATIONS_DB", "/unused/operations.sqlite3")
    return state


def run(fake, **kwargs):
    return asyncio.run(r.preflight(transport=fake["transport"], **kwargs))


def test_ready_reads_complete_queue_without_leaks_or_provider(fake):
    fake["contexts"]["dispatcher"]["work_items"] *= 37
    result = run(fake)
    assert result["readiness"] == "ready"
    assert result["checks"]["review_queue_count"] == 37
    assert result["checks"]["approved_route_remaining_count"] == 1
    assert "private-" not in json.dumps(result) and "private.example" not in json.dumps(result)
    assert not any(path.startswith("/v1/") for _, path in fake["calls"])


@pytest.mark.parametrize("check", ["local", "public", "auth"])
def test_health_or_missing_auth_blocks(fake, check):
    fake[check] = 200 if check == "auth" else 503
    assert run(fake)["errors"]


def test_expired_demo_blocks(fake):
    fake["config"]["demo_callers"]["private-caller"]["expires_at"] = (datetime.now(UTC)-timedelta(seconds=1)).isoformat()
    assert "demo_expired_or_invalid" in run(fake)["errors"]


def test_membership_mismatch_blocks(fake):
    fake["contexts"]["dispatcher"]["actor"]["permissions"] = []
    assert "roles_binding_or_operations_unavailable" in run(fake)["errors"]


def test_unapproved_route_blocks(fake):
    fake["contexts"]["technician"]["plan"]["approved"] = False
    assert "no_approved_remaining_route" in run(fake)["errors"]


def test_pdf_expiry_does_not_fail_voice(fake):
    fake["receipt"] = "pdf_window_unavailable"
    result = run(fake)
    assert result["readiness"] == "voice_only" and result["voice_ready"] and not result["pdf_ready"]


@pytest.mark.parametrize("age, expected", [(23*3600-1, "ready"), (23*3600, "pdf_window_unavailable"), (-61, "pdf_window_unavailable")])
def test_window_uses_real_message_timestamp(monkeypatch, age, expected):
    actor = r.Actor(user_id="fake", organization_id="daybreak-demo", role="technician")
    monkeypatch.setattr(r, "read_rows", lambda *a: [(json.dumps({"id": "real", "timestamp": 100000-age}), r.actor_key(actor))])
    assert r.receipt_status("unused", "caller", "destination", actor, now=100000) == expected


def test_changed_receipt_binding(monkeypatch):
    actor = r.Actor(user_id="fake", organization_id="daybreak-demo", role="technician")
    monkeypatch.setattr(r, "read_rows", lambda *a: [('{}', 'changed')])
    assert r.receipt_status("unused", "caller", "destination", actor) == "receipt_binding_changed"


def test_aggregate_counts_hide_job_payloads(monkeypatch):
    monkeypatch.setattr(r, "read_rows", lambda *a: [("queued", 3), ("running", 2), ("needs_reconciliation", 1), ("done", 70)])
    assert r.job_counts("unused") == {"pending": 3, "running": 2, "needs_reconciliation": 1}


def test_provider_optin_get_only_detects_turn_drift(fake, monkeypatch):
    monkeypatch.setattr(r, "desired_agent", lambda c: deepcopy(fake["expected"]))
    monkeypatch.setattr(r, "check_agent", lambda a, c: None)
    monkeypatch.setattr(r, "get_key", lambda: "private-key")
    fake["expected"] = {"conversation_config": {"turn": {"turn_eagerness": "eager"}, "agent": {"prompt": {"prompt": "private-prompt", "tools": [{"type": "webhook", "api_schema": {"method": "POST"}}]}}}}
    fake["agent"] = deepcopy(fake["expected"])
    assert run(fake, provider=True)["checks"]["provider_config"]
    fake["agent"]["conversation_config"]["turn"]["turn_eagerness"] = "patient"
    assert "provider_config_unavailable_or_mismatch" in run(fake, provider=True)["errors"]
    assert all(method == "GET" for method, path in fake["calls"] if path.startswith("/v1/"))


def test_exception_output_does_not_echo_private_values(fake, monkeypatch):
    monkeypatch.setattr(r, "load_config", lambda: (_ for _ in ()).throw(ValueError("private-token private-phone")))
    result = run(fake)
    assert result["errors"] == ["private_config_unavailable"]
    assert "private-token" not in json.dumps(result)


def test_provider_defaults_do_not_hide_requested_value_changes():
    assert r.matches({"timeout": -1, "provider_default": None}, {"timeout": -1})
    assert not r.matches({"timeout": 10, "provider_default": None}, {"timeout": -1})


def test_deadline_blocks_without_private_exception(fake, monkeypatch):
    async def slow_response(request):
        await asyncio.sleep(1)
        return httpx.Response(200, json={})
    fake["transport"] = httpx.MockTransport(slow_response)
    monkeypatch.setattr(r, "DEADLINE", 0)
    assert "preflight_deadline" in run(fake)["errors"]


def test_cli_nonzero_for_blocker(fake, monkeypatch, capsys):
    fake["local"] = 503
    monkeypatch.setattr(sys, "argv", ["readiness"])
    monkeypatch.setattr(r, "environment", dict)
    original = r.preflight
    monkeypatch.setattr(r, "preflight", lambda **kw: original(transport=fake["transport"], **kw))
    assert r.main() == 2
    assert json.loads(capsys.readouterr().out)["readiness"] == "blocked"
