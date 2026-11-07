import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest

from cyberpunks.operations.models import OperationError
from cyberpunks.operations.service import OperationsService

from .conftest import confirm, create_case, propose


def test_service_auth_before_actor_parse(env, monkeypatch):
    c = env["client"]
    for headers in ({}, {"X-Daybreak-Actor": "{bad"}, {"Authorization": "Bearer wrong", "X-Daybreak-Actor": "{bad"}):
        assert c.get("/api/operations/context", headers=headers).status_code == 401
    assert (
        c.get(
            "/api/operations/context",
            headers={"Authorization": "Bearer test-internal-token-only", "X-Daybreak-Actor": "{bad"},
        ).status_code
        == 401
    )
    monkeypatch.delenv("DAYBREAK_INTERNAL_TOKEN")
    assert c.get("/api/operations/context").status_code == 503


def test_read_scopes_and_role_denial(env):
    s, customer, tech, dispatch = (env[k] for k in ("service", "customer", "technician", "dispatcher"))
    own, crew, all_ = s.context(customer), s.context(tech), s.context(dispatch)
    assert own["work_items"] == [] and "routes" not in own["plan"] and "summary" not in own["plan"]
    assert len(all_["work_items"]) >= 600
    ids = {stop["work_item_id"] for r in crew["plan"]["routes"] for stop in r["stops"]}
    assert {w["work_item_id"] for w in crew["work_items"]} == ids
    assert all(r["crew_id"] == tech.crew_id for r in crew["plan"]["routes"])
    assert crew["next_stop"] is None
    other_org = dispatch.model_copy(update={"organization_id": "other-org"})
    with pytest.raises(OperationError) as err:
        s.context(other_org)
    assert err.value.status_code == 404
    for action, data in [
        ("approve_plan", {"plan_id": all_["plan"]["plan_id"]}),
        ("review_work_item", {"work_item_id": next(iter(ids)), "decision": "approve"}),
        ("record_verdict", {"work_item_id": next(iter(ids)), "outcome": "confirmed"}),
    ]:
        r = env["client"].post(
            "/api/operations/proposals", headers=env["headers"](), json={"action": action, "data": data}
        )
        assert r.status_code == 403
    restricted = dispatch.model_copy(update={"permissions": []})
    with pytest.raises(OperationError) as err:
        s.prepare(restricted, "approve_plan", {"plan_id": all_["plan"]["plan_id"]})
    assert err.value.status_code == 403
    foreign = next(w for w in all_["work_items"] if w["work_item_id"] not in ids)
    with pytest.raises(OperationError) as err:
        s.prepare(tech, "record_verdict", {"work_item_id": foreign["work_item_id"], "outcome": "confirmed"})
    assert err.value.status_code == 404


def test_proposal_is_not_an_effect_and_confirm_is_shared_and_idempotent(env):
    s, customer = env["service"], env["customer"]
    data = {
        "connection_id": env["binding"]["connection_id"],
        "symptom": "Inverter stops at noon",
        "symptom_type": "meter",
    }
    p = propose(env, "create_case", data)
    assert not s.context(customer)["cases"]
    assert propose(env, "create_case", data)["proposal_id"] == p["proposal_id"]
    cmd = confirm(env, p)
    assert cmd["status"] == "succeeded" and cmd["result"]["repaired"] is False
    assert confirm(env, p) == cmd
    assert s.command(customer, cmd["command_id"]) == cmd
    for actor in [customer, env["technician"], env["dispatcher"]]:
        assert s.context(actor)["cases"][0]["case_id"] == cmd["result"]["case"]["case_id"]
    assert len(s.context(env["dispatcher"])["events"]) == 1
    s2 = OperationsService(s.outputs, s.db_path)
    assert s2.context(customer)["cases"][0]["case_id"] == cmd["result"]["case"]["case_id"]
    # Same report from a separate retry key still does not duplicate the operational case.
    retry = confirm(env, propose(env, "create_case", {**data, "idempotency_key": "retry-report"}))
    assert retry["result"]["deduplicated"] is True
    assert len(s.context(customer)["cases"]) == 1


