"""Extinderea din 7 nov.: fuziunea cu bilanțul, lucrările de bilanț pe post, scara de soluții C, lista după lei pe oră."""

from __future__ import annotations

import json
import sys
import types
from datetime import datetime
from pathlib import Path

import pytest

from cyberpunks.common.contracts import AuditRecord
from cyberpunks.planner import agent
from cyberpunks.planner.settings import TZ

from .conftest import DATE, SCENARIO, fixture_items, variant, write_items

EARLY = datetime(2026, 11, 2, 18, 0, tzinfo=TZ)  # întreruperea anunțată cu o săptămână înainte


def _decisions(res) -> dict:
    return {d.work_item_id: d for d in res.plan.decisions}


def _audit(out_root: Path) -> list[AuditRecord]:
    path = out_root / "plans" / SCENARIO / "audit.jsonl"
    return [AuditRecord.model_validate_json(x) for x in path.read_text(encoding="utf-8").splitlines()]


def _bilant_post(asset: str, action: str, score: float = 0.8, value: float = 2000.0, skill: str = "metering", **extra) -> dict:
    base = fixture_items("A")[1]
    it = variant(base, asset, **{"prediction.score": score, "impact.value_if_true_lei": value, "prediction.confidence": "high"})
    it["asset_type"] = "transformer_post"
    it["prediction"]["model_id"] = "bilant-lgbm"
    it["prediction"]["model_version"] = "bilant-lgbm@test"
    it["prediction"]["label"] = extra.pop("label", "pierdere_tehnica")
    it["recommended_action"] = action
    it["effort"] = {"duration_min": 90, "crew_skill": skill, "crew_size": 2, "requires_planned_outage": False}
    it["extra"] = {"post_excess_loss_lei_month": 640.0, **extra}
    return it


# ------------------------------------------------------------------ fuziunea


@pytest.fixture()
def fake_fuse(monkeypatch: pytest.MonkeyPatch):
    """Un modul cyberpunks.a_bilant.fuse de test: confirmă contorul MTR-019833 pe postul PT-1432."""
    calls = {}

    def fuse(items, scenario, date):
        calls["n"] = len(items)
        out = []
        for wi in items:
            if wi.asset_id == "MTR-019833":
                d = wi.model_dump(mode="json")
                a = d["prediction"]["score"]
                d["prediction"]["score"] = 0.93
                d["prediction"]["interval_low"], d["prediction"]["interval_high"] = 0.85, 0.97
                d["prediction"]["confidence"] = "high"
                d["impact"]["expected_value_lei"] = round(0.93 * d["impact"]["value_if_true_lei"], 2)
                d["extra"]["fusion"] = {"post_id": "PT-1432", "bilant_prediction_id": "b-123", "post_excess_loss_kwh_day": 18.5,
                                        "post_excess_loss_lei_month": 388.5, "a_score": a, "combined_score": 0.93,
                                        "note_ro": "Postul PT-1432 are lipsă peste normal din aceeași zi în care contorul a scăzut."}
                out.append(d)
            else:
                out.append(wi)
        return out

    pkg = types.ModuleType("cyberpunks.a_bilant")
    mod = types.ModuleType("cyberpunks.a_bilant.fuse")
    mod.fuse = fuse
    monkeypatch.setitem(sys.modules, "cyberpunks.a_bilant", pkg)
    monkeypatch.setitem(sys.modules, "cyberpunks.a_bilant.fuse", mod)
    return calls


def test_fusion_raises_score_and_is_logged(out_root: Path, fake_fuse) -> None:
    write_items(out_root, "A", fixture_items("A"))
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)
    d = _decisions(res)["A-20261109-MTR-019833"]
    assert d.reason_ro.startswith("Confirmat de bilanțul postului PT-1432")
    assert d.threshold["fusion_combined_score"] == 0.93 and d.decision.value == "assigned"
    fusion = [a for a in _audit(out_root) if a.rule_id == "R-FUSION-BILANT"]
    assert len(fusion) == 1 and fusion[0].threshold["a_score"] == 0.64 and fusion[0].inputs_sha256
    assert res.meta["fusion"]["status"] == "ok" and fake_fuse["n"] == 3


