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
