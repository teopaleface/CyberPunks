"""Private findings and human corrections on isolated, complete local planner copies."""

import asyncio
import json
from io import BytesIO
from uuid import uuid4

import pytest
from fastapi import HTTPException
from PIL import Image
from starlette.requests import Request

from cyberpunks.operations import photos
from cyberpunks.operations.models import OperationError
from cyberpunks.operations.router import upload_photo as upload_endpoint
from cyberpunks.operations.service import OperationsService

from .conftest import confirm, create_case, propose


def raster(fmt="JPEG", *, exif=False):
    output = BytesIO()
    image = Image.new("RGB", (24, 16), "red")  # Clearly synthetic test raster.
    metadata = Image.Exif()
    metadata[0x010E] = "synthetic private source metadata"
    image.save(output, format=fmt, **({"exif": metadata} if exif else {}))
    return output.getvalue()


def upload(env, *, wid=None, actor=None, body=None, mime="image/jpeg", scenario="demo-vara", **headers):
    actor = actor or env["technician"]
    wid = wid or env["binding"]["work_item_id"]
    return env["client"].post(
        f"/api/operations/work-items/{wid}/photos?scenario={scenario}",
        headers=env["headers"](actor, **{"Content-Type": mime, **headers}),
        content=body if body is not None else raster(),
    )


def get_photo(env, photo, actor):
    return env["client"].get(photo["url"], headers=env["headers"](actor))


def verdict(env, photo, **extra):
    return propose(
        env,
        "record_verdict",
        {"work_item_id": photo["work_item_id"], "outcome": "confirmed", "photo_ids": [photo["photo_id"]], **extra},
        env["technician"],
    )


def work(context, wid):
    return next(w for w in context["work_items"] if w["work_item_id"] == wid)


@pytest.mark.parametrize("with_case", [False, True])
def test_photo_finding_prepare_confirm_durable_private_and_idempotent(env, with_case):
    s, tech, dispatcher = env["service"], env["technician"], env["dispatcher"]
    if with_case:
        create_case(env)
    plan_version = s.planner.version("demo-vara")
    r = upload(env, body=raster(exif=True), **{"X-File-Name": "../../private.svg"})
    assert r.status_code == 200, r.text
    photo = r.json()
    assert photo["status"] == "draft" and photo["width"] == 24 and photo["height"] == 16
    assert s.planner.version("demo-vara") == plan_version
    assert not work(s.context(tech), photo["work_item_id"])["findings"]
    for actor in [env["customer"], dispatcher, tech.model_copy(update={"user_id": "another-tech"})]:
        assert get_photo(env, photo, actor).status_code == 404
    image = get_photo(env, photo, tech)
    assert image.status_code == 200 and image.headers["cache-control"] == "private, no-store"
    assert image.headers["x-content-type-options"] == "nosniff"
    assert image.headers["content-type"] == "image/jpeg"
    assert len(image.content) == photo["size_bytes"]
    assert not Image.open(BytesIO(image.content)).getexif()
    assert b"private source metadata" not in image.content
    p = verdict(env, photo, note="Synthetic test finding")
    assert p["data"]["photos"] == [photo]
    assert not work(s.context(tech), photo["work_item_id"])["findings"]
    assert get_photo(env, photo, dispatcher).status_code == 404
    cmd = confirm(env, p, tech)
    assert cmd["status"] == "succeeded", cmd
    finding = cmd["result"]["finding"]
    assert finding["actor_id"] == tech.user_id and finding["actor_role"] == "technician"
    assert finding["photos"] == [{**photo, "status": "attached"}]
    assert finding["note"] == "Synthetic test finding" and finding["repair_confirmed"] is False
    assert confirm(env, p, tech) == cmd
    restarted = OperationsService(s.outputs, s.db_path)
    for actor in [tech, dispatcher]:
        context = restarted.context(actor)
        item = work(context, photo["work_item_id"])
        assert item["findings"] == [finding] and item["photos"] == finding["photos"]
        assert context["events"][-1]["finding"] == finding
        assert get_photo(env, photo, actor).status_code == 200
    customer_context = restarted.context(env["customer"])
    assert customer_context["work_items"] == []
    assert '"photos"' not in json.dumps(customer_context)
    assert '"finding"' not in json.dumps(customer_context)
    assert get_photo(env, photo, env["customer"]).status_code == 404
    if with_case:
        assert s.context(dispatcher)["cases"][0]["verdict"]["photos"] == finding["photos"]
    assert env["client"].delete(photo["url"], headers=env["headers"](tech)).status_code == 409
    with s.db.connect() as db:
        assert db.execute("SELECT count(*) FROM findings").fetchone()[0] == 1
        assert db.execute("SELECT count(*) FROM photos WHERE status='attached'").fetchone()[0] == 1