def test_case_connection_isolation_and_identity_injection(env):
    s, a = env["service"], env["customer"]
    case = create_case(env)
    other = a.model_copy(update={"user_id": "other-customer"})
    assert s.context(other)["cases"] == []
    for who in [other, a.model_copy(update={"connection_ids": ["unknown"]})]:
        with pytest.raises(OperationError) as err:
            s.prepare(
                who,
                "set_availability",
                {"case_id": case["case_id"], "start": "2026-11-08T10:00:00+02:00", "end": "2026-11-08T11:00:00+02:00"},
            )
        assert err.value.status_code == 404
    for data in [
        {"connection_id": "unknown", "symptom": "No power"},
        {"connection_id": env["binding"]["connection_id"], "symptom": "No power", "role": "dispatcher"},
    ]:
        with pytest.raises(OperationError) as err:
            s.prepare(a, "create_case", data)
        assert err.value.status_code in (404, 422)


def test_proposal_owner_expiry_and_membership(env):
    s, a = env["service"], env["customer"]
    p = propose(env, "request_human", {"connection_id": env["binding"]["connection_id"], "reason": "Need assistance"})
    with pytest.raises(OperationError) as err:
        s.confirm(a.model_copy(update={"user_id": "other"}), p["proposal_id"])
    assert err.value.status_code == 404
    with pytest.raises(OperationError) as err:
        s.confirm(a.model_copy(update={"connection_ids": []}), p["proposal_id"])
    assert err.value.status_code == 403
    with s.db.transaction() as db:
        row = json.loads(
            db.execute("SELECT body FROM proposals WHERE proposal_id=?", (p["proposal_id"],)).fetchone()["body"]
        )
        row["expires_at"] = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()
        db.execute("UPDATE proposals SET body=? WHERE proposal_id=?", (json.dumps(row), p["proposal_id"]))
    with pytest.raises(OperationError) as err:
        s.confirm(a, p["proposal_id"])
    assert err.value.code == "proposal_expired"
    assert not s.context(env["dispatcher"])["events"]


def test_case_versions_and_access_window_are_requests(env):
    s, a = env["service"], env["customer"]
    case = create_case(env)
    p = propose(
        env,
        "set_availability",
        {
            "case_id": case["case_id"],
            "case_version": 1,
            "start": "2026-11-08T10:00:00+02:00",
            "end": "2026-11-08T11:00:00+02:00",
        },
    )
    q = propose(env, "request_human", {"case_id": case["case_id"], "reason": "Please review this case"})
    confirm(env, q)
    with pytest.raises(OperationError) as err:
        s.confirm(a, p["proposal_id"])
    assert err.value.code == "stale_case"
    fresh = propose(
        env,
        "set_availability",
        {"case_id": case["case_id"], "start": "2026-11-08T10:00:00+02:00", "end": "2026-11-08T11:00:00+02:00"},
    )
    saved = confirm(env, fresh)["result"]["case"]
    assert saved["availability"]["status"] == "requested"
    assert "scheduled" not in saved["status"]
    assert s.context(env["dispatcher"])["human_requests"][0]["status"] == "queued"


def test_plan_approval_and_stale_version(env):
    s, d = env["service"], env["dispatcher"]
    case = create_case(env)
    plan = s.context(d)["plan"]
    approval = propose(env, "approve_plan", {"plan_id": plan["plan_id"]}, d)
    stale = propose(
        env,
        "record_verdict",
        {"work_item_id": env["binding"]["work_item_id"], "outcome": "confirmed"},
        env["technician"],
    )
    cmd = confirm(env, approval, d)
    assert cmd["status"] == "succeeded" and cmd["result"]["effect"]["effect_verified"]
    assert s.context(d)["plan"]["approved"] is True
    assert s.context(env["customer"])["cases"][0]["status"] == "intervention_approved"
    assert s.context(env["technician"])["next_stop"] is not None
    assert confirm(env, approval, d) == cmd
    with pytest.raises(OperationError) as err:
        s.confirm(env["technician"], stale["proposal_id"])
    assert err.value.code == "stale_plan"
    audit = [json.loads(x) for x in (env["root"] / "plans/demo-vara/audit.jsonl").read_text().splitlines()]
    assert sum(a["action"] == "plan_approved" for a in audit) == 1
    assert case["case_id"] == cmd["result"]["case"]["case_id"]