def test_fusion_failure_keeps_original_scores(out_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = types.ModuleType("cyberpunks.a_bilant.fuse")
    mod.fuse = lambda items, scenario, date: (_ for _ in ()).throw(RuntimeError("bilanț căzut"))
    monkeypatch.setitem(sys.modules, "cyberpunks.a_bilant", types.ModuleType("cyberpunks.a_bilant"))
    monkeypatch.setitem(sys.modules, "cyberpunks.a_bilant.fuse", mod)
    write_items(out_root, "A", fixture_items("A"))
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)
    assert res.meta["fusion"]["status"] == "eroare"
    assert any("Fuziunea" in a.title_ro for a in res.plan.alerts)
    assert "Confirmat" not in _decisions(res)["A-20261109-MTR-019833"].reason_ro


# ------------------------------------------------------------------ lucrările de bilanț pe post


def test_bilant_post_actions(out_root: Path) -> None:
    write_items(out_root, "A", fixture_items("A"))
    rows = [
        _bilant_post("PT-B001", "office_correction", label="post_gresit"),
        _bilant_post("PT-B002", "grid_inspection", skill="lv_grid"),
        _bilant_post("PT-B003", "remote_reading", label="contor_defect"),
        _bilant_post("PT-B004", "grid_inspection", skill="lv_grid", value=100.0),  # nu acoperă deplasarea
    ]
    write_items(out_root, "A_bilant", rows)
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)
    d = _decisions(res)
    assert d["A-20261109-PT-B001"].rule_id == "R-BILANT-OFFICE" and d["A-20261109-PT-B001"].decision.value == "remote_action"
    assert d["A-20261109-PT-B001"].threshold["cost_lei"] < 50  # corecție în birou, fără deplasare
    assert d["A-20261109-PT-B002"].rule_id == "R-BILANT-GRID" and d["A-20261109-PT-B002"].decision.value == "assigned"
    crew = d["A-20261109-PT-B002"].crew_id
    from cyberpunks.planner.settings import Settings

    assert "lv_grid" in next(c for c in Settings.load().crews if c.crew_id == crew).skills
    assert d["A-20261109-PT-B003"].rule_id == "R-BILANT-REMOTE"
    assert d["A-20261109-PT-B004"].rule_id == "R-BILANT-WATCH"
    assert res.plan.sources_status["A"] == "ok"  # A.jsonl și A_bilant.jsonl, ambele ok
    assert res.meta["sources"]["A_bilant"]["valid"] == 4
    # ordinea: întâi verificările de la distanță și corecțiile, apoi lista pe echipe
    kinds = [x.decision.value for x in res.plan.decisions]
    first_route = kinds.index("assigned")
    assert all(k == "remote_action" for k in kinds[:first_route])


def test_bilant_missing_module_does_not_degrade_a(out_root: Path) -> None:
    write_items(out_root, "A", fixture_items("A"))
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)
    assert res.plan.sources_status["A"] == "ok"
    assert not any("bilanț" in a.title_ro for a in res.plan.alerts)


def test_ranks_follow_lei_per_work_hour(out_root: Path) -> None:
    a = fixture_items("A")
    rows = [variant(a[1], f"MTR-6{i:05d}", **{"prediction.confidence": "high", "prediction.score": 0.9,
                                             "impact.value_if_true_lei": 600.0 + 300 * i, "location.lat": 44.40 + 0.01 * i}) for i in range(8)]
    write_items(out_root, "A", rows)
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)
    ranked = sorted((x for x in res.plan.decisions if x.rank is not None and "lei_per_work_hour" in x.threshold), key=lambda x: x.rank)
    values = [x.threshold["lei_per_work_hour"] for x in ranked]
    assert values == sorted(values, reverse=True) and len(values) >= 5


# ------------------------------------------------------------------ scara de soluții C


def _c_with_ladder(asset: str, options: list[dict], p90: float = 1.125, value: float = 3000.0) -> dict:
    c = fixture_items("C")[0]
    it = variant(c, asset, **{"impact.value_if_true_lei": value})
    it["prediction"]["point_estimate"] = round(p90 - 0.01, 3)
    it["prediction"]["point_interval"] = [round(p90 - 0.03, 3), p90]
    it["extra"] = {"remedy_options": options}
    return it


def _opt(action: str, cost: float, effect: float, base: float = 1.125, crew: bool = False, **kw) -> dict:
    o = {"action": action, "cost_lei": cost, "p90_after_pu": round(base + effect, 4), "effect_pu": effect, "confidence": "medium",
         "duration_min": 60 if crew else 0, "needs_crew": crew, "crew_skill": "lv_grid" if crew else None, "combinable": True,
         "note_ro": f"treapta {action} (test)"}
    o.update(kw)
    return o


