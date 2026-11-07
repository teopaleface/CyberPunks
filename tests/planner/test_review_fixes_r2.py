"""Regresii pentru runda a doua de revizuire independentă (Codex, 7 nov., 14:15)."""

from __future__ import annotations

import json
import shutil
import sys
import types
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cyberpunks.api import app as app_mod
from cyberpunks.api.store import Store
from cyberpunks.common.contracts import WorkItem
from cyberpunks.planner import agent
from cyberpunks.planner.feedback import approvals, approve_route, record_verdict
from cyberpunks.planner.review import apply_review
from cyberpunks.planner.settings import TZ, Settings

from .conftest import DATE, SCENARIO, fixture_items, variant, write_items
from .test_extension import EARLY, _c_with_ladder, _opt

D = datetime(2026, 11, 9, tzinfo=TZ)


def _decisions(res) -> dict:
    return {d.work_item_id: d for d in res.plan.decisions}


def test_r2_1_work_order_follows_the_agent_action() -> None:
    from cyberpunks.planner import workorders

    c = WorkItem.model_validate(_c_with_ladder("PT-R201", []))
    workorders._ACTION.clear()
    workorders._ACTION[c.work_item_id] = "phase_rebalance"
    assert workorders._kind_label(c) == "Mutarea unor case pe altă fază"
    assert not any("priza" in s.lower() for s in workorders._steps(c))
    workorders._ACTION[c.work_item_id] = "measurement_campaign"
    assert "analizor" in workorders._steps(c)[0]
    workorders._ACTION.clear()


def test_r2_2_outage_notice_uses_the_crew_arrival(out_root: Path) -> None:
    opts = [_opt("notify_customers", 0.0, -0.005, participation_rate=0.2), _opt("phase_rebalance", 350.0, -0.03, crew=True)]
    it = _c_with_ladder("PT-R202", opts)
    write_items(out_root, "C", [it])
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root, as_of=EARLY)
    stop = next(s for r in res.plan.routes for s in r.stops if s.work_item_id == it["work_item_id"])
    eta = stop.eta.astimezone(TZ)
    start = eta.replace(minute=0 if eta.minute < 30 else 30)
    notice = next(n for n in res.plan.notifications if n.work_item_id == it["work_item_id"] and n.audience == "clienti_zona")
    assert f"între {start:%H:%M} și" in notice.message_ro


def test_r2_3_participation_scenarios_are_not_added(out_root: Path) -> None:
    opts = [_opt("notify_customers", 0.0, -0.005, participation_rate=0.1), _opt("notify_customers", 0.0, -0.010, participation_rate=0.2),
            _opt("notify_customers", 0.0, -0.015, participation_rate=0.3)]
    it = _c_with_ladder("PT-R203", opts)
    write_items(out_root, "C", [it])
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)
    d = _decisions(res)[it["work_item_id"]]
    assert d.decision.value == "human_review"  # niciun scenariu singur nu ajunge sub 1,10, iar scenariile nu se adună
    assert d.threshold["p90_after_pu"] == 1.115 and d.threshold.get("participation_rate") == 0.2  # scenariul central


def test_r2_4_approval_goes_stale_when_the_action_changes(out_root: Path) -> None:
    a = fixture_items("A")
    rows = [variant(a[1], f"MTR-72{i:04d}", **{"prediction.confidence": "high", "prediction.score": 0.9}) for i in range(2)]
    write_items(out_root, "A", rows)
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)
    crew = res.plan.routes[0].crew_id
    approve_route(SCENARIO, crew, "Ana", out_root=out_root)
    actions_path = out_root / "plans" / SCENARIO / "actions.json"
    actions = json.loads(actions_path.read_text(encoding="utf-8"))
    actions[res.plan.routes[0].stops[0].work_item_id] = "grid_inspection"
    actions_path.write_text(json.dumps(actions), encoding="utf-8")
    assert approvals(SCENARIO, out_root=out_root)[0]["stale"] is True


def test_r2_5_and_6_bad_times_and_infinite_values_are_quarantined(out_root: Path) -> None:
    a = fixture_items("A")
    mixed = variant(a[1], "MTR-720005")
    mixed["time_window"] = {"start": "2026-11-09T13:00:00+02:00", "end": "2026-11-09T14:00:00"}
    inf = variant(a[1], "MTR-720006")
    line = json.dumps(inf).replace(f'"expected_value_lei": {inf["impact"]["expected_value_lei"]}', '"expected_value_lei": 1e309')
    line = line.replace(f'"value_if_true_lei": {inf["impact"]["value_if_true_lei"]}', '"value_if_true_lei": 1e309')
    assert "1e309" in line
    write_items(out_root, "A", [a[0], mixed, line])
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)
    d = _decisions(res)
    assert d[mixed["work_item_id"]].decision.value == "rejected_invalid"
    assert d[inf["work_item_id"]].decision.value == "rejected_invalid" and "finite" in d[inf["work_item_id"]].reason_ro