@pytest.mark.parametrize(
    "outcome,label,status",
    [
        ("confirmed", 1, "verification_after_visit"),
        ("not_found", 0, "verification_after_visit"),
        ("no_access", None, "access_blocked"),
        ("other_problem", None, "verification_after_visit"),
    ],
)
def test_field_verdict_is_actual_but_not_a_repair(env, outcome, label, status):
    create_case(env)
    s, t = env["service"], env["technician"]
    p = propose(env, "record_verdict", {"work_item_id": env["binding"]["work_item_id"], "outcome": outcome}, t)
    cmd = confirm(env, p, t)
    assert cmd["status"] == "succeeded"
    assert cmd["result"]["effect"]["label"]["label"] == label
    assert cmd["result"]["repaired"] is False
    assert s.context(env["customer"])["cases"][0]["status"] == status
    assert confirm(env, p, t) == cmd
    labels = [json.loads(x) for x in (env["root"] / "plans/demo-vara/labels.jsonl").read_text().splitlines()]
    assert len(labels) == 1 and labels[0]["prediction_id"] and labels[0]["model_version"]
    assert labels[0]["work_item_id"] == env["binding"]["work_item_id"]


def test_concurrent_confirmation_executes_once(env):
    s, a = env["service"], env["customer"]
    p = propose(env, "create_case", {"connection_id": env["binding"]["connection_id"], "symptom": "Power stops"})
    with ThreadPoolExecutor(max_workers=3) as pool:
        commands = list(pool.map(lambda _: s.confirm(a, p["proposal_id"]), range(3)))
    assert len({c["command_id"] for c in commands}) == 1
    assert len(s.context(a)["cases"]) == 1
    assert len(s.context(env["dispatcher"])["events"]) == 1


def test_two_competing_case_writes_conflict(env):
    case = create_case(env)
    p = propose(env, "request_human", {"case_id": case["case_id"], "reason": "First request"})
    q = propose(env, "request_human", {"case_id": case["case_id"], "reason": "Second request"})
    s, a = env["service"], env["customer"]

    def execute(proposal):
        try:
            return s.confirm(a, proposal["proposal_id"])["status"]
        except OperationError as e:
            return e.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(execute, [p, q]))
    assert sorted(statuses) == ["stale_case", "succeeded"]


def test_replan_calls_real_planner_and_deletes_stale_pdfs(env):
    s, d = env["service"], env["dispatcher"]
    create_case(env)
    before = s.context(d)["plan"]
    crew = env["binding"]["crew_id"]
    pdf = env["root"] / f"plans/demo-vara/work_orders/{crew}.pdf"
    assert pdf.exists()
    # Real workorder writer deletes PDFs not present in its new route set.
    stale_pdf = env["root"] / "plans/demo-vara/work_orders/STALE-QA-CREW.pdf"
    stale_pdf.write_bytes(b"synthetic obsolete workorder")
    # Reject one assigned stop; the actual planner must remove the obsolete work order too.
    rejected = [
        stop["work_item_id"] for route in before["routes"] if route["crew_id"] == crew for stop in route["stops"]
    ][:1]
    for wid in rejected:
        p = propose(
            env, "review_work_item", {"work_item_id": wid, "decision": "reject", "note": "QA synthetic review"}, d
        )
        cmd = confirm(env, p, d)
        assert cmd["status"] == "succeeded", cmd
    assert not stale_pdf.exists()
    after = s.context(d)["plan"]
    assert after["plan_id"] != before["plan_id"]
    assert not any(stop["work_item_id"] in rejected for r in after["routes"] for stop in r["stops"])
    if not any(r["crew_id"] == crew for r in after["routes"]):
        assert not pdf.exists()
    overrides = json.loads((env["root"] / "plans/demo-vara/overrides.json").read_text())
    assert all(overrides[wid]["decision"] == "reject" for wid in rejected)


