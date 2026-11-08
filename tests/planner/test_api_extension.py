"""API-ul pentru extindere: harta posturilor, pagina postului, aprobarea listei, verdictul, regulile, scara C."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cyberpunks.api import app as app_mod
from cyberpunks.api.store import Store
from cyberpunks.common.contracts import AuditRecord
from cyberpunks.planner import agent

from .conftest import DATE, SCENARIO, fixture_items, write_items
from .test_extension import LADDER, _bilant_post, _c_with_ladder


@pytest.fixture()
def live(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, Path]:
    out = tmp_path / "out"
    write_items(out, "A", fixture_items("A"))
    write_items(out, "A_bilant", [_bilant_post("PT-B002", "grid_inspection", skill="lv_grid"),
                                  _bilant_post("PT-B005", "watchlist", value=300.0, post_excess_loss_lei_month=150.0)])
    write_items(out, "C", [_c_with_ladder("PT-L001", LADDER)])
    agent.run(SCENARIO, date=DATE, mode="existing", out_root=out)
    monkeypatch.setattr(app_mod, "store", Store(outputs=out, demo=tmp_path / "demo", reports=tmp_path / "rep"))
    return TestClient(app_mod.app), out


def test_posts_map_and_detail(live) -> None:
    client, _ = live
    posts = {p["post_id"]: p for p in client.get("/api/posts", params={"scenario": SCENARIO}).json()}
    assert posts["PT-B002"]["color"] == "rosu" and posts["PT-B002"]["loss_lei_month"] == 640.0
    assert posts["PT-B005"]["color"] == "verde"
    assert posts["PT-L001"]["voltage_p90_pu"] == 1.125 and posts["PT-L001"]["c_rule_id"] == "R-REMEDY-LADDER"
    detail = client.get("/api/posts/PT-B002", params={"scenario": SCENARIO}).json()
    assert detail["work_items"][0]["decision"]["rule_id"] == "R-BILANT-GRID"
    assert client.get("/api/posts/NU-EXISTA", params={"scenario": SCENARIO}).status_code == 404
    assert client.get("/api/posts/..%2F..", params={"scenario": SCENARIO}).status_code in (404, 422)


def test_route_approval_and_verdict_labels(live) -> None:
    client, out = live
    plan = client.get("/api/plan", params={"scenario": SCENARIO}).json()
    crew = plan["routes"][0]["crew_id"]
    first = plan["routes"][0]["stops"][0]["work_item_id"]
    r = client.post(f"/api/routes/{crew}/approve", params={"scenario": SCENARIO}, json={"reviewer": "Ana", "note": "ok"})
    assert r.status_code == 200 and r.json()["work_item_ids"]
    approvals = client.get("/api/approvals", params={"scenario": SCENARIO}).json()
    assert approvals[0]["crew_id"] == crew and approvals[0]["stale"] is False
    audit = [AuditRecord.model_validate_json(x) for x in (out / "plans" / SCENARIO / "audit.jsonl").read_text(encoding="utf-8").splitlines()]
    assert any(a.action == "route_approve" and a.actor == "human" and a.work_item_id == first for a in audit)
    v = client.post(f"/api/verdict/{first}", params={"scenario": SCENARIO}, json={"outcome": "confirmed", "reviewer": "echipa E-BV-1"})
    assert v.status_code == 200 and v.json()["label"]["label"] == 1
    labels = client.get("/api/labels", params={"scenario": SCENARIO}).json()
    assert labels[0]["work_item_id"] == first and labels[0]["prediction_id"] and labels[0]["model_version"]
    assert client.post("/api/verdict/A-20261109-NU-EXISTA", params={"scenario": SCENARIO}, json={"outcome": "confirmed"}).status_code == 404
    assert client.post("/api/routes/E-NIMENI/approve", params={"scenario": SCENARIO}, json={}).status_code == 404


def test_rules_and_remedies(live) -> None:
    client, _ = live
    rules = client.get("/api/rules").json()
    assert "R-REMEDY-LADDER" in rules["rules"] and "R-FUSION-BILANT" in rules["rules"]
    assert rules["thresholds"]["posts"]["red_lei_month"] == 600
    rem = client.get("/api/remedies", params={"scenario": SCENARIO}).json()
    assert rem[0]["chosen"] == ["export_limit"]


def test_feedback_needs_a_live_plan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app_mod, "store", Store(outputs=tmp_path / "o", demo=tmp_path / "d", reports=tmp_path / "r"))
    client = TestClient(app_mod.app)
    assert client.post("/api/verdict/A-20261109-MTR-004217", json={"outcome": "confirmed"}).status_code == 409
    assert client.post("/api/routes/E-BV-1/approve", json={}).status_code == 409


def test_run_info_and_health(live) -> None:
    client, _ = live
    info = client.get("/api/run-info", params={"scenario": SCENARIO}).json()
    assert set(info["timings"]) >= {"perceive", "estimate", "decide", "act"} and info["solver"]["name"] in ("ortools", "greedy")
    assert info["data_mode"] == "live"
    health = client.get("/api/health", params={"scenario": SCENARIO}).json()
    assert health["plan_id"] == info["plan_id"] and health["mode"] == "live"
    assert client.get("/api/run-info", params={"scenario": "nimic"}).status_code == 404


def test_plan_approval(live) -> None:
    client, out = live
    plan = client.get("/api/plan", params={"scenario": SCENARIO}).json()
    assert client.get("/api/plan/approval", params={"scenario": SCENARIO}).json()["approved"] is False
    r = client.post("/api/plan/approve", json={"scenario": SCENARIO, "plan_id": plan["plan_id"], "approver": "Ana", "note": "ok"})
    assert r.status_code == 200 and r.json()["action"] == "plan_approved" and r.json()["actor"] == "human"
    assert client.get("/api/plan/approval", params={"scenario": SCENARIO}).json()["approved"] is True
    assert client.post("/api/plan/approve", json={"scenario": SCENARIO, "plan_id": "PLAN-vechi"}).status_code == 409
    assert (out / "plans" / SCENARIO / "posts.json").exists()


def test_api_source_can_be_pinned_to_demo(live, tmp_path, monkeypatch) -> None:
    from cyberpunks.planner.snapshot import snapshot

    client, out = live
    snapshot(SCENARIO, src=out, dest=tmp_path / "demo", reports=tmp_path / "rep")
    monkeypatch.setenv("CYBERPUNKS_API_SOURCE", "demo")
    assert client.get("/api/health", params={"scenario": SCENARIO}).json()["mode"] == "demo"
    assert (tmp_path / "demo" / "plans" / SCENARIO / "posts.json").exists()


def test_review_through_the_api_replans(live) -> None:
    """Cap-coadă prin API: dispecerul aprobă un caz din coada „nu sunt sigur” și respinge altul; planul se recalculează,
    cazul aprobat intră în traseu, cel respins iese, jurnalul păstrează ambele decizii, iar aprobarea veche a planului expiră."""
    client, _ = live
    q = {"scenario": SCENARIO}
    plan = client.get("/api/plan", params=q).json()
    human = [d for d in plan["decisions"] if d["decision"] == "human_review"]
    assert len(human) >= 1
    approved_id = human[0]["work_item_id"]
    assert client.post("/api/plan/approve", json={"scenario": SCENARIO, "plan_id": plan["plan_id"], "approver": "Ana"}).status_code == 200

    r = client.post(f"/api/review/{approved_id}", params=q, json={"decision": "approve", "reviewer": "Ana", "note": "merg"})
    assert r.status_code == 200 and r.json()["actor"] == "human" and r.json()["action"] == "review_approve"
    after = client.get("/api/plan", params=q).json()
    assert after["plan_id"] != plan["plan_id"]
    d = next(x for x in after["decisions"] if x["work_item_id"] == approved_id)
    assert d["rule_id"] == "R-HUMAN-APPROVE" and d["decision"] in ("assigned", "remote_action")
    if d["decision"] == "assigned":
        assert any(st["work_item_id"] == approved_id for rt in after["routes"] for st in rt["stops"])
    assert client.get("/api/plan/approval", params=q).json()["approved"] is False  # planul aprobat nu mai e cel curent

    stop = next(st["work_item_id"] for rt in after["routes"] for st in rt["stops"] if st["work_item_id"] != approved_id)
    assert client.post(f"/api/review/{stop}", params=q, json={"decision": "reject", "reviewer": "Ana"}).status_code == 200
    final = client.get("/api/plan", params=q).json()
    gone = next(x for x in final["decisions"] if x["work_item_id"] == stop)
    assert gone["rule_id"] == "R-HUMAN-REJECT" and all(st["work_item_id"] != stop for rt in final["routes"] for st in rt["stops"])
    actions = [a["action"] for a in client.get("/api/audit", params={**q, "work_item_id": approved_id}).json()]
    assert "review_approve" in actions
    assert client.post("/api/review/A-20261109-MTR-999999", params=q, json={"decision": "approve"}).status_code == 404
    assert client.post("/api/review/..%2Fplan", params=q, json={"decision": "approve"}).status_code in (404, 422)
    assert client.post(f"/api/review/{stop}", params=q, json={"decision": "poate"}).status_code == 422