@pytest.mark.parametrize("fmt,mime", [("PNG", "image/png"), ("WEBP", "image/webp")])
def test_supported_raster_formats(env, fmt, mime):
    r = upload(env, body=raster(fmt), mime=mime)
    assert r.status_code == 200, r.text
    result = get_photo(env, r.json(), env["technician"])
    assert result.status_code == 200 and result.headers["content-type"] == mime
    assert Image.open(BytesIO(result.content)).format == fmt


@pytest.mark.parametrize(
    "body,mime,status",
    [
        (b'<svg xmlns="http://www.w3.org/2000/svg"/>', "image/svg+xml", 415),
        (b"<html><script>alert(1)</script></html>", "image/jpeg", 422),
        (b"not an image", "image/png", 422),
        (raster("PNG"), "image/jpeg", 415),
        (raster()[:50], "image/jpeg", 422),
    ],
)
def test_rejects_non_rasters_mismatch_and_truncation(env, body, mime, status):
    assert upload(env, body=body, mime=mime).status_code == status
    with env["service"].db.connect() as db:
        assert db.execute("SELECT count(*) FROM photos").fetchone()[0] == 0


def test_photo_auth_scope_current_route_and_revocation(env):
    s, tech = env["service"], env["technician"]
    for actor in [env["customer"], env["dispatcher"]]:
        assert upload(env, actor=actor).status_code == 403
    assert env["client"].post("/api/operations/work-items/guess/photos", content=raster()).status_code == 401
    assert upload(env, actor=tech.model_copy(update={"organization_id": "other"})).status_code == 404
    assert upload(env, scenario="other-scenario").status_code == 404
    assert upload(env, actor=tech.model_copy(update={"crew_id": "other-crew"})).status_code == 404
    photo = upload(env).json()
    revoked = tech.model_copy(update={"crew_id": "other-crew"})
    assert get_photo(env, photo, revoked).status_code == 404
    assert env["client"].delete(photo["url"], headers=env["headers"](revoked)).status_code == 404
    plan_path = s.outputs / "plans/demo-vara/plan.json"
    plan = json.loads(plan_path.read_text())
    for route in plan["routes"]:
        route["stops"] = [stop for stop in route["stops"] if stop["work_item_id"] != photo["work_item_id"]]
    plan_path.write_text(json.dumps(plan))
    assert get_photo(env, photo, tech).status_code == 404
    assert upload(env).status_code == 404


def test_photo_limit_quota_and_pending_delete(env):
    first = upload(env).json()
    assert env["client"].delete(first["url"], headers=env["headers"](env["technician"])).status_code == 200
    assert get_photo(env, first, env["technician"]).status_code == 404
    ids = [upload(env).json()["photo_id"] for _ in range(20)]
    assert upload(env).status_code == 409
    for selected in [ids[:7], [ids[0], ids[0]], ["not-a-uuid"]]:
        r = env["client"].post(
            "/api/operations/proposals",
            headers=env["headers"](env["technician"]),
            json={
                "action": "record_verdict",
                "data": {"work_item_id": first["work_item_id"], "outcome": "confirmed", "photo_ids": selected},
            },
        )
        assert r.status_code == 422
    assert (
        env["client"].delete(f"/api/operations/photos/{ids[0]}", headers=env["headers"](env["technician"])).status_code
        == 200
    )
    assert upload(env).status_code == 200


