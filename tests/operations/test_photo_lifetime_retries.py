"""Expiry, scoped quotas and retries on complete temporary planner data."""

import json
from datetime import UTC, datetime, timedelta

import pytest

import cyberpunks.operations.service as operations
from cyberpunks.operations import photos
from cyberpunks.operations.models import OperationError

from .conftest import confirm, create_case, propose
from .test_photos_corrections import get_photo, upload, verdict, work


def clock(monkeypatch):
    time = [datetime.now(UTC)]
    monkeypatch.setattr(operations, "now", lambda: time[0])
    return time


def photo_rows(service):
    with service.db.connect() as db:
        return {row["photo_id"]: row["status"] for row in db.execute("SELECT photo_id,status FROM photos")}


def test_expired_abandoned_drafts_no_longer_use_quota_even_beyond_gc_batch(env, monkeypatch):
    time = clock(monkeypatch)
    initial = time[0]
    old = [upload(env).json() for _ in range(20)]
    time[0] = initial + timedelta(hours=24, seconds=-1)
    assert upload(env).status_code == 409
    monkeypatch.setattr(photos, "GC_BATCH_SIZE", 1)
    time[0] = initial + timedelta(hours=24)
    result = upload(env)
    assert result.status_code == 200, result.text
    # One request removes only one expired raster; the other 19 do not count.
    rows = photo_rows(env["service"])
    expired_remaining = [p for p in old if p["photo_id"] in rows]
    assert len(rows) == 20 and len(expired_remaining) == 19
    assert get_photo(env, expired_remaining[0], env["technician"]).status_code == 404
    with pytest.raises(OperationError) as err:
        env["service"].prepare(
            env["technician"],
            "record_verdict",
            {
                "work_item_id": expired_remaining[0]["work_item_id"],
                "outcome": "confirmed",
                "photo_ids": [expired_remaining[0]["photo_id"]],
            },
        )
    assert err.value.code == "invalid_photo"
    assert photo_rows(env["service"]) == rows  # Reads and prepare do not collect data.
    assert upload(env).status_code == 200
    assert len(photo_rows(env["service"])) == 20


def test_active_proposal_extends_draft_lifetime_then_attached_photo_never_expires(env, monkeypatch):
    time = clock(monkeypatch)
    initial = time[0]
    bound, abandoned = upload(env).json(), upload(env).json()
    time[0] = initial + timedelta(hours=23, minutes=59)
    p = verdict(env, bound)
    time[0] = initial + timedelta(hours=24, minutes=1)
    assert upload(env).status_code == 200
    assert bound["photo_id"] in photo_rows(env["service"])
    assert abandoned["photo_id"] not in photo_rows(env["service"])
    assert get_photo(env, bound, env["technician"]).status_code == 200
    assert env["client"].delete(bound["url"], headers=env["headers"](env["technician"])).status_code == 409
    # A protected older draft remains active and still consumes a current-scope slot.
    for _ in range(18):
        assert upload(env).status_code == 200
    assert upload(env).status_code == 409
    cmd = confirm(env, p, env["technician"])
    assert cmd["status"] == "succeeded", cmd
    assert upload(env).status_code == 200  # Attachment frees the pending slot.
    time[0] += timedelta(days=30)
    assert upload(env).status_code == 200
    assert photo_rows(env["service"])[bound["photo_id"]] == "attached"
    assert get_photo(env, bound, env["dispatcher"]).status_code == 200
    assert confirm(env, p, env["technician"]) == cmd


def test_expired_unconfirmed_binding_is_collected_without_deleting_proposal_history(env, monkeypatch):
    time = clock(monkeypatch)
    initial = time[0]
    photo = upload(env).json()
    p = verdict(env, photo)
    time[0] = initial + timedelta(hours=25)
    assert upload(env).status_code == 200
    assert photo["photo_id"] not in photo_rows(env["service"])
    with env["service"].db.connect() as db:
        assert db.execute("SELECT 1 FROM proposals WHERE proposal_id=?", (p["proposal_id"],)).fetchone()
        assert not db.execute("SELECT 1 FROM proposal_photos WHERE photo_id=?", (photo["photo_id"],)).fetchone()
    response = env["client"].post(
        f"/api/operations/proposals/{p['proposal_id']}/confirm", headers=env["headers"](env["technician"])
    )
    assert response.status_code == 409 and response.json()["detail"]["code"] == "proposal_expired"


