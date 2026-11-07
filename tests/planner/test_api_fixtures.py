"""API-ul pe fixture-uri: forma răspunsurilor, CORS, validarea parametrilor."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cyberpunks.api import app as app_mod
from cyberpunks.api.store import Store
from cyberpunks.common.contracts import AuditRecord, Plan, Series, WorkItem


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    # Exemplele din contracts/fixtures/ doar la cerere explicită (dezvoltarea interfeței), niciodată în locul unui plan real.
    monkeypatch.setenv("CYBERPUNKS_API_SOURCE", "fixtures")
    monkeypatch.setattr(app_mod, "store", Store(outputs=tmp_path / "out", demo=tmp_path / "demo", reports=tmp_path / "rep"))
    return TestClient(app_mod.app)


def test_without_any_plan_the_api_never_serves_the_fixtures(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """QA-ul orchestratorului (17:55): scenariul `maine` arăta exemplele de test ca plan real."""
    monkeypatch.delenv("CYBERPUNKS_API_SOURCE", raising=False)
    monkeypatch.setattr(app_mod, "store", Store(outputs=tmp_path / "out", demo=tmp_path / "demo", reports=tmp_path / "rep"))
    c = TestClient(app_mod.app)
    assert c.get("/api/health", params={"scenario": "maine"}).json()["mode"] == "none"
    plan = Plan.model_validate(c.get("/api/plan", params={"scenario": "maine"}).json())
    assert plan.decisions == [] and plan.routes == [] and plan.plan_id == "FARA-PLAN-maine"
    assert set(plan.sources_status.values()) == {"missing"} and "Rulează agentul" in plan.alerts[0].body_ro
    assert c.get("/api/work-items", params={"scenario": "maine"}).json() == []
    assert "MTR-004217" not in c.get("/api/plan", params={"scenario": "maine"}).text  # contorul din exemple


def test_health_reports_fixture_mode(client: TestClient) -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["mode"] == "fixtures"
    assert set(body["sources_status"]) == {"A", "B", "C"}


def test_plan_is_valid_contract(client: TestClient) -> None:
    r = client.get("/api/plan", params={"scenario": "demo-vara"})
    assert r.status_code == 200
    Plan.model_validate(r.json())


def test_work_items_valid_and_filtered(client: TestClient) -> None:
    items = client.get("/api/work-items").json()
    assert len(items) == 7
    for it in items:
        WorkItem.model_validate(it)
    only_b = client.get("/api/work-items", params={"source": "B"}).json()
    assert only_b and all(w["source"] == "B" for w in only_b)


def test_work_item_detail_has_decision(client: TestClient) -> None:
    r = client.get("/api/work-items/A-20261109-MTR-004217")
    assert r.status_code == 200
    body = r.json()
    assert body["decision"]["decision"] == "assigned"
    assert client.get("/api/work-items/A-20261109-NU-EXISTA").status_code == 404


@pytest.mark.parametrize("wid", ["A-20261109-MTR-004217", "B-20261109-CT-MEDGIDIA", "C-20261109-PT-1432"])
def test_series_per_source(client: TestClient, wid: str) -> None:
    r = client.get(f"/api/series/{wid}")
    assert r.status_code == 200
    s = Series.model_validate(r.json())
    assert s.synthetic and "ilustrativ" in s.title_ro


def test_audit_and_filter(client: TestClient) -> None:
    records = client.get("/api/audit").json()
    assert len(records) >= 4  # câte o decizie pentru fiecare lucrare din exemple
    for rec in records:
        AuditRecord.model_validate(rec)
    one = client.get("/api/audit", params={"work_item_id": "A-20261109-MTR-004217"}).json()
    assert len(one) == 1


def test_bad_parameters_rejected(client: TestClient) -> None:
    assert client.get("/api/plan", params={"scenario": "../../etc"}).status_code == 422
    assert client.get("/api/series/..%2F..%2Fpasswd").status_code in (404, 422)
    assert client.get("/api/work-items/X-1-2").status_code == 422
    assert client.get("/api/work-orders/..%2Fx.pdf").status_code in (404, 422)


def test_cors_for_ui(client: TestClient) -> None:
    r = client.get("/api/health", headers={"Origin": "http://localhost:3710"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:3710"


def test_metrics_shape_without_reports(client: TestClient) -> None:
    body = client.get("/api/metrics").json()
    assert set(body) == {"A", "B", "C", "bilant", "planner"}


def test_scenarios_listed(client: TestClient) -> None:
    ids = [s["scenario_id"] for s in client.get("/api/scenarios").json()]
    assert {"demo-vara", "maine"} <= set(ids)


def test_quarantine_in_fixture_mode(client: TestClient) -> None:
    q = client.get("/api/quarantine").json()
    assert len(q) == 1 and q[0]["errors"]