def test_photo_size_pixels_bomb_and_stream_bound(env, monkeypatch):
    assert upload(env, body=b"x" * (photos.MAX_BYTES + 1)).status_code == 413
    monkeypatch.setattr(photos, "MAX_PIXELS", 10)
    assert upload(env).status_code == 413
    monkeypatch.setattr(photos, "MAX_PIXELS", 12_000_000)
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 10)
    assert upload(env).status_code == 422
    # An unbounded request without Content-Length stops at the first oversized chunk.
    consumed = []

    async def receive():
        consumed.append(1)
        return {"type": "http.request", "body": b"x" * (photos.MAX_BYTES + 1), "more_body": True}

    req = Request({"type": "http", "method": "POST", "headers": [(b"content-type", b"image/jpeg")]}, receive)
    with pytest.raises(HTTPException) as err:
        asyncio.run(upload_endpoint(env["binding"]["work_item_id"], req, env["technician"], env["service"]))
    assert err.value.status_code == 413 and consumed == [1]


def test_prepared_photo_cannot_be_deleted_and_missing_photo_refuses_confirm(env):
    photo = upload(env).json()
    p = verdict(env, photo)
    assert env["client"].delete(photo["url"], headers=env["headers"](env["technician"])).status_code == 409
    # Simulate corruption/removal outside the application only in this temporary database.
    with env["service"].db.connect() as db:
        db.execute("PRAGMA foreign_keys=OFF")
        db.execute("DELETE FROM photos WHERE photo_id=?", (photo["photo_id"],))
    r = env["client"].post(
        f"/api/operations/proposals/{p['proposal_id']}/confirm", headers=env["headers"](env["technician"])
    )
    assert r.status_code == 409 and r.json()["detail"]["code"] == "invalid_photo"
    assert not env["service"].context(env["dispatcher"])["events"]


def test_photo_ids_are_bound_to_work_uploader_and_scenario(env):
    s, tech = env["service"], env["technician"]
    photo = upload(env).json()
    other_wid = next(
        w["work_item_id"] for w in s.context(tech)["work_items"] if w["work_item_id"] != photo["work_item_id"]
    )
    for actor, wid, ids in [
        (tech, other_wid, [photo["photo_id"]]),
        (tech.model_copy(update={"user_id": "other-tech"}), photo["work_item_id"], [photo["photo_id"]]),
        (tech, photo["work_item_id"], [str(uuid4())]),
    ]:
        with pytest.raises(OperationError) as err:
            s.prepare(actor, "record_verdict", {"work_item_id": wid, "outcome": "confirmed", "photo_ids": ids})
        assert err.value.code == "invalid_photo"


def test_photo_recovery_keeps_original_uploader_and_does_not_restore_revoked_access(env, monkeypatch):
    s, tech, dispatcher = env["service"], env["technician"], env["dispatcher"]
    photo = upload(env).json()
    p = verdict(env, photo)
    real_apply = s._apply

    def fail_ledger(*args, **kwargs):
        raise OSError("synthetic interruption after planner publication")

    monkeypatch.setattr(s, "_apply", fail_ledger)
    cmd = confirm(env, p, tech)
    assert cmd["status"] == "reconciling"
    monkeypatch.setattr(s, "_apply", real_apply)
    revoked = tech.model_copy(update={"crew_id": "revoked"})
    with pytest.raises(OperationError):
        s.command(revoked, cmd["command_id"])
    recovered = s.command(dispatcher, cmd["command_id"])
    assert recovered["status"] == "succeeded", recovered
    finding = recovered["result"]["finding"]
    assert finding["actor_id"] == tech.user_id and finding["actor_role"] == "technician"
    assert finding["reconciled_by"]["user_id"] == dispatcher.user_id
    assert get_photo(env, photo, revoked).status_code == 404
    assert get_photo(env, photo, dispatcher).status_code == 200
    assert work(s.context(dispatcher), photo["work_item_id"])["findings"] == [finding]