def test_interrupted_file_publication_recovers_without_duplicate_effect(env, monkeypatch):
    import cyberpunks.operations.planner as adapter

    s, t = env["service"], env["technician"]
    create_case(env)
    p = propose(env, "record_verdict", {"work_item_id": env["binding"]["work_item_id"], "outcome": "no_access"}, t)
    original = adapter.os.replace
    count = 0

    def interrupt(src, dest):
        nonlocal count
        if str(src).endswith(".daybreak-tmp"):
            count += 1
            if count == 2:
                raise OSError("synthetic crash after first file effect")
        return original(src, dest)

    monkeypatch.setattr(adapter.os, "replace", interrupt)
    cmd = confirm(env, p, t)
    assert cmd["status"] == "reconciling" and cmd["result"] is None
    assert s.context(env["customer"])["cases"][0]["status"] == "awaiting_decision"
    assert s.context(env["dispatcher"])["reconciliation_pending"]
    another = propose(
        env, "request_human", {"case_id": s.context(env["customer"])["cases"][0]["case_id"], "reason": "Review needed"}
    )
    with pytest.raises(OperationError) as err:
        s.confirm(env["customer"], another["proposal_id"])
    assert err.value.code == "reconciliation_pending"
    monkeypatch.setattr(adapter.os, "replace", original)
    recovered = s.command(t, cmd["command_id"])
    assert recovered["status"] == "succeeded"
    assert confirm(env, p, t) == recovered
    plan = env["root"] / "plans/demo-vara"
    audit = [json.loads(x) for x in (plan / "audit.jsonl").read_text().splitlines()]
    labels = [json.loads(x) for x in (plan / "labels.jsonl").read_text().splitlines()]
    assert sum(a["action"] == "field_verdict" for a in audit) == 1
    assert len(labels) == 1 and labels[0]["label"] is None
    assert s.context(env["customer"])["cases"][0]["status"] == "access_blocked"


def test_timeout_after_sqlite_success_recovers_by_command_id(env, monkeypatch):
    s, a = env["service"], env["customer"]
    p = propose(env, "create_case", {"connection_id": env["binding"]["connection_id"], "symptom": "Power flickers"})
    result = confirm(env, p)
    # The client loses the first response; all workers recover the durable command unchanged.
    restarted = OperationsService(s.outputs, s.db_path)
    assert restarted.command(a, result["command_id"]) == result
    assert restarted.confirm(a, p["proposal_id"]) == result
    assert len(restarted.context(a)["cases"]) == 1


def test_snapshot_is_read_only_not_silently_promoted(env, tmp_path):
    s = OperationsService(tmp_path / "no-local-run", tmp_path / "snapshot.sqlite", demo=env["root"])
    ctx = s.context(env["dispatcher"])
    assert ctx["plan"]["source"] == "demo_snapshot" and not ctx["plan"]["writable"]
    with pytest.raises(OperationError) as err:
        s.prepare(env["dispatcher"], "approve_plan", {"plan_id": ctx["plan"]["plan_id"]})
    assert err.value.code == "read_only_snapshot"
    assert not (tmp_path / "no-local-run").exists()


@pytest.mark.parametrize("kind", ["abstain", "date", "missing", "provenance"])
def test_model_absence_or_mismatch_never_creates_a_probability(env, kind):
    path = env["root"] / "plans/demo-vara/work_items.jsonl"
    rows = [json.loads(x) for x in path.read_text().splitlines()]
    selected = [w for w in rows if w["source"] == "C" and w["asset_id"] == env["binding"]["post_id"]]
    assert selected
    w = selected[0]
    if kind == "abstain":
        w["prediction"].update(abstain=True, abstain_reason="Synthetic QA abstention")
    elif kind == "date":
        w["target_date"] = "2000-01-01"
    elif kind == "missing":
        w["data_quality"]["missing_ratio"] = 0.8
    else:
        w["prediction"].pop("model_version")
    path.write_text("\n".join(json.dumps(w) for w in rows) + "\n")
    c = create_case(env, symptom_type="voltage")
    assert c["status"] == "awaiting_data"
    assert c["assessment"]["status"] == "needs_data" and c["assessment"]["score"] is None


def test_voltage_assessment_matches_authorized_post_and_model(env):
    c = create_case(env, symptom_type="voltage")
    ctx = env["service"].context(env["dispatcher"])
    predicted = next(w for w in ctx["work_items"] if w["source"] == "C" and w["asset_id"] == env["binding"]["post_id"])
    a = c["assessment"]
    assert a["prediction_id"] == predicted["prediction"]["prediction_id"]
    assert a["model_version"] == predicted["prediction"]["model_version"]
    assert a["score"] == predicted["prediction"]["score"]
    assert a["target_date"] == ctx["plan"]["plan_date"] and a["scenario"] == "demo-vara"
    assert a["synthetic"] and a["source"] == "local_run"
    assert c["connection_id"] == env["binding"]["connection_id"]