LADDER = [
    _opt("notify_customers", 0.0, -0.005, participation_rate=0.2, message_preview_ro="Strada ta a evitat ieri 3 opriri ale panourilor. Mâine între 12 și 15, pornește mașina de spălat."),
    _opt("offer_battery", 20.0, -0.015, battery_kwh_total=30.0, revenue_lei=18000.0, payback_years=7.5, customers_targeted=3),
    _opt("export_limit", 50.0, -0.03),
    _opt("phase_rebalance", 300.0, -0.03, crew=True),
    _opt("transformer_upgrade", 80000.0, -0.08, crew=True, combinable=False),
]


def test_ladder_picks_cheapest_combination_and_explains(out_root: Path) -> None:
    it = _c_with_ladder("PT-L001", LADDER)
    write_items(out_root, "C", [it])
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)
    d = _decisions(res)[it["work_item_id"]]
    assert d.rule_id == "R-REMEDY-LADDER" and d.decision.value == "notify"
    assert d.threshold["remedy_cost_lei"] == 50.0 and d.threshold["p90_after_pu"] < 1.10  # limita de injecție, singură
    assert "1,120 pu" in d.reason_ro and "la 20% participare" in d.reason_ro  # de ce nu ajung mesajele singure
    assert "1,105 pu" in d.reason_ro  # mesajele + bateriile tot nu ajung
    remedies = json.loads((out_root / "plans" / SCENARIO / "remedies.json").read_text(encoding="utf-8"))
    assert remedies[0]["chosen"] == ["export_limit"] and not remedies[0]["invest"]


def test_ladder_targeted_message_and_battery_offer(out_root: Path) -> None:
    # mesajele singure: 1,110; bateriile singure: 1,105; împreună: 1,090 (sub limită), deci combinația de 20 lei
    opts = [dict(LADDER[0], effect_pu=-0.015, p90_after_pu=1.11), dict(LADDER[1], effect_pu=-0.02, p90_after_pu=1.105)]
    it = _c_with_ladder("PT-L002", opts)
    write_items(out_root, "C", [it])
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)
    d = _decisions(res)[it["work_item_id"]]
    assert d.decision.value == "notify" and d.threshold["remedy_steps"] == 2
    texts = [n.message_ro for n in res.plan.notifications if n.work_item_id == it["work_item_id"]]
    assert any(t.startswith("Strada ta a evitat") for t in texts)  # textul de grup din message_preview_ro
    assert all(n.demo_only and n.audience == "prosumatori" for n in res.plan.notifications if n.work_item_id == it["work_item_id"])
    report = (out_root / "plans" / SCENARIO / "report.md").read_text(encoding="utf-8")
    assert "Pentru PPC Energie: oferte de baterii" in report


def test_ladder_crew_step_needs_notice(out_root: Path, tmp_path: Path) -> None:
    opts = [_opt("notify_customers", 0.0, -0.005, participation_rate=0.2), _opt("phase_rebalance", 300.0, -0.03, crew=True)]
    it = _c_with_ladder("PT-L003", opts)
    write_items(out_root, "C", [it])
    d = _decisions(agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root))[it["work_item_id"]]
    assert d.decision.value == "notify" and "le programez pe" in d.reason_ro  # fără preaviz ANRE: programată mai târziu
    out2 = tmp_path / "o2"
    write_items(out2, "C", [it])
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out2, as_of=EARLY)
    d = _decisions(res)[it["work_item_id"]]
    assert d.decision.value == "assigned" and d.rule_id == "R-REMEDY-LADDER"
    stop = next(s for r in res.plan.routes for s in r.stops if s.work_item_id == it["work_item_id"])
    assert stop.duration_min == 60  # durata treptei alese, nu a lucrării inițiale


def test_ladder_investment_and_nothing_feasible(out_root: Path) -> None:
    only_upgrade = _c_with_ladder("PT-L004", [_opt("notify_customers", 0.0, -0.005, participation_rate=0.2),
                                              _opt("transformer_upgrade", 80000.0, -0.08, crew=True, combinable=False)])
    hopeless = _c_with_ladder("PT-L005", [_opt("notify_customers", 0.0, -0.005, participation_rate=0.2), _opt("export_limit", 50.0, -0.01)])
    write_items(out_root, "C", [only_upgrade, hopeless])
    d = _decisions(agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root))
    assert d[only_upgrade["work_item_id"]].decision.value == "deferred" and "investiții" in d[only_upgrade["work_item_id"]].reason_ro
    assert d[hopeless["work_item_id"]].decision.value == "human_review"