def test_corrections_apply_real_planner_and_preserve_original_ai_history(env):
    s, dispatcher = env["service"], env["dispatcher"]
    wid = env["binding"]["work_item_id"]
    before = work(s.context(dispatcher), wid)
    original_prediction = before["prediction"]
    original_decision = before["decision"]
    plan_dir = s.outputs / "plans/demo-vara"
    # Synthetic stale PDF in temporary data must be invalidated by the real planner.
    stale_pdf = plan_dir / "work_orders" / "synthetic-stale-order.pdf"
    stale_pdf.parent.mkdir(exist_ok=True)
    stale_pdf.write_bytes(b"synthetic test artifact")
    first = propose(
        env,
        "review_work_item",
        {
            "work_item_id": wid,
            "decision": "defer",
            "is_correction": True,
            "note": "  Synthetic inspection disproves dispatch  ",
        },
        dispatcher,
    )
    assert first["data"]["decision_before"] == original_decision
    assert first["data"]["original_ai_decision_status"] == "verified"
    assert first["data"]["original_ai_decision"] == original_decision
    assert work(s.context(dispatcher), wid)["manual_corrections"] == []
    cmd = confirm(env, first, dispatcher)
    assert cmd["status"] == "succeeded", cmd
    correction = cmd["result"]["manual_correction"]
    current = work(s.context(dispatcher), wid)
    assert correction["decision_after"] == current["decision"]
    assert current["decision"]["decision"] == "deferred" and current["decision"]["rule_id"] == "R-HUMAN-DEFER"
    assert not any(stop["work_item_id"] == wid for r in s.context(dispatcher)["plan"]["routes"] for stop in r["stops"])
    assert correction["reason"] == "Synthetic inspection disproves dispatch"
    assert correction["actor_id"] == dispatcher.user_id and correction["actor_role"] == "dispatcher"
    assert current["prediction"] == original_prediction
    assert s.context(dispatcher)["events"][-1]["manual_correction"] == correction
    assert confirm(env, first, dispatcher) == cmd
    assert not stale_pdf.exists()
    second = propose(
        env,
        "review_work_item",
        {"work_item_id": wid, "decision": "reject", "is_correction": True, "note": "Synthetic duplicate work"},
        dispatcher,
    )
    second_cmd = confirm(env, second, dispatcher)
    assert second_cmd["status"] == "succeeded", second_cmd
    after = work(OperationsService(s.outputs, s.db_path).context(dispatcher), wid)
    assert len(after["manual_corrections"]) == 2
    assert after["manual_corrections"][0] == correction
    latest = after["latest_manual_correction"]
    assert latest["decision_before"] == correction["decision_after"]
    assert latest["original_ai_decision"] == original_decision
    assert latest["decision_after"]["rule_id"] == "R-HUMAN-REJECT"
    assert after["prediction"] == original_prediction


def test_correction_reason_permission_stale_version_and_browser_provenance_refused(env):
    s, dispatcher, tech = env["service"], env["dispatcher"], env["technician"]
    data = {
        "work_item_id": env["binding"]["work_item_id"],
        "decision": "defer",
        "is_correction": True,
        "note": "reason",
    }
    for bad in [
        {**data, "note": "  "},
        {**data, "note": "ab"},
        {**data, "decision_before": {}},
        {**data, "original_ai_decision": {}},
        {**data, "model_version": "browser-supplied"},
    ]:
        with pytest.raises(OperationError) as err:
            s.prepare(dispatcher, "review_work_item", bad)
        assert err.value.status_code == 422
    for actor in [tech, env["customer"], dispatcher.model_copy(update={"permissions": []})]:
        with pytest.raises(OperationError) as err:
            s.prepare(actor, "review_work_item", data)
        assert err.value.status_code == 403
    pending = s.prepare(dispatcher, "review_work_item", data)
    approve = s.prepare(dispatcher, "approve_plan", {"plan_id": s.context(dispatcher)["plan"]["plan_id"]})
    assert s.confirm(dispatcher, approve["proposal_id"])["status"] == "succeeded"
    with pytest.raises(OperationError) as err:
        s.confirm(dispatcher, pending["proposal_id"])
    assert err.value.code == "stale_plan"
    assert not work(s.context(dispatcher), data["work_item_id"])["manual_corrections"]