def test_idempotency_key_conflict_and_unknown_actions(env):
    s, a = env["service"], env["customer"]
    p = propose(
        env,
        "create_case",
        {"connection_id": env["binding"]["connection_id"], "symptom": "No power", "idempotency_key": "same"},
    )
    with pytest.raises(OperationError) as err:
        s.prepare(
            a,
            "create_case",
            {
                "connection_id": env["binding"]["connection_id"],
                "symptom": "Different report",
                "idempotency_key": "same",
            },
        )
    assert err.value.code == "idempotency_conflict"
    r = env["client"].post(
        "/api/operations/proposals", headers=env["headers"](), json={"action": "shell", "data": {"command": "anything"}}
    )
    assert r.status_code == 422
    assert confirm(env, p)["status"] == "succeeded"


def test_same_post_does_not_conflate_voltage_case_with_meter_verdict(env):
    s, t = env["service"], env["technician"]
    meter = create_case(env)
    voltage = create_case(env, symptom_type="voltage", symptom="Inverter stops at noon")
    assert meter["assessment"]["work_item_id"] == env["binding"]["work_item_id"]
    assert voltage["assessment"]["work_item_id"].startswith("C-")
    assert meter["assessment"]["work_item_id"] != voltage["assessment"]["work_item_id"]
    cases_for_tech = s.context(t)["cases"]
    assert {c["case_id"] for c in cases_for_tech} == {meter["case_id"]}
    cmd = confirm(
        env,
        propose(env, "record_verdict", {"work_item_id": env["binding"]["work_item_id"], "outcome": "confirmed"}, t),
        t,
    )
    assert cmd["status"] == "succeeded"
    cases = {c["case_id"]: c for c in s.context(env["customer"])["cases"]}
    assert cases[meter["case_id"]]["status"] == "verification_after_visit"
    assert cases[voltage["case_id"]]["status"] == "awaiting_decision"
    assert cases[voltage["case_id"]]["version"] == 1
    assert "verdict" not in cases[voltage["case_id"]]


def test_no_matching_model_leaves_case_unlinked_instead_of_arbitrary_work(env):
    c = create_case(env, symptom_type="outage", symptom="There is no power now")
    raw = env["service"].context(env["dispatcher"])["cases"][0]
    assert c["status"] == "awaiting_data" and c["assessment"]["score"] is None
    assert raw["work_item_id"] is None
    assert env["service"].context(env["technician"])["cases"] == []


def test_saved_assessment_loses_current_status_after_prediction_replaced(env):
    c = create_case(env)
    path = env["root"] / "plans/demo-vara/work_items.jsonl"
    rows = [json.loads(x) for x in path.read_text().splitlines()]
    selected = next(w for w in rows if w["work_item_id"] == c["assessment"]["work_item_id"])
    selected["prediction"]["prediction_id"] = "new-prediction-id-for-qa"
    path.write_text("\n".join(json.dumps(w) for w in rows) + "\n")
    current = env["service"].context(env["customer"])["cases"][0]
    assert current["assessment"]["status"] == "stale"
    assert current["assessment"]["score"] is None
    assert current["assessment"]["prediction_id"] == c["assessment"]["prediction_id"]


def test_completed_file_effect_then_database_failure_recovers_atomically(env, monkeypatch):
    s, t = env["service"], env["technician"]
    create_case(env)
    p = propose(env, "record_verdict", {"work_item_id": env["binding"]["work_item_id"], "outcome": "confirmed"}, t)
    original = s._save_case

    def fail_database(db, case):
        raise RuntimeError("synthetic database failure after complete file effect")

    monkeypatch.setattr(s, "_save_case", fail_database)
    cmd = confirm(env, p, t)
    assert cmd["status"] == "reconciling"
    assert s.context(env["customer"])["cases"][0]["version"] == 1
    assert len(s.context(env["dispatcher"])["events"]) == 1
    monkeypatch.setattr(s, "_save_case", original)
    recovered = s.command(t, cmd["command_id"])
    assert recovered["status"] == "succeeded"
    labels = [json.loads(x) for x in (env["root"] / "plans/demo-vara/labels.jsonl").read_text().splitlines()]
    assert len(labels) == 1
    assert s.context(env["customer"])["cases"][0]["version"] == 2
    assert len(s.context(env["dispatcher"])["events"]) == 2


def test_new_linked_case_invalidates_prior_field_proposal(env):
    s, t = env["service"], env["technician"]
    p = propose(env, "record_verdict", {"work_item_id": env["binding"]["work_item_id"], "outcome": "confirmed"}, t)
    create_case(env)
    with pytest.raises(OperationError) as err:
        s.confirm(t, p["proposal_id"])
    assert err.value.code == "stale_case"
    assert not (env["root"] / "plans/demo-vara/labels.jsonl").exists()
