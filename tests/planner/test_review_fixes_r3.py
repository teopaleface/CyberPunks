"""Regresii pentru runda a treia de revizuire independentă (Codex, 7 nov., 14:50)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from cyberpunks.common.contracts import WorkItem
from cyberpunks.planner import agent
from cyberpunks.planner.settings import TZ, Settings

from .conftest import DATE, SCENARIO, confirmed_by_bilant, fixture_items, variant, write_items
from .test_extension import EARLY, _c_with_ladder, _opt

D = datetime(2026, 11, 9, tzinfo=TZ)


def test_r3_1_combined_remedy_keeps_every_crew_step(out_root: Path) -> None:
    from cyberpunks.planner import workorders

    opts = [_opt("phase_rebalance", 350.0, -0.015, crew=True), dict(_opt("adjust_tap", 450.0, -0.015, crew=True), crew_skill="mv_grid")]
    it = _c_with_ladder("PT-R301", opts)
    write_items(out_root, "C", [it])
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root, as_of=EARLY)
    actions = json.loads((out_root / "plans" / SCENARIO / "actions.json").read_text(encoding="utf-8"))
    assert set(actions[it["work_item_id"]].split("+")) == {"phase_rebalance", "adjust_tap"}
    wi = WorkItem.model_validate(it)
    steps = " ".join(workorders._steps(wi, actions)).lower()
    assert "branșament" in steps and "priza" in steps  # ambele trepte au instrucțiuni (fazele și priza)
    assert "+" in workorders._kind_label(wi, actions)
    assert res.plan.summary.assigned == 1


def test_r3_2_no_remote_reading_without_smart_meter(out_root: Path) -> None:
    a = fixture_items("A")[0]  # siguranță
    dumb = confirmed_by_bilant(variant(a, "MTR-R302", **{"effort.duration_min": 720, "extra": {"smart_meter": False}}))
    write_items(out_root, "A", [dumb])
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)
    d = {x.work_item_id: x for x in res.plan.decisions}[dumb["work_item_id"]]
    assert d.rule_id == "R-SAFETY-NO-CREW" and d.decision.value == "deferred"


def test_r3_3_corrupt_cached_output_does_not_crash_estimate(out_root: Path) -> None:
    path = out_root / "work_items" / SCENARIO / "A_bilant.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xff\xfe\x00garbage")
    write_items(out_root, "A", fixture_items("A"))
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)
    assert res.plan.sources_status["A"] in ("ok", "degraded")


def test_r3_4_safety_ablation_uses_the_same_settings(tmp_path: Path) -> None:
    from cyberpunks.planner.evaluate import evaluate_demo_day

    root = tmp_path / "outputs"
    a = fixture_items("A")
    write_items(root, "A", a, scenario="demo-vara")
    truth = root / "work_items" / "demo-vara" / "A_ground_truth.csv"
    truth.write_text("meter_id,true_problem,true_value_lei\n" + "".join(f"{w['asset_id']},1,1000\n" for w in a), encoding="utf-8")
    s = Settings.load()
    s.crews = []  # fără echipe: nimeni nu poate vizita nimic
    r = evaluate_demo_day("demo-vara", out_root=root, settings=s)
    assert all(v["visits_total"] == 0 for v in r["strategies"].values())


def test_r3_5_empty_demo_output_is_skipped(tmp_path: Path) -> None:
    from cyberpunks.planner.evaluate import evaluate_demo_day

    root = tmp_path / "outputs"
    (root / "work_items" / "demo-vara").mkdir(parents=True)
    (root / "work_items" / "demo-vara" / "A.jsonl").write_text("", encoding="utf-8")
    (root / "work_items" / "demo-vara" / "A_ground_truth.csv").write_text("meter_id,true_problem,true_value_lei\n", encoding="utf-8")
    assert evaluate_demo_day("demo-vara", out_root=root) is None


def test_r3_6_chart_shows_negative_values(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import matplotlib.figure

    from cyberpunks.planner.evaluate import STRATEGIES, render_chart

    seen = {}

    def fake_save(fig, path, **kw):
        seen["xlim"] = fig.axes[0].get_xlim()

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", fake_save)
    values = [100.0, -200.0, -300.0, -400.0, -500.0]
    strategies = {n: {"net_value_lei_per_day": v, "urgent_missed_rate": 0.1} for n, v in zip(STRATEGIES, values, strict=True)}
    report = {"main": {"strategies": strategies, "days": 1}, "reproduce_cmd": "test"}
    render_chart(report, tmp_path / "x.png")
    assert seen["xlim"][0] < -500 and seen["xlim"][1] > 100
