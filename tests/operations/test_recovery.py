"""Recuperare prin API, sub autoritatea actuală, după revocarea emitentului."""

import json

import pytest

from cyberpunks.operations.service import OperationsService, get_service

from .conftest import confirm, create_case, propose


def get(env, path, actor):
    return env["client"].get("/api/operations/" + path, headers=env["headers"](actor))


def post(env, path, actor, body=None):
    return env["client"].post("/api/operations/" + path, headers=env["headers"](actor), json=body)


@pytest.mark.parametrize("interruption", ["complete_effect", "partial_effect"])
@pytest.mark.parametrize("legacy", [False, True])
def test_dispatcher_recovers_published_effect_after_issuer_membership_revoked(env, monkeypatch, interruption, legacy):
    import cyberpunks.operations.planner as adapter
    from cyberpunks.planner import feedback

    s, tech, dispatcher = env["service"], env["technician"], env["dispatcher"]
    case = create_case(env)
    p = propose(env, "record_verdict", {"work_item_id": env["binding"]["work_item_id"], "outcome": "no_access"}, tech)
    with s.db.connect() as db:
        immutable = db.execute("SELECT body FROM proposals WHERE proposal_id=?", (p["proposal_id"],)).fetchone()["body"]
    if interruption == "complete_effect":
        original_save = s._save_case

        def fail_db(db, case):
            raise OSError("synthetic ledger interruption after file publication")

        monkeypatch.setattr(s, "_save_case", fail_db)
    else:
        original_replace = adapter.os.replace
        count = 0

        def fail_second_file(src, dest):
            nonlocal count
            if str(src).endswith(".daybreak-tmp"):
                count += 1
                if count == 2:
                    raise OSError("synthetic interruption after first file publication")
            return original_replace(src, dest)

        monkeypatch.setattr(adapter.os, "replace", fail_second_file)
    cmd = confirm(env, p, tech)
    assert cmd["status"] == "reconciling" and cmd["result"] is None
    if interruption == "complete_effect":
        monkeypatch.setattr(s, "_save_case", original_save)
    else:
        monkeypatch.setattr(adapter.os, "replace", original_replace)
    if legacy:
        # Commands confirmed before this recovery fix did not save an actor-role snapshot.
        with s.db.transaction() as db:
            body = json.loads(
                db.execute("SELECT body FROM commands WHERE command_id=?", (cmd["command_id"],)).fetchone()["body"]
            )
            body.pop("confirmed_by", None)
            db.execute("UPDATE commands SET body=? WHERE command_id=?", (json.dumps(body), cmd["command_id"]))
    # Refresh/restart loses all in-memory command IDs but preserves discovery through the API.
    restarted = OperationsService(s.outputs, s.db_path)
    env["client"].app.dependency_overrides[get_service] = lambda: restarted
    revoked = tech.model_copy(update={"crew_id": "REVOKED-CREW", "permissions": []})
    assert get(env, "commands/" + cmd["command_id"], revoked).status_code == 403
    assert post(env, "proposals/" + p["proposal_id"] + "/confirm", revoked).status_code == 403
    revoked_context = get(env, "context", revoked).json()
    assert revoked_context["work_items"] == [] and revoked_context["cases"] == []
    assert revoked_context["pending_commands"][0]["can_recover"] is False
    assert revoked_context["pending_commands"][0]["recovery_action"] == "requires_dispatcher"
    for _ in range(2):
        pending = get(env, "context", dispatcher).json()["pending_commands"]
        assert pending == [
            {
                **pending[0],
                "command_id": cmd["command_id"],
                "proposal_id": p["proposal_id"],
                "action": "record_verdict",
                "status": "reconciling",
                "can_recover": True,
                "recovery_action": "retrieve",
            }
        ]
    unauthorized_dispatcher = dispatcher.model_copy(update={"user_id": "restricted", "permissions": ["approve_plan"]})
    assert get(env, "commands/" + cmd["command_id"], unauthorized_dispatcher).status_code == 404
    assert get(env, "context", unauthorized_dispatcher).json()["pending_commands"] == []
    foreign_org = dispatcher.model_copy(update={"organization_id": "foreign-organization"})
    assert get(env, "commands/" + cmd["command_id"], foreign_org).status_code == 404
    other_tech = tech.model_copy(update={"user_id": "different-technician"})
    assert get(env, "commands/" + cmd["command_id"], other_tech).status_code == 404
    assert get(env, "context", other_tech).json()["pending_commands"] == []
    # An already-published command cannot be disguised as a safe cancellation.
    assert (
        post(
            env,
            "commands/" + cmd["command_id"] + "/recover",
            dispatcher,
            {"decision": "cancel", "reason": "Cannot cancel a published effect"},
        ).status_code
        == 409
    )

    def never_reexecute(*args, **kwargs):
        raise AssertionError("A revoked issuer must not trigger another planner operation")

    monkeypatch.setattr(feedback, "record_verdict", never_reexecute)
    r = get(env, "commands/" + cmd["command_id"], dispatcher)
    assert r.status_code == 200
    recovered = r.json()
    assert recovered["status"] == "succeeded", recovered
    assert recovered["recovery"]["confirmed_by"] == {"user_id": tech.user_id, "role": None if legacy else "technician"}
    assert recovered["recovery"]["reconciled_by"]["user_id"] == dispatcher.user_id
    assert recovered["recovery"]["reconciled_by"]["permission"] == "recover_commands"
    assert get(env, "commands/" + cmd["command_id"], dispatcher).json() == recovered
    assert get(env, "commands/" + cmd["command_id"], revoked).status_code == 403
    context = get(env, "context", dispatcher).json()
    assert not context["reconciliation_pending"] and context["pending_commands"] == []
    assert context["cases"][0]["status"] == "access_blocked" and context["cases"][0]["version"] == 2
    assert context["cases"][0]["requester_id"] == env["customer"].user_id
    event = next(e for e in context["events"] if e["command_id"] == cmd["command_id"])
    assert event["actor_id"] == tech.user_id and event["role"] == (None if legacy else "technician")
    assert event["reconciled_by"]["user_id"] == dispatcher.user_id
    labels = [json.loads(x) for x in (env["root"] / "plans/demo-vara/labels.jsonl").read_text().splitlines()]
    assert len(labels) == 1 and labels[0]["label"] is None and labels[0]["reviewer"] == tech.user_id
    with s.db.connect() as db:
        assert (
            db.execute("SELECT body FROM proposals WHERE proposal_id=?", (p["proposal_id"],)).fetchone()["body"]
            == immutable
        )
        audits = [json.loads(r["body"]) for r in db.execute("SELECT body FROM command_recoveries")]
    assert len(audits) == 1 and audits[0]["status"] == "completed"
    # Independent authenticated work is unblocked, without restoring the old technician's membership.
    next_p = propose(env, "request_human", {"case_id": case["case_id"], "reason": "Arrange access with the customer"})
    assert confirm(env, next_p)["status"] == "succeeded"


