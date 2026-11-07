"""Coada „nu sunt sigur”: mică și cu cazuri care cer un om (cererea orchestratorului de la 14:20)."""

from __future__ import annotations

from pathlib import Path

from cyberpunks.planner import agent
from cyberpunks.planner.settings import Settings

from .conftest import DATE, SCENARIO, fixture_items, variant, write_items
from .test_extension import _c_with_ladder, _opt


def _decisions(res) -> dict:
    return {d.work_item_id: d for d in res.plan.decisions}


def _abstain(base: dict, asset: str, value: float, **extra) -> dict:
    it = variant(base, asset, **{"impact.value_if_true_lei": value})
    it["prediction"].update(abstain=True, abstain_reason="nu sunt sigur: test", confidence="low")
    it["recommended_action"] = "human_review"
    it["extra"] = {**it.get("extra", {}), **extra}
    return it


def test_abstain_routes_by_cause_and_value(out_root: Path) -> None:
    a = fixture_items("A")[1]
    data = _abstain(a, "MTR-Q001", 2000.0, selection="data")
    small = _abstain(a, "MTR-Q002", 100.0)  # EV 64 lei
    big = _abstain(a, "MTR-Q003", 2000.0)
    write_items(out_root, "A", [data, small, big])
    d = _decisions(agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root))
    assert d[data["work_item_id"]].rule_id == "R-ABSTAIN-DATA" and d[data["work_item_id"]].decision.value == "remote_action"
    assert d[small["work_item_id"]].rule_id == "R-ABSTAIN-WATCH" and d[small["work_item_id"]].decision.value == "deferred"
    assert d[big["work_item_id"]].rule_id == "R-ABSTAIN" and d[big["work_item_id"]].decision.value == "human_review"
    assert "Nu sunt sigur" not in d[big["work_item_id"]].reason_ro.replace("Modelul nu e sigur", "")


def test_human_queue_is_capped_by_value(out_root: Path) -> None:
    cap = int(Settings.load().rule("global", "human_review_max_per_day"))
    a = fixture_items("A")[1]
    rows = [_abstain(a, f"MTR-Q1{i:03d}", 1000.0 + 10 * i) for i in range(cap + 6)]
    write_items(out_root, "A", rows)
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)
    d = _decisions(res)
    human = [x for x in d.values() if x.decision.value == "human_review"]
    full = [x for x in d.values() if x.rule_id == "R-HUMAN-QUEUE-FULL"]
    assert len(human) == cap and len(full) == 6
    kept_min = min(float(x.threshold["expected_value_lei"]) for x in human)
    assert all(float(x.threshold["expected_value_lei"]) <= kept_min for x in full)  # rămân cele cu valoarea cea mai mare


def test_weak_safety_signal_is_not_mandatory(out_root: Path) -> None:
    a = fixture_items("A")[0]  # tamper, safety_flag
    weak = variant(a, "MTR-Q201", **{"prediction.score": 0.55, "prediction.confidence": "medium"})
    strong = variant(a, "MTR-Q202", **{"prediction.score": 0.9, "prediction.confidence": "high"})
    write_items(out_root, "A", [weak, strong])
    d = _decisions(agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root))
    assert d[strong["work_item_id"]].rule_id == "R-SAFETY"
    assert d[weak["work_item_id"]].rule_id != "R-SAFETY"


def test_ladder_starts_from_phase_adjusted_p90(out_root: Path) -> None:
    opts = [_opt("phase_rebalance", 350.0, -0.018, base=1.1756, crew=True), _opt("export_limit", 150.0, -0.05, base=1.1756)]
    it = _c_with_ladder("PT-Q301", opts, p90=1.1556)
    it["extra"]["ladder_base_p90_pu"] = 1.1756
    write_items(out_root, "C", [it])
    d = _decisions(agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root))[it["work_item_id"]]
    assert d.threshold["p90_before_pu"] == 1.1756
    # de la 1,1756, fazele și limita împreună ajung doar la 1,1076: nicio combinație nu ajunge, decide un om.
    # De la P90-ul modelului (1,1556) ar fi părut rezolvabil (1,0876), exact greșeala pe care o evită ladder_base_p90_pu.
    assert d.decision.value == "human_review" and d.threshold["p90_after_pu"] == 1.1076


def test_storm_below_model_threshold_is_not_prepositioned(out_root: Path) -> None:
    b = fixture_items("B")[0]
    calm = variant(b, "CT-LINISTIT", **{"prediction.score": 0.05, "impact.value_if_true_lei": 200000.0, "extra": {"decision_threshold": 0.16}})
    write_items(out_root, "B", [calm])
    d = _decisions(agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root))[calm["work_item_id"]]
    assert d.rule_id == "R-B-BELOW-THRESHOLD" and d.decision.value == "deferred"
    assert d.threshold["preposition_min_score"] == 0.16  # pragul modelului B, mai mare decât cel din config


def test_mandatory_safety_has_a_daily_quota(out_root: Path) -> None:
    cap = int(Settings.load().rule("global", "safety_max_mandatory_per_day"))
    a = fixture_items("A")[0]  # tamper cu safety_flag
    rows = [variant(a, f"MTR-S{i:03d}", **{"prediction.score": 0.9 + i / 1000, "prediction.confidence": "high",
                                          "location.lat": 44.40 + 0.003 * i}) for i in range(cap + 5)]
    write_items(out_root, "A", rows)
    d = _decisions(agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root))
    over = [x for x in d.values() if x.rule_id == "R-SAFETY-OVER-CAP"]
    assert len(over) == 5  # cele cu scorul cel mai mic peste cotă
    kept = [x for x in d.values() if x.rule_id in ("R-SAFETY", "R-SAFETY-NO-CREW")]
    assert len(kept) == cap
