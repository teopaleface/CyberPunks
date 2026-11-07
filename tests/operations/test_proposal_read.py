"""Propunerile din linkuri se citesc prin API fără confirmare implicită."""

import json
from datetime import UTC, datetime, timedelta

import pytest

from cyberpunks.operations.service import OperationsService, get_service

from .conftest import confirm, propose


def read(env, p, actor=None):
    return env["client"].get(
        "/api/operations/proposals/" + p["proposal_id"], headers=env["headers"](actor or env["customer"])
    )


def pending_report(env):
    return propose(
        env,
        "create_case",
        {
            "connection_id": env["binding"]["connection_id"],
            "symptom_type": "meter",
            "symptom": "Meter readings look wrong",
        },
    )


def registry(s):
    with s.db.connect() as db:
        return {
            table: [tuple(row) for row in db.execute("SELECT * FROM " + table + " ORDER BY rowid")]
            for table in ("connections", "cases", "proposals", "commands", "events", "command_recoveries")
        }


def test_owner_reads_the_original_public_proposal_without_any_execution(env, monkeypatch):
    p = pending_report(env)
    s = env["service"]
    # Retrieval remains possible after an API restart, without conversational memory.
    restarted = OperationsService(s.outputs, s.db_path)
    env["client"].app.dependency_overrides[get_service] = lambda: restarted
    before, version = registry(s), s.planner.version("demo-vara")

    def no_action(*args, **kwargs):
        raise AssertionError("Reading a proposal must not prepare, execute, cancel or reconcile anything")

    for method in ("prepare", "confirm", "recover", "command"):
        monkeypatch.setattr(restarted, method, no_action)
    for _ in range(2):
        response = read(env, p)
        assert response.status_code == 200, response.text
        assert response.json() == p
        assert "actor_signature" not in response.json() and "confirmed_by" not in response.json()
    assert registry(s) == before and s.planner.version("demo-vara") == version
    assert not list(s.planner.state.glob("effects/*/effect.json"))


@pytest.mark.parametrize("viewer", ["foreign_sender", "dispatcher", "foreign_organization", "role_promotion"])
def test_no_other_sender_or_promoted_identity_can_open_a_proposal(env, viewer):
    p = pending_report(env)
    actor = env["customer"]
    expected = 404
    if viewer == "foreign_sender":
        actor = actor.model_copy(update={"user_id": "foreign-sender"})
    elif viewer == "dispatcher":
        actor = env["dispatcher"]  # recover_commands permits command recovery, never proposal adoption.
    elif viewer == "foreign_organization":
        actor = actor.model_copy(update={"organization_id": "foreign-organization"})
    else:
        actor = actor.model_copy(update={"role": "dispatcher", "permissions": ["create_case", "recover_commands"]})
        expected = 403
    before = registry(env["service"])
    response = read(env, p, actor)
    assert response.status_code == expected
    assert "symptom" not in response.json().get("detail", {})
    assert registry(env["service"]) == before


@pytest.mark.parametrize(
    "change", [{"connection_ids": []}, {"permissions": ["new-permission"]}, {"crew_id": "different-crew"}]
)
def test_current_membership_must_still_match_the_proposal(env, change):
    p = pending_report(env)
    response = read(env, p, env["customer"].model_copy(update=change))
    assert response.status_code == 403 and response.json()["detail"]["code"] == "membership_changed"
    assert not env["service"].context(env["dispatcher"])["events"]


def test_expired_proposal_is_a_read_conflict_without_mutation(env):
    p = pending_report(env)
    s = env["service"]
    with s.db.transaction() as db:
        row = db.execute("SELECT body FROM proposals WHERE proposal_id=?", (p["proposal_id"],)).fetchone()
        original = json.loads(row["body"])
        original["expires_at"] = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()
        db.execute("UPDATE proposals SET body=? WHERE proposal_id=?", (json.dumps(original), p["proposal_id"]))
    before = registry(s)
    response = read(env, p)
    assert response.status_code == 409 and response.json()["detail"]["code"] == "proposal_expired"
    assert registry(s) == before


@pytest.mark.parametrize("state", ["succeeded", "reconciling", "cancelled"])
def test_previously_confirmed_proposals_are_not_reopened_or_recovered_by_get(env, state, monkeypatch):
    p = pending_report(env)
    s = env["service"]
    if state != "succeeded":
        original_apply = s._apply

        def unavailable(*args, **kwargs):
            raise OSError("synthetic interruption before the database effect")

        monkeypatch.setattr(s, "_apply", unavailable)
    cmd = confirm(env, p)
    if state != "succeeded":
        monkeypatch.setattr(s, "_apply", original_apply)
        assert cmd["status"] == "reconciling"
    if state == "cancelled":
        r = env["client"].post(
            "/api/operations/commands/" + cmd["command_id"] + "/recover",
            headers=env["headers"](env["dispatcher"]),
            json={"decision": "cancel", "reason": "Cancel unpublished operation"},
        )
        assert r.status_code == 200 and r.json()["status"] == "cancelled"
    before = registry(s)
    response = read(env, p)
    assert response.status_code == 409 and response.json()["detail"]["code"] == "proposal_consumed"
    assert registry(s) == before


def test_current_object_scope_is_rechecked_even_when_membership_has_not_changed(env):
    s, actor = env["service"], env["technician"]
    p = propose(env, "record_verdict", {"work_item_id": env["binding"]["work_item_id"], "outcome": "no_access"}, actor)
    # A real replan can remove the job without changing the technician's membership.
    plan_path = env["root"] / "plans/demo-vara/plan.json"
    plan = json.loads(plan_path.read_text())
    for route in plan["routes"]:
        route["stops"] = [stop for stop in route["stops"] if stop["work_item_id"] != env["binding"]["work_item_id"]]
    plan_path.write_text(json.dumps(plan))
    before = registry(s)
    response = read(env, p, actor)
    assert response.status_code == 409 and response.json()["detail"]["code"] == "stale_plan"
    assert registry(s) == before