def test_pending_command_protects_aged_photo_and_original_uploader_recovery(env, monkeypatch):
    time = clock(monkeypatch)
    initial = time[0]
    s, tech, dispatcher = env["service"], env["technician"], env["dispatcher"]
    protected, abandoned = upload(env).json(), upload(env).json()
    p = verdict(env, protected)
    real_apply = s._apply

    def fail_ledger(*args, **kwargs):
        raise OSError("synthetic interruption after file publication")

    monkeypatch.setattr(s, "_apply", fail_ledger)
    cmd = confirm(env, p, tech)
    assert cmd["status"] == "reconciling"
    monkeypatch.setattr(s, "_apply", real_apply)
    time[0] = initial + timedelta(days=30)
    another_uploader = tech.model_copy(update={"user_id": "other-authorized-technician"})
    assert upload(env, actor=another_uploader).status_code == 200
    assert protected["photo_id"] in photo_rows(s)
    assert abandoned["photo_id"] not in photo_rows(s)
    assert env["client"].delete(protected["url"], headers=env["headers"](tech)).status_code == 409
    revoked = tech.model_copy(update={"crew_id": "revoked"})
    recovered = s.command(dispatcher, cmd["command_id"])
    assert recovered["status"] == "succeeded", recovered
    assert recovered["result"]["finding"]["actor_id"] == tech.user_id
    assert recovered["result"]["finding"]["reconciled_by"]["user_id"] == dispatcher.user_id
    assert get_photo(env, protected, revoked).status_code == 404
    assert get_photo(env, protected, dispatcher).status_code == 200
    assert len(work(s.context(dispatcher), protected["work_item_id"])["findings"]) == 1


@pytest.mark.parametrize("change", ["membership", "assignment"])
def test_inaccessible_old_drafts_cannot_block_current_technician_quota(env, change):
    s, tech = env["service"], env["technician"]
    old = [upload(env).json() for _ in range(20)]
    verdict(env, old[0])  # Protected evidence must survive a crew/scope change.
    if change == "membership":
        route = next(
            r for r in s.context(env["dispatcher"])["plan"]["routes"] if r["crew_id"] != tech.crew_id and r["stops"]
        )
        current = tech.model_copy(update={"crew_id": route["crew_id"]})
        wid = route["stops"][0]["work_item_id"]
    else:
        wid = next(
            w["work_item_id"] for w in s.context(tech)["work_items"] if w["work_item_id"] != old[0]["work_item_id"]
        )
        plan_path = s.outputs / "plans/demo-vara/plan.json"
        plan = json.loads(plan_path.read_text())
        for route in plan["routes"]:
            route["stops"] = [stop for stop in route["stops"] if stop["work_item_id"] != old[0]["work_item_id"]]
        plan_path.write_text(json.dumps(plan))
        current = tech
    result = upload(env, actor=current, wid=wid)
    assert result.status_code == 200, result.text
    rows = photo_rows(s)
    assert len(rows) == 21 and all(rows[p["photo_id"]] == "draft" for p in old)
    assert get_photo(env, old[0], current).status_code == 404
    assert env["client"].delete(old[0]["url"], headers=env["headers"](current)).status_code == 404


@pytest.mark.parametrize("action", ["record_verdict", "review_work_item"])
@pytest.mark.parametrize("legacy", [False, True])
def test_same_key_retry_returns_original_after_confirm_without_mutable_revalidation(env, monkeypatch, action, legacy):
    time = clock(monkeypatch)
    s = env["service"]
    case = create_case(env)
    wid = env["binding"]["work_item_id"]
    common = {
        "work_item_id": wid,
        "case_id": case["case_id"],
        "idempotency_key": "same-request-after-confirm",
        "note": "Synthetic stable client request",
    }
    if action == "record_verdict":
        photo = upload(env).json()
        actor = env["technician"]
        data = {**common, "outcome": "confirmed", "photo_ids": [photo["photo_id"]]}
        field = "findings"
    else:
        actor = env["dispatcher"]
        data = {**common, "decision": "defer", "is_correction": True}
        field = "manual_corrections"
    p = propose(env, action, data, actor)
    assert "request_data" not in p
    if legacy:
        # Pre-fix proposals did not save the canonical client-only fields.
        with s.db.transaction() as db:
            stored = json.loads(
                db.execute("SELECT body FROM proposals WHERE proposal_id=?", (p["proposal_id"],)).fetchone()["body"]
            )
            stored.pop("request_data")
            db.execute("UPDATE proposals SET body=? WHERE proposal_id=?", (json.dumps(stored), p["proposal_id"]))
    cmd = confirm(env, p, actor)
    assert cmd["status"] == "succeeded", cmd
    time[0] += timedelta(days=30)  # Consumed key survives proposal and draft lifetimes.
    retry = propose(env, action, data, actor)
    assert retry == p and confirm(env, retry, actor) == cmd
    assert len(work(s.context(env["dispatcher"]), wid)[field]) == 1
    with pytest.raises(OperationError) as err:
        s.prepare(actor, action, {**data, "note": "Changed request under the same key"})
    assert err.value.code == "idempotency_conflict"
    revoked = (
        actor.model_copy(update={"crew_id": "revoked"})
        if action == "record_verdict"
        else actor.model_copy(update={"permissions": []})
    )
    with pytest.raises(OperationError) as err:
        s.prepare(revoked, action, data)
    assert err.value.status_code == 403
    if action == "record_verdict":
        plan_path = s.outputs / "plans/demo-vara/plan.json"
        plan = json.loads(plan_path.read_text())
        for route in plan["routes"]:
            route["stops"] = [stop for stop in route["stops"] if stop["work_item_id"] != wid]
        plan_path.write_text(json.dumps(plan))
        with pytest.raises(OperationError) as err:
            s.prepare(actor, action, data)
        assert err.value.status_code == 404