def test_r2_7_replan_replays_the_saved_fusion(out_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state = {"score": 0.93}

    def fuse(items, scenario, date):
        out = []
        for wi in items:
            d = wi.model_dump(mode="json")
            if wi.asset_id == "MTR-019833":
                a = d["prediction"]["score"]
                s = state["score"]
                d["prediction"].update(score=s, interval_low=max(0.0, s - 0.05), interval_high=min(1.0, s + 0.03), confidence="high")
                d["impact"]["expected_value_lei"] = round(s * d["impact"]["value_if_true_lei"], 2)
                d["extra"]["fusion"] = {"post_id": "PT-1432", "bilant_prediction_id": "b-1", "post_excess_loss_kwh_day": 10.0,
                                        "post_excess_loss_lei_month": 210.0, "a_score": a, "combined_score": s, "note_ro": "test"}
            out.append(d)
        return out

    mod = types.ModuleType("cyberpunks.a_bilant.fuse")
    mod.fuse = fuse
    monkeypatch.setitem(sys.modules, "cyberpunks.a_bilant", types.ModuleType("cyberpunks.a_bilant"))
    monkeypatch.setitem(sys.modules, "cyberpunks.a_bilant.fuse", mod)
    write_items(out_root, "A", fixture_items("A"))
    first = _decisions(agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root))["A-20261109-MTR-019833"]
    state["score"] = 0.10  # modulul de fuziune s-a schimbat între timp
    apply_review(SCENARIO, "A-20261109-MTR-027710", "defer", None, "Ana", out_root=out_root)
    plan = json.loads((out_root / "plans" / SCENARIO / "plan.json").read_text(encoding="utf-8"))
    again = next(x for x in plan["decisions"] if x["work_item_id"] == "A-20261109-MTR-019833")
    assert again["decision"] == first.decision.value and again["threshold"]["fusion_combined_score"] == 0.93


def test_r2_8_quarantine_ids_unique_across_a_files(out_root: Path) -> None:
    a = fixture_items("A")
    good = variant(a[1], "MTR-SAME")
    bad = json.loads(json.dumps(good))
    bad["prediction"]["score"] = 1.7
    write_items(out_root, "A", [bad, good])
    write_items(out_root, "A_bilant", [bad])
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)
    ids = [x.work_item_id for x in res.plan.decisions]
    assert len(ids) == len(set(ids)) == 3


def test_r2_9_baselines_respect_meter_access_windows() -> None:
    from cyberpunks.planner.evaluate import run_baseline
    from cyberpunks.planner.simulate import SimDay

    a = fixture_items("A")[1]
    it = variant(a, "MTR-720009")
    it["time_window"] = {"start": (D + timedelta(hours=3)).isoformat(), "end": (D + timedelta(hours=4)).isoformat()}
    res = run_baseline(SimDay(D.date(), [it], {it["work_item_id"]: True}), Settings.load(), "top_k_scor", 1)
    assert res.visits == 0


def test_r2_10_posts_survive_malformed_fusion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out = tmp_path / "out"
    a = fixture_items("A")
    write_items(out, "A", [variant(a[1], "MTR-720010", extra={"fusion": ["bad"], "post_id": ["x"]})])
    agent.run(SCENARIO, date=DATE, mode="existing", out_root=out)
    monkeypatch.setattr(app_mod, "store", Store(outputs=out, demo=tmp_path / "demo", reports=tmp_path / "rep"))
    assert TestClient(app_mod.app).get("/api/posts", params={"scenario": SCENARIO}).status_code == 200


def test_r2_11_approvals_and_labels_from_the_demo_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from cyberpunks.planner.snapshot import snapshot

    out = tmp_path / "out"
    write_items(out, "A", fixture_items("A"))
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out)
    crew = res.plan.routes[0].crew_id
    approve_route(SCENARIO, crew, "Ana", out_root=out)
    record_verdict(SCENARIO, res.plan.routes[0].stops[0].work_item_id, "confirmed", "echipa", out_root=out)
    demo = tmp_path / "demo"
    snapshot(SCENARIO, src=out, dest=demo, reports=tmp_path / "rep")
    shutil.rmtree(out / "plans")
    monkeypatch.setattr(app_mod, "store", Store(outputs=out, demo=demo, reports=tmp_path / "rep"))
    client = TestClient(app_mod.app)
    assert client.get("/api/health", params={"scenario": SCENARIO}).json()["mode"] == "demo"
    assert len(client.get("/api/approvals", params={"scenario": SCENARIO}).json()) == 1
    assert len(client.get("/api/labels", params={"scenario": SCENARIO}).json()) == 1