def test_proposal_reads_require_the_same_trusted_service_authentication(env):
    p = pending_report(env)
    r = env["client"].get("/api/operations/proposals/" + p["proposal_id"])
    assert r.status_code == 401


def context_proposals(env, actor=None):
    response = env["client"].get("/api/operations/context", headers=env["headers"](actor or env["customer"]))
    assert response.status_code == 200, response.text
    return response.json()["pending_proposals"]


def test_context_discovers_own_pending_proposal_after_restart_without_effects(env, monkeypatch):
    p = pending_report(env)
    s = env["service"]
    restarted = OperationsService(s.outputs, s.db_path)
    env["client"].app.dependency_overrides[get_service] = lambda: restarted
    before, version = registry(s), s.planner.version("demo-vara")

    def no_action(*args, **kwargs):
        raise AssertionError("Context discovery must not execute or change a proposal")

    for method in ("prepare", "confirm", "recover", "command"):
        monkeypatch.setattr(restarted, method, no_action)
    expected = {
        key: p[key]
        for key in ("proposal_id", "action", "summary", "scenario", "created_at", "expires_at", "requires_confirmation")
    }
    for _ in range(2):
        assert context_proposals(env) == [expected]
    assert read(env, p).json() == p
    assert registry(s) == before and s.planner.version("demo-vara") == version


def test_context_pending_proposals_belong_only_to_current_unchanged_emitter(env):
    own = pending_report(env)
    foreign = env["customer"].model_copy(update={"user_id": "another-sender"})
    theirs = propose(
        env,
        "create_case",
        {"connection_id": env["binding"]["connection_id"], "symptom": "A separate report", "symptom_type": "meter"},
        foreign,
    )
    dispatch = propose(env, "request_human", {"reason": "Dispatcher own review"}, env["dispatcher"])
    assert [p["proposal_id"] for p in context_proposals(env)] == [own["proposal_id"]]
    assert [p["proposal_id"] for p in context_proposals(env, foreign)] == [theirs["proposal_id"]]
    assert [p["proposal_id"] for p in context_proposals(env, env["dispatcher"])] == [dispatch["proposal_id"]]
    revoked = env["customer"].model_copy(update={"connection_ids": []})
    promoted = env["customer"].model_copy(update={"role": "dispatcher", "permissions": ["recover_commands"]})
    assert context_proposals(env, revoked) == []
    assert context_proposals(env, promoted) == []
    forbidden = env["customer"].model_copy(update={"organization_id": "another-org"})
    response = env["client"].get("/api/operations/context", headers=env["headers"](forbidden))
    assert response.status_code == 404 and own["proposal_id"] not in response.text


def test_context_excludes_expired_and_consumed_proposals(env):
    expired = pending_report(env)
    consumed = propose(
        env, "request_human", {"connection_id": env["binding"]["connection_id"], "reason": "Already confirmed"}
    )
    confirm(env, consumed)
    valid = propose(
        env, "request_human", {"connection_id": env["binding"]["connection_id"], "reason": "Still unconfirmed"}
    )
    s = env["service"]
    with s.db.transaction() as db:
        row = db.execute("SELECT body FROM proposals WHERE proposal_id=?", (expired["proposal_id"],)).fetchone()
        p = json.loads(row["body"])
        p["expires_at"] = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()
        db.execute("UPDATE proposals SET body=? WHERE proposal_id=?", (json.dumps(p), expired["proposal_id"]))
    before = registry(s)
    assert [p["proposal_id"] for p in context_proposals(env)] == [valid["proposal_id"]]
    assert registry(s) == before


def test_context_excludes_proposal_when_case_version_changes(env):
    from .conftest import create_case

    case = create_case(env)
    stale = propose(
        env,
        "set_availability",
        {"case_id": case["case_id"], "start": "2026-11-08T10:00:00+02:00", "end": "2026-11-08T11:00:00+02:00"},
    )
    changed = propose(env, "request_human", {"case_id": case["case_id"], "reason": "A confirmed case update"})
    confirm(env, changed)
    valid = pending_report(env)
    assert read(env, stale).status_code == 409
    assert [p["proposal_id"] for p in context_proposals(env)] == [valid["proposal_id"]]


def test_context_excludes_proposals_on_an_old_plan(env):
    p = pending_report(env)
    plan_path = env["root"] / "plans/demo-vara/plan.json"
    plan = json.loads(plan_path.read_text())
    plan["plan_id"] += "-synthetic-revision"
    plan_path.write_text(json.dumps(plan))
    before = registry(env["service"])
    assert context_proposals(env) == []
    assert registry(env["service"]) == before
    assert read(env, p).status_code == 409


def test_context_returns_at_most_ten_recent_valid_proposals(env):
    proposals = [
        propose(
            env,
            "request_human",
            {"connection_id": env["binding"]["connection_id"], "reason": f"Synthetic unconfirmed review {i}"},
        )
        for i in range(12)
    ]
    before = registry(env["service"])
    visible = context_proposals(env)
    assert len(visible) == 10
    assert [p["proposal_id"] for p in visible] == [p["proposal_id"] for p in reversed(proposals[-10:])]
    assert all(p["requires_confirmation"] is True for p in visible)
    assert registry(env["service"]) == before
