"""Regresii pentru problemele găsite la revizuirea independentă (Codex, 7 nov., 14:00)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cyberpunks.api import app as app_mod
from cyberpunks.api.store import Store
from cyberpunks.planner import agent
from cyberpunks.planner.feedback import approvals, approve_route
from cyberpunks.planner.review import apply_review
from cyberpunks.planner.settings import TZ, Settings

from .conftest import DATE, SCENARIO, fixture_items, variant, write_items
from .test_extension import EARLY, _bilant_post, _c_with_ladder, _opt

D = datetime(2026, 11, 9, tzinfo=TZ)


def _decisions(res) -> dict:
    return {d.work_item_id: d for d in res.plan.decisions}


def _stop(res, wid):
    return next((s, r) for r in res.plan.routes for s in r.stops if s.work_item_id == wid)


def test_1_meter_access_window_is_respected(out_root: Path) -> None:
    a = fixture_items("A")[1]
    it = variant(a, "MTR-700001", **{"prediction.confidence": "high", "prediction.score": 0.9})
    it["time_window"] = {"start": (D + timedelta(hours=13)).isoformat(), "end": (D + timedelta(hours=14)).isoformat()}
    write_items(out_root, "A", [it])
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)
    stop, _ = _stop(res, it["work_item_id"])
    assert D + timedelta(hours=13) <= stop.eta <= D + timedelta(hours=13, minutes=20)  # 14:00 minus 40 de minute de lucru


def test_2_combined_remedy_needs_all_skills(out_root: Path) -> None:
    # Regula tipurilor de echipe (8 nov.): o treaptă JT și una MT nu le face aceeași echipă; combinația nu intră în traseu.
    opts = [_opt("phase_rebalance", 350.0, -0.015, crew=True), dict(_opt("adjust_tap", 450.0, -0.015, crew=True), crew_skill="mv_grid")]
    it = _c_with_ladder("PT-L010", opts)  # 1,125: fiecare singură ajunge la 1,110; împreună 1,095
    write_items(out_root, "C", [it])
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root, as_of=EARLY)
    d = _decisions(res)[it["work_item_id"]]
    assert d.decision.value != "assigned" and d.crew_id is None
    assert "două tipuri de echipe" in d.reason_ro
    assert all(not ({"lv_grid", "mv_grid"} <= c.skills) for c in Settings.load().crews)


def test_3_greedy_never_puts_a_storm_crew_after_the_shift(out_root: Path) -> None:
    b = fixture_items("B")[0]
    far = variant(b, "TL-DEPARTE", **{"location.lat": 45.17, "location.lon": 28.79, "location.county": "Tulcea",
                                      "extra": {"storm_onset": (D + timedelta(hours=20)).isoformat()}})
    write_items(out_root, "B", [far])
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root, solver="greedy")
    for r in res.plan.routes:
        assert r.stops[-1].eta <= D + timedelta(hours=15, minutes=30)


def test_4_malformed_prediction_is_quarantined_not_fatal(out_root: Path) -> None:
    a = fixture_items("A")
    bad = dict(variant(a[1], "MTR-700004"), prediction=["invalid"])
    write_items(out_root, "A", [a[0], bad])
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)
    assert _decisions(res)[bad["work_item_id"]].decision.value == "rejected_invalid"


def test_6_early_plan_announces_the_outage(out_root: Path) -> None:
    c = fixture_items("C")[0]
    it = variant(c, "PT-9101", **{"impact.value_if_true_lei": 5000.0})
    write_items(out_root, "C", [it])
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root, as_of=EARLY)
    d = _decisions(res)[it["work_item_id"]]
    assert d.rule_id == "R-C-TAP" and "Anunț întreruperea azi" in d.reason_ro
    assert any(n.audience == "clienti_zona" and n.work_item_id == it["work_item_id"] for n in res.plan.notifications)


def test_7_series_ref_cannot_leave_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out = tmp_path / "out"
    secret = tmp_path / "secret.json"
    secret.write_text(json.dumps({"parola": "x"}), encoding="utf-8")
    a = fixture_items("A")
    it = variant(a[0], "MTR-700007", extra={"series_ref": str(secret)})
    rel = variant(a[1], "MTR-700008", extra={"series_ref": "../../secret.json"})
    write_items(out, "A", [it, rel])
    agent.run(SCENARIO, date=DATE, mode="existing", out_root=out)
    monkeypatch.setattr(app_mod, "store", Store(outputs=out, demo=tmp_path / "demo", reports=tmp_path / "rep"))
    client = TestClient(app_mod.app)
    assert client.get(f"/api/series/{it['work_item_id']}", params={"scenario": SCENARIO}).status_code == 404
    assert client.get(f"/api/series/{rel['work_item_id']}", params={"scenario": SCENARIO}).status_code == 404


def test_8_approval_keeps_the_proposed_action(out_root: Path) -> None:
    grid = _bilant_post("PT-B701", "human_review", skill="lv_grid")  # agentul trimite la om
    office = _bilant_post("PT-B702", "office_correction", label="post_gresit")
    write_items(out_root, "A_bilant", [grid, office])
    agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)
    apply_review(SCENARIO, grid["work_item_id"], "approve", None, "Ana", out_root=out_root)
    apply_review(SCENARIO, office["work_item_id"], "approve", None, "Ana", out_root=out_root)
    plan = json.loads((out_root / "plans" / SCENARIO / "plan.json").read_text(encoding="utf-8"))
    d = {x["work_item_id"]: x for x in plan["decisions"]}
    assert d[grid["work_item_id"]]["rule_id"] == "R-HUMAN-APPROVE" and d[grid["work_item_id"]]["decision"] == "assigned"
    crew = next(c for c in Settings.load().crews if c.crew_id == d[grid["work_item_id"]]["crew_id"])
    assert "lv_grid" in crew.skills  # inspecția de rețea, nu o vizită la contor
    assert d[office["work_item_id"]]["decision"] == "remote_action"  # corecția din birou rămâne fără deplasare


def test_9_invalid_then_valid_same_id_gets_one_decision_each(out_root: Path) -> None:
    a = fixture_items("A")
    good = variant(a[1], "MTR-700009")
    bad = json.loads(json.dumps(good))
    bad["prediction"]["score"] = 1.7
    write_items(out_root, "A", [bad, good])
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)
    ids = [x.work_item_id for x in res.plan.decisions]
    assert len(ids) == len(set(ids)) == 2
    assert _decisions(res)[good["work_item_id"]].decision.value != "rejected_invalid"
    assert f"{good['work_item_id']}~A-linia1" in ids


def test_10_unreachable_storms_do_not_use_the_region_cap(out_root: Path) -> None:
    b = fixture_items("B")[0]
    early = [variant(b, f"CT-ZORI{i}", **{"impact.value_if_true_lei": 90000.0 + i, "location.lon": 28.2 + 0.05 * i,
                                          "extra": {"storm_onset": (D + timedelta(hours=8)).isoformat()}}) for i in range(3)]
    late = variant(b, "CT-DUPAMASA", **{"impact.value_if_true_lei": 30000.0, "extra": {"storm_onset": (D + timedelta(hours=15)).isoformat()}})
    write_items(out_root, "B", [*early, late])
    d = _decisions(agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root))
    assert all(d[x["work_item_id"]].rule_id == "R-B-TOO-LATE" for x in early)
    assert d[late["work_item_id"]].decision.value == "assigned"


def test_11_route_approval_goes_stale_when_the_route_changes(out_root: Path) -> None:
    a = fixture_items("A")
    rows = [variant(a[1], f"MTR-71{i:04d}", **{"prediction.confidence": "high", "prediction.score": 0.9, "location.lat": 44.42 + 0.004 * i})
            for i in range(3)]
    write_items(out_root, "A", rows)
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)
    route = next(r for r in res.plan.routes if len(r.stops) >= 2)
    approve_route(SCENARIO, route.crew_id, "Ana", out_root=out_root)
    assert approvals(SCENARIO, out_root=out_root)[0]["stale"] is False
    apply_review(SCENARIO, route.stops[0].work_item_id, "reject", "client plecat", "Ana", out_root=out_root)
    assert approvals(SCENARIO, out_root=out_root)[0]["stale"] is True


def test_12_baselines_use_the_same_storm_deadline() -> None:
    from cyberpunks.planner.evaluate import run_baseline
    from cyberpunks.planner.simulate import SimDay

    b = fixture_items("B")[0]
    it = variant(b, "CT-ACEEASI", extra={"storm_onset": (D + timedelta(hours=15)).isoformat()})
    it["time_window"] = {"start": (D + timedelta(hours=8)).isoformat(), "end": (D + timedelta(hours=20)).isoformat()}
    day = SimDay(D.date(), [it], {it["work_item_id"]: True})
    res = run_baseline(day, Settings.load(), "top_k_scor", 1)
    assert res.storms_covered == 1


def test_notice_skips_legal_holidays() -> None:
    from datetime import date

    from cyberpunks.planner.decide import earliest_outage_date, working_days_between

    # 30 noiembrie (Sf. Andrei) și 1 decembrie (Ziua națională) sunt libere: anunțat vineri 27.11.2026,
    # zilele lucrătoare pline sunt 2 și 3 decembrie, deci întreruperea poate fi cel mai devreme pe 4 decembrie
    assert working_days_between(date(2026, 11, 27), date(2026, 12, 3)) == 1
    assert earliest_outage_date(date(2026, 11, 27), 2) == date(2026, 12, 4)