def test_legacy_review_is_human_history_and_prior_human_is_not_claimed_as_ai(env):
    from cyberpunks.planner.review import apply_review

    s, dispatcher = env["service"], env["dispatcher"]
    wid = env["binding"]["work_item_id"]
    apply_review("demo-vara", wid, "defer", "Synthetic historical human review", "old-human", out_root=s.outputs)
    p = s.prepare(dispatcher, "review_work_item", {"work_item_id": wid, "decision": "reject"})
    assert p["data"]["is_correction"] is False
    assert p["data"]["original_ai_decision"] is None
    assert p["data"]["original_ai_decision_status"] == "unknown"
    cmd = s.confirm(dispatcher, p["proposal_id"])
    assert cmd["status"] == "succeeded", cmd
    history = work(s.context(dispatcher), wid)["manual_corrections"]
    assert len(history) == 1 and history[0]["is_correction"] is False
    assert history[0]["original_ai_decision_status"] == "unknown"


def test_correction_recovery_keeps_issuer_and_manifest_decision(env, monkeypatch):
    from cyberpunks.planner import review

    s, dispatcher = env["service"], env["dispatcher"]
    wid = env["binding"]["work_item_id"]
    data = {"work_item_id": wid, "decision": "defer", "is_correction": True, "note": "Synthetic recoverable correction"}
    p = s.prepare(dispatcher, "review_work_item", data)
    real_apply = s._apply

    def fail_ledger(*args, **kwargs):
        raise OSError("synthetic interruption after review publication")

    monkeypatch.setattr(s, "_apply", fail_ledger)
    cmd = s.confirm(dispatcher, p["proposal_id"])
    assert cmd["status"] == "reconciling"
    monkeypatch.setattr(s, "_apply", real_apply)

    def never_repeat(*args, **kwargs):
        raise AssertionError("A recovered correction must use the durable planner effect")

    monkeypatch.setattr(review, "apply_review", never_repeat)
    recoverer = dispatcher.model_copy(update={"user_id": "authorized-recoverer", "permissions": ["recover_commands"]})
    recovered = s.command(recoverer, cmd["command_id"])
    assert recovered["status"] == "succeeded", recovered
    correction = recovered["result"]["manual_correction"]
    assert correction["actor_id"] == dispatcher.user_id
    assert correction["reconciled_by"]["user_id"] == recoverer.user_id
    assert correction["decision_before"] == p["data"]["decision_before"]
    assert correction["original_ai_decision"] == p["data"]["original_ai_decision"]
    assert correction["decision_after"] == work(s.context(recoverer), wid)["decision"]
    assert s.command(recoverer, cmd["command_id"]) == recovered
    assert work(s.context(recoverer), wid)["manual_corrections"] == [correction]


def test_upload_rechecks_current_assignment_after_decoding(env, monkeypatch):
    original = photos.sanitize
    s = env["service"]
    wid = env["binding"]["work_item_id"]

    def revoke_during_decode(content, mime):
        result = original(content, mime)
        plan_path = s.outputs / "plans/demo-vara/plan.json"
        plan = json.loads(plan_path.read_text())
        for route in plan["routes"]:
            route["stops"] = [stop for stop in route["stops"] if stop["work_item_id"] != wid]
        plan_path.write_text(json.dumps(plan))
        return result

    monkeypatch.setattr(photos, "sanitize", revoke_during_decode)
    assert upload(env).status_code == 404
    with s.db.connect() as db:
        assert db.execute("SELECT count(*) FROM photos").fetchone()[0] == 0