@pytest.mark.parametrize("interruption", ["before_manifest", "prepared_unpublished", "database_only"])
def test_unpublished_revoked_command_requires_explicit_authorized_cancellation(env, monkeypatch, interruption):
    import cyberpunks.operations.planner as adapter

    s, tech, dispatcher = env["service"], env["technician"], env["dispatcher"]
    original = tech
    if interruption == "database_only":
        original = env["customer"]
        p = propose(env, "create_case", {"connection_id": env["binding"]["connection_id"], "symptom": "Unsent report"})
        original_apply = s._apply

        def fail_apply(*args, **kwargs):
            raise OSError("synthetic database-only operation interruption")

        monkeypatch.setattr(s, "_apply", fail_apply)
    else:
        p = propose(
            env, "record_verdict", {"work_item_id": env["binding"]["work_item_id"], "outcome": "confirmed"}, tech
        )
        original_replace = adapter.os.replace

        def fail_before_publication(src, dest):
            if str(dest).endswith("effect.json") and interruption == "before_manifest":
                raise OSError("synthetic manifest preparation interruption")
            if str(src).endswith(".daybreak-tmp") and interruption == "prepared_unpublished":
                raise OSError("synthetic interruption before any file publication")
            return original_replace(src, dest)

        monkeypatch.setattr(adapter.os, "replace", fail_before_publication)
    cmd = confirm(env, p, original)
    assert cmd["status"] == "reconciling"
    if interruption == "database_only":
        monkeypatch.setattr(s, "_apply", original_apply)
    else:
        monkeypatch.setattr(adapter.os, "replace", original_replace)
    revoked = original.model_copy(update={"connection_ids": [], "crew_id": "REVOKED"})
    assert get(env, "commands/" + cmd["command_id"], revoked).status_code == 403
    before = s.planner.version("demo-vara")
    response = get(env, "commands/" + cmd["command_id"], dispatcher)
    assert response.status_code == 200
    pending = response.json()
    assert pending["status"] == "reconciling"
    assert pending["recovery"]["action"] == "cancel" and pending["recovery"]["requires_confirmation"]
    assert s.planner.version("demo-vara") == before
    assert not (env["root"] / "plans/demo-vara/labels.jsonl").exists()
    assert not get(env, "context", env["customer"]).json()["cases"]
    # The current issuer has no cancellation authority; neither does a dispatcher without the explicit grant.
    assert (
        post(
            env,
            "commands/" + cmd["command_id"] + "/recover",
            original,
            {"decision": "cancel", "reason": "Reassign safely"},
        ).status_code
        == 403
    )
    assert (
        post(
            env,
            "commands/" + cmd["command_id"] + "/recover",
            dispatcher,
            {"decision": "execute", "reason": "Execute after revocation"},
        ).status_code
        == 422
    )
    cancelled = post(
        env,
        "commands/" + cmd["command_id"] + "/recover",
        dispatcher,
        {"decision": "cancel", "reason": "Issuer membership changed before publication"},
    )
    assert cancelled.status_code == 200
    saved = cancelled.json()
    assert saved["status"] == "cancelled" and saved["result"]["effect_published"] is False
    assert saved["recovery"]["confirmed_by"]["user_id"] == original.user_id
    assert get(env, "commands/" + cmd["command_id"], dispatcher).json() == saved
    assert (
        post(
            env,
            "commands/" + cmd["command_id"] + "/recover",
            dispatcher,
            {"decision": "cancel", "reason": "Retry cancellation"},
        ).json()
        == saved
    )
    assert not get(env, "context", dispatcher).json()["reconciliation_pending"]
    assert s.planner.version("demo-vara") == before
    assert (
        confirm(
            env,
            propose(
                env,
                "request_human",
                {"connection_id": env["binding"]["connection_id"], "reason": "Independent review request"},
            ),
        )["status"]
        == "succeeded"
    )


def test_an_unconfirmed_proposal_cannot_be_recovered_or_cancelled(env):
    p = propose(
        env, "request_human", {"connection_id": env["binding"]["connection_id"], "reason": "Unconfirmed request"}
    )
    assert get(env, "commands/" + p["proposal_id"], env["dispatcher"]).status_code == 404
    assert (
        post(
            env,
            "commands/" + p["proposal_id"] + "/recover",
            env["dispatcher"],
            {"decision": "cancel", "reason": "Cannot adopt unconfirmed work"},
        ).status_code
        == 404
    )
    assert get(env, "context", env["dispatcher"]).json()["pending_commands"] == []
