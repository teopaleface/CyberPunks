"""Agentul cap-coadă: contracte, carantină, surse lipsă, rezerva solverului, reguli, om în buclă, determinism."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from cyberpunks.common.contracts import AuditRecord, Plan, WorkItem
from cyberpunks.planner import agent, routing
from cyberpunks.planner.review import apply_review
from cyberpunks.planner.settings import TZ

from .conftest import DATE, SCENARIO, fixture_items, variant, write_items


def _decisions(res) -> dict[str, object]:
    return {d.work_item_id: d for d in res.plan.decisions}


def _audit(plan_dir: Path) -> list[AuditRecord]:
    return [AuditRecord.model_validate_json(line) for line in (plan_dir / "audit.jsonl").read_text(encoding="utf-8").splitlines()]


def test_fixtures_end_to_end_contracts(out_root: Path) -> None:
    res = agent.run("demo-vara", mode="fixtures", out_root=out_root)
    plan_dir = out_root / "plans" / "demo-vara"
    Plan.model_validate_json((plan_dir / "plan.json").read_text(encoding="utf-8"))
    audit = _audit(plan_dir)
    items = [WorkItem.model_validate_json(x) for x in (plan_dir / "work_items.jsonl").read_text(encoding="utf-8").splitlines()]
    # fiecare lucrare are exact o decizie, iar fiecare decizie duce la predicția ei prin jurnal
    ids = [d.work_item_id for d in res.plan.decisions]
    assert sorted(ids) == sorted(it.work_item_id for it in items)
    by_audit = {a.audit_id: a for a in audit}
    for d in res.plan.decisions:
        rec = by_audit[d.audit_id]
        assert rec.rule_id == d.rule_id and rec.inputs_sha256 and rec.prediction_id
    assert set(res.timings) >= {"perceive", "estimate", "decide", "act"}
    for name in ("report.md", "alerts.json", "notifications.json", "run.json", "quarantine.jsonl"):
        assert (plan_dir / name).exists(), name
    assert all(n.demo_only for n in res.plan.notifications)


def test_rules_on_fixtures(out_root: Path) -> None:
    d = _decisions(agent.run("demo-vara", mode="fixtures", out_root=out_root))
    assert d["A-20261109-MTR-027710"].decision.value == "human_review"  # abstain → om
    assert d["A-20261109-MTR-027710"].rule_id == "R-ABSTAIN"
    # semnal de manipulare 0,87 fără bilanț pentru post: sub pragul de 0,95 pentru regimul de siguranță fără confirmare
    assert d["A-20261109-MTR-004217"].rule_id != "R-SAFETY" and "fără regim de siguranță" in d["A-20261109-MTR-004217"].reason_ro
    # încredere medie, dar valoarea netă (~650 lei) trece de marja de siguranță (25% din costul vizitei): echipă
    assert d["A-20261109-MTR-019833"].rule_id == "R-A-VISIT-MEDIUM" and d["A-20261109-MTR-019833"].decision.value == "assigned"
    # pe valorile din fixture, priza (450 lei + întreruperea pentru 38 de clienți) costă mai mult decât valoarea așteptată
    assert d["C-20261109-PT-1432"].rule_id == "R-C-NOTIFY" and d["C-20261109-PT-1432"].threshold["net_tap_value_lei"] < 0
    for dec in d.values():
        assert dec.reason_ro and dec.rule_id


def test_bad_inputs_are_quarantined_and_plan_continues(out_root: Path) -> None:
    a = fixture_items("A")
    good = variant(a[1], "MTR-100001")
    rows = [
        good,
        "{nu e json",
        variant(a[1], "MTR-100002", **{"prediction.score": 1.4}),  # probabilitate imposibilă
        variant(a[1], "MTR-100003", **{"location.lat": 51.5}),  # în afara României
        variant(a[1], "MTR-100004", **{"location.lat": 47.9, "location.lon": 26.9}),  # România, dar nu zona Rețele Electrice
        variant(a[1], "MTR-100005", **{"impact.expected_value_lei": 99999.0}),  # incoerent cu scorul
        good,  # ID duplicat
        {**variant(a[1], "MTR-100006"), "source": "C"},  # sursă greșită în fișierul A
    ]
    write_items(out_root, "A", rows)
    write_items(out_root, "C", fixture_items("C"))
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)
    d = _decisions(res)
    invalid = [x for x in res.plan.decisions if x.decision.value == "rejected_invalid"]
    assert len(invalid) == 7
    assert all(x.rule_id == "R-QUARANTINE" and x.reason_ro.startswith("Intrare greșită") for x in invalid)
    assert d[good["work_item_id"]].decision.value != "rejected_invalid"
    q = [json.loads(x) for x in (out_root / "plans" / SCENARIO / "quarantine.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(q) == 7 and all(row["errors"] for row in q)
    assert res.plan.sources_status["A"] == "degraded"  # peste 20% linii respinse


def test_missing_source_plan_continues(out_root: Path) -> None:
    write_items(out_root, "A", fixture_items("A"))
    write_items(out_root, "C", fixture_items("C"))
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)
    assert res.plan.sources_status == {"A": "ok", "B": "missing", "C": "ok"}
    assert any("Sursa B" in a.title_ro and "lipsește" in a.title_ro for a in res.plan.alerts)
    assert res.plan.summary.assigned >= 1


def test_wrong_date_items_rejected(out_root: Path) -> None:
    write_items(out_root, "A", fixture_items("A"))
    res = agent.run(SCENARIO, date="2026-11-10", mode="existing", out_root=out_root)
    assert all(x.decision.value == "rejected_invalid" for x in res.plan.decisions)
    assert "planul e pentru 2026-11-10" in res.plan.decisions[0].reason_ro


def test_solver_failure_falls_back_to_greedy(out_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(routing, "solve_ortools", lambda *a, **k: None)  # solverul nu termină la timp
    res = agent.run("demo-vara", mode="fixtures", out_root=out_root)
    assert res.meta["solver"]["name"] == "greedy" and res.meta["solver"]["status"].startswith("FALLBACK")
    assert any("rezervă" in a.title_ro for a in res.plan.alerts)
    assert res.plan.summary.assigned >= 1


def test_greedy_and_ortools_respect_windows_and_skills(out_root: Path) -> None:
    for solver in ("ortools", "greedy"):
        res = agent.run("demo-vara", mode="fixtures", out_root=out_root, solver=solver)
        items = {it["work_item_id"]: it for s in "ABC" for it in fixture_items(s)}
        from cyberpunks.planner.settings import Settings

        crews = {c.crew_id: c for c in Settings.load().crews}
        for r in res.plan.routes:
            for st in r.stops:
                it = items[st.work_item_id]
                assert it["effort"]["crew_skill"] in crews[r.crew_id].skills, solver
                assert crews[r.crew_id].size >= it["effort"]["crew_size"], solver
                if it["source"] == "B":  # echipa ajunge cu o oră înainte de furtună
                    assert st.eta <= datetime.fromisoformat(it["time_window"]["start"]).astimezone(TZ).replace(tzinfo=TZ) - __import__("datetime").timedelta(minutes=60)


def test_low_confidence_goes_to_human_or_watch(out_root: Path) -> None:
    a = fixture_items("A")
    rich = variant(a[1], "MTR-200001", **{"prediction.confidence": "low", "prediction.score": 0.6})
    poor = variant(a[1], "MTR-200002", **{"prediction.confidence": "low", "prediction.score": 0.05})
    wide = variant(a[1], "MTR-200003", **{"prediction.interval_low": 0.1, "prediction.interval_high": 0.95})
    write_items(out_root, "A", [rich, poor, wide])
    d = _decisions(agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root))
    assert d[rich["work_item_id"]].decision.value == "human_review"
    assert d[poor["work_item_id"]].decision.value == "deferred"  # prea puțină valoare pentru timpul unui om
    assert d[wide["work_item_id"]].rule_id == "R-WIDE-INTERVAL"


def test_high_confidence_meter_visit_when_worth_it(out_root: Path) -> None:
    a = fixture_items("A")
    hi = variant(a[1], "MTR-300001", **{"prediction.confidence": "high", "prediction.score": 0.9})
    cheap = variant(a[1], "MTR-300002", **{"prediction.confidence": "high", "prediction.score": 0.12})
    write_items(out_root, "A", [hi, cheap])
    d = _decisions(agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root))
    assert d[hi["work_item_id"]].rule_id == "R-A-VISIT" and d[hi["work_item_id"]].decision.value == "assigned"
    assert d[cheap["work_item_id"]].decision.value in ("deferred", "remote_action")  # sub pragul de rentabilitate
    th = d[hi["work_item_id"]].threshold
    assert th["net_value_lei"] > th["min_net_value_lei"] and "breakeven_score" in th


def test_medium_confidence_small_value_goes_remote(out_root: Path) -> None:
    a = fixture_items("A")
    small = variant(a[1], "MTR-500001", **{"impact.value_if_true_lei": 450.0})  # EV 288 lei, sub costul vizitei + marja
    dumb = variant(a[1], "MTR-500002", **{"impact.value_if_true_lei": 450.0, "extra": {"smart_meter": False}})
    write_items(out_root, "A", [small, dumb])
    d = _decisions(agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root))
    assert d[small["work_item_id"]].rule_id == "R-A-REMOTE-FIRST" and d[small["work_item_id"]].decision.value == "remote_action"
    assert d[dumb["work_item_id"]].decision.value != "remote_action"  # contor care nu se citește de la distanță


def test_capacity_overflow_falls_back_to_remote_reading(out_root: Path) -> None:
    a = fixture_items("A")
    rows = [
        variant(a[1], f"MTR-4{i:05d}", **{"prediction.confidence": "high", "prediction.score": 0.9, "location.lat": 44.40 + 0.002 * i})
        for i in range(40)
    ]
    write_items(out_root, "A", rows)
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)
    kinds = {d.decision.value for d in res.plan.decisions}
    assert "assigned" in kinds and "remote_action" in kinds
    assert any(d.rule_id == "R-CAPACITY-REMOTE" for d in res.plan.decisions)
    # rutele nu depășesc tura (08:30 plecare, 15:30 întoarcere)
    for r in res.plan.routes:
        assert r.stops[-1].eta.hour < 16


def test_tap_change_needs_notice_and_value(out_root: Path, tmp_path: Path) -> None:
    c = fixture_items("C")[0]
    worth = variant(c, "PT-9001", **{"impact.value_if_true_lei": 5000.0})  # sezonul întreg de energie pierdută
    small = variant(c, "PT-9002", **{"impact.value_if_true_lei": 300.0})  # nu acoperă priza + întreruperea
    write_items(out_root, "C", [worth, small])
    early = datetime(2026, 11, 2, 18, 0, tzinfo=TZ)  # întreruperea anunțată cu o săptămână înainte
    d = _decisions(agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root, as_of=early))
    assert d[worth["work_item_id"]].rule_id == "R-C-TAP" and d[worth["work_item_id"]].decision.value == "assigned"
    assert d[small["work_item_id"]].rule_id == "R-C-NOTIFY"
    late = datetime(2026, 11, 8, 18, 0, tzinfo=TZ)  # seara dinainte: fără preaviz legal
    d = _decisions(agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root, as_of=late))
    assert d[worth["work_item_id"]].rule_id == "R-C-TAP-NOTICE"
    assert "miercuri 11.11.2026" in d[worth["work_item_id"]].reason_ro  # 2 zile lucrătoare pline după duminică


def test_storm_region_cap(out_root: Path) -> None:
    from cyberpunks.planner.settings import Settings

    cap = int(Settings.load().rule("storm", "max_crews_per_region"))
    b = fixture_items("B")[0]
    rows = [variant(b, f"CT-Z{i}", **{"location.lon": 28.2 + 0.05 * i}) for i in range(cap + 2)]
    write_items(out_root, "B", rows)
    d = _decisions(agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root))
    capped = sum(1 for x in d.values() if x.rule_id == "R-B-REGION-CAP")
    kept = [x for x in d.values() if x.rule_id == "R-B-PREPOSITION"]
    # Cel mult `cap` zone păstrate și doar câte echipe pot ajunge la timp (în Dobrogea, o singură echipă de medie tensiune);
    # restul cer întăriri la dispecer.
    assert 1 <= len(kept) <= cap and capped == len(rows) - len(kept)
    assert all(x.decision.value == "assigned" for x in kept)


def test_plan_totals_are_consistent(out_root: Path) -> None:
    """Cererea interfeței: totalurile din rezumat se potrivesc cu traseele și cu deciziile."""
    res = agent.run("demo-vara", mode="fixtures", out_root=out_root)
    plan = res.plan
    items = {it["work_item_id"]: it for s in "ABC" for it in fixture_items(s)}
    s = plan.summary
    assert s.total_km == round(sum(r.total_km for r in plan.routes), 2)
    assigned = [d for d in plan.decisions if d.decision.value == "assigned"]
    assert s.expected_value_lei == round(sum(items[d.work_item_id]["impact"]["expected_value_lei"] for d in assigned), 2)
    assert s.assigned == len(assigned) and s.crews_used == len(plan.routes)
    counts = {k: sum(1 for d in plan.decisions if d.decision.value == k) for k in ("deferred", "human_review", "remote_action")}
    assert (s.deferred, s.human_review, s.remote_actions) == (counts["deferred"], counts["human_review"], counts["remote_action"])
    assert s.items_in == s.items_valid + s.items_invalid == len(plan.decisions)
    assert s.notifications == len(plan.notifications)
    stops = {st.work_item_id: r.crew_id for r in plan.routes for st in r.stops}
    assert sorted(stops) == sorted(d.work_item_id for d in assigned)  # fiecare alocare e exact într-un traseu
    for d in assigned:
        assert d.crew_id == stops[d.work_item_id]
        assert d.threshold["cost_lei"] > 0 and "action_cost_lei" in d.threshold  # costul folosit la decizie
    for r in plan.routes:
        assert r.depart_at is not None and r.depart_at <= r.stops[0].eta
        if r.return_at is not None:
            assert r.return_at >= r.stops[-1].eta


def test_storm_onset_and_gust_warning(out_root: Path) -> None:
    b = fixture_items("B")[0]
    gusty = variant(b, "CT-RAFALE", **{"impact.safety_flag": True, "extra": {"storm_onset": "2026-11-09T15:00:00+02:00", "gust_max_kmh": 95}})
    write_items(out_root, "B", [gusty])
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)
    d = _decisions(res)[gusty["work_item_id"]]
    assert d.rule_id == "R-B-PREPOSITION"  # la B, safety_flag nu face lucrarea obligatorie
    assert "nu lucrează la înălțime" in d.reason_ro and "15:00" in d.reason_ro
    stop = next(st for r in res.plan.routes for st in r.stops if st.work_item_id == gusty["work_item_id"])
    assert stop.eta == datetime(2026, 11, 9, 14, 0, tzinfo=TZ)  # în zonă cu o oră înainte de furtuna de la 15:00, nu dis-de-dimineață
    route = next(r for r in res.plan.routes if r.stops[-1].work_item_id == gusty["work_item_id"])
    assert route.return_at is None  # echipa rămâne în zonă


def test_human_review_approve_then_replan(out_root: Path) -> None:
    agent.run("demo-vara", mode="fixtures", out_root=out_root)
    wid = "A-20261109-MTR-027710"
    rec = apply_review("demo-vara", wid, "approve", "verificat la telefon", "Ana", out_root=out_root)
    assert rec.actor == "human" and rec.action == "review_approve"
    plan_dir = out_root / "plans" / "demo-vara"
    plan = Plan.model_validate_json((plan_dir / "plan.json").read_text(encoding="utf-8"))
    dec = next(d for d in plan.decisions if d.work_item_id == wid)
    assert dec.rule_id == "R-HUMAN-APPROVE" and dec.decision.value == "assigned"
    trail = [a for a in _audit(plan_dir) if a.work_item_id == wid]
    assert [a.actor for a in trail] == ["agent", "human", "agent"]  # agentul → omul → agentul (replanificare)
    apply_review("demo-vara", wid, "reject", "client plecat", "Ana", out_root=out_root)
    plan = Plan.model_validate_json((plan_dir / "plan.json").read_text(encoding="utf-8"))
    assert next(d for d in plan.decisions if d.work_item_id == wid).rule_id == "R-HUMAN-REJECT"


def test_fresh_run_ignores_previous_human_decisions(out_root: Path) -> None:
    agent.run("demo-vara", mode="fixtures", out_root=out_root)
    wid = "A-20261109-MTR-027710"
    apply_review("demo-vara", wid, "approve", None, "Ana", out_root=out_root)
    res = agent.run("demo-vara", mode="fixtures", out_root=out_root)  # rulare nouă: de la zero
    assert _decisions(res)[wid].rule_id == "R-ABSTAIN"
    history = list((out_root / "plans" / "demo-vara" / "history").iterdir())
    assert any((h / "overrides.json").exists() for h in history)  # decizia omului e păstrată în istoric


def test_review_unknown_item(out_root: Path) -> None:
    agent.run("demo-vara", mode="fixtures", out_root=out_root)
    with pytest.raises(KeyError):
        apply_review("demo-vara", "A-20261109-NU-EXISTA", "approve", None, "Ana", out_root=out_root)


def test_deterministic_plan(out_root: Path, tmp_path: Path) -> None:
    r1 = agent.run("demo-vara", mode="fixtures", out_root=out_root)
    r2 = agent.run("demo-vara", mode="fixtures", out_root=tmp_path / "o2")
    def key(r):
        return [(d.work_item_id, d.decision.value, d.rule_id, d.crew_id) for d in r.plan.decisions]

    assert key(r1) == key(r2)
    assert [(r.crew_id, [s.work_item_id for s in r.stops]) for r in r1.plan.routes] == [
        (r.crew_id, [s.work_item_id for s in r.stops]) for r in r2.plan.routes
    ]


def test_slow_model_output_is_reused_when_fresh(out_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """În modul auto, un model lent (bilanțul) nu se mai rulează dacă are o ieșire proaspătă pentru aceeași zi."""
    import sys
    import types

    calls = {"n": 0}

    def run(scenario, date):
        calls["n"] += 1
        raise RuntimeError("nu trebuia rulat")

    mod = types.ModuleType("cyberpunks.a_bilant.predict")
    mod.run = run
    monkeypatch.setitem(sys.modules, "cyberpunks.a_bilant", types.ModuleType("cyberpunks.a_bilant"))
    monkeypatch.setitem(sys.modules, "cyberpunks.a_bilant.predict", mod)
    for name in ("cyberpunks.a_contoare.predict", "cyberpunks.b_furtuna.predict", "cyberpunks.c_prosumatori.predict"):
        other = types.ModuleType(name)
        other.run = lambda scenario, date: (_ for _ in ()).throw(SystemExit(f"scenariu necunoscut: {scenario}"))
        monkeypatch.setitem(sys.modules, name, other)  # modelele reale nu rulează în test; cad ca B cu un scenariu necunoscut
    from .test_extension import _bilant_post

    write_items(out_root, "A_bilant", [_bilant_post("PT-RE01", "remote_reading")])
    res = agent.run(SCENARIO, date=DATE, mode="auto", out_root=out_root)
    assert calls["n"] == 0 and res.meta["sources"]["A_bilant"]["origin"] == "model"
    assert "refolosit" in res.meta["sources"]["A_bilant"]["note"]
    assert "SystemExit" in res.meta["sources"]["B"]["note"]  # un model care se oprește cu SystemExit nu oprește planul
