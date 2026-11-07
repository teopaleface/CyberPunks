"""A patra revizuire independentă (Codex, 16:55): un test pentru fiecare problemă găsită."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from cyberpunks.planner import agent, review
from cyberpunks.planner.decide import pick_storm_zones
from cyberpunks.planner.evaluate import _with
from cyberpunks.planner.geo import TravelModel
from cyberpunks.planner.routing import Task, Vehicle, build_problem, solution_value, solve_greedy, solve_ortools
from cyberpunks.planner.settings import TZ, Settings

from .conftest import DATE, SCENARIO, fixture_items, variant, write_items


def _decisions(res) -> dict:
    return {d.work_item_id: d for d in res.plan.decisions}


def _zone(b: dict, name: str, county: str, lat: float, lon: float) -> dict:
    return variant(b, name, **{"location.lat": lat, "location.lon": lon, "location.county": county, "location.zone_id": name,
                               "location.label": f"Zona {name}"})


def test_storm_choice_reserves_the_crew_of_an_approved_zone() -> None:
    # Echipele A (Arad) și R (Reșița); zona M e aprobată de dispecer; plafon 1 pentru zonele opționale Z1 și Z2.
    # M cu A, apoi Z2 cu R: 5.000 + 8.100. Dacă selecția ar uita că M ține o echipă, ar păstra Z1 (8.000 cu A).
    nets = {0: {"A": 5000.0, "R": 2000.0}, 1: {"A": 8000.0, "R": 7000.0}, 2: {"R": 8100.0}}
    regions = {0: "Banat", 1: "Banat", 2: "Banat"}
    assert pick_storm_zones(nets, regions, cap=1, mandatory={0}) == {0, 2}
    assert pick_storm_zones(nets, regions, cap=1) == {2}  # fără zona aprobată: cea mai valoroasă singură


def test_approving_a_reinforcement_request_keeps_the_cap_for_the_rest(out_root: Path) -> None:
    b = fixture_items("B")[0]
    zones = [_zone(b, "TM-LUGOJ", "Timiș", 45.6886, 21.9031), _zone(b, "TM-TIMISOARA", "Timiș", 45.7537, 21.2257),
             _zone(b, "CS-RESITA", "Caraș-Severin", 45.3008, 21.8892), _zone(b, "AR-ARAD", "Arad", 46.1866, 21.3123),
             _zone(b, "HD-DEVA", "Hunedoara", 45.8781, 22.9116)]
    write_items(out_root, "B", zones)
    d = _decisions(agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root))
    capped = [k for k, x in d.items() if x.rule_id == "R-B-REGION-CAP"]
    assert capped
    review.apply_review(scenario=SCENARIO, work_item_id=capped[0], decision="approve", note=None, reviewer="Ana", out_root=out_root)
    plan = json.loads((out_root / "plans" / SCENARIO / "plan.json").read_text(encoding="utf-8"))
    after = {x["work_item_id"]: x for x in plan["decisions"]}
    assert after[capped[0]]["rule_id"] == "R-HUMAN-APPROVE"
    optional_kept = [k for k, x in after.items() if x["rule_id"] == "R-B-PREPOSITION"]
    assert len(optional_kept) <= int(Settings.load().rule("storm", "max_crews_per_region"))
    crews = [r["crew_id"] for r in plan["routes"]]
    assert len(crews) == len(set(crews))  # o echipă într-o singură zonă


def test_bad_c_summary_does_not_stop_the_plan(out_root: Path) -> None:
    c = fixture_items("C")[0]
    path = write_items(out_root, "C", [c])
    for bad in ("[]", '{"weather": {"gti_max": "lipsește", "temp_noon": null}, "posts": "multe"}', "{nu e json"):
        (path.parent / "C_summary.json").write_text(bad, encoding="utf-8")
        res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)
        lines = res.meta["day_context"]
        assert any(x.startswith("Tensiune") for x in lines) and not any("W/m²" in x for x in lines)


def test_winter_context_reports_the_crews_that_were_sent(out_root: Path) -> None:
    c = fixture_items("C")[0]
    worth = variant(c, "PT-9101", **{"impact.value_if_true_lei": 5000.0})
    write_items(out_root, "C", [worth])
    early = datetime(2026, 11, 2, 18, 0, tzinfo=TZ)  # întreruperea anunțată la timp: priza se plătește și în noiembrie
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root, as_of=early)
    assert _decisions(res)[worth["work_item_id"]].rule_id == "R-C-TAP"
    line = next(x for x in res.meta["day_context"] if x.startswith("Tensiune"))
    assert "1 primesc echipă" in line and "nu se mai plătește" not in line and "până la primăvară" not in line


def test_no_alert_lists_the_same_case_twice(out_root: Path) -> None:
    a = fixture_items("A")[0]  # tamper, cu risc pentru oameni
    rows = [variant(a, f"MTR-S{i:04d}", **{"prediction.score": 0.95, "prediction.confidence": "high", "location.lat": 44.40 + 0.003 * i})
            for i in range(14)]
    write_items(out_root, "A", rows)
    tight = _with([(("global", "safety_max_mandatory_per_day"), 1)])
    tight.crews = [c for c in tight.crews if c.crew_id == "E-BV-1"]  # o singură echipă de contoare: nu încap toate
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root, settings=tight)
    over = [x for x in res.plan.decisions if x.rule_id == "R-SAFETY-OVER-CAP"]
    assert any(x.decision.value == "remote_action" for x in over)  # cazuri peste cotă care n-au încăput: rezerva a fost folosită
    for alert in res.plan.alerts:
        assert len(alert.work_item_ids) == len(set(alert.work_item_ids)), alert.title_ro


def _vehicle() -> Vehicle:
    s = Settings.load()
    crew = next(c for c in s.crews if c.depot_id == "D-BUC-V")
    return Vehicle(crew, s.depots["D-BUC-V"], 8 * 60, 16 * 60, 1.2, 2.0)


def _task(tid: str, penalty: int, mandatory: bool, service: int = 480) -> Task:
    depot = Settings.load().depots["D-BUC-V"]
    return Task(tid, depot.lat, depot.lon, service, service, "metering", 2, 8 * 60, 8 * 60, False, penalty, mandatory, [0])


def test_ortools_and_the_comparison_agree_on_mandatory_work() -> None:
    # Două lucrări de 8 ore, una singură încape. Cea opțională are un premiu uriaș (peste vechea penalitate fixă de 10^10 bani);
    # obligatoria trebuie să câștige oricum, și în OR-Tools, și în comparația cu greedy.
    pb = build_problem([_task("obligatorie", 100, True), _task("optionala", 10**10 + 101, False)], [_vehicle()], TravelModel(), 100)
    res = solve_ortools(pb, time_limit_s=2.0, solution_limit=50)
    assert res is not None and set(res.assigned) == {"obligatorie"}
    greedy = solve_greedy(pb)
    assert set(greedy.assigned) == {"obligatorie"} and solution_value(pb, res) == solution_value(pb, greedy)


def test_time_limit_stop_is_flagged() -> None:
    tasks = [Task(f"t{i}", 44.40 + 0.01 * i, 26.0 + 0.01 * (i % 7), 30, 30, "metering", 2, 8 * 60, 15 * 60, False, 50_000, False, [0])
             for i in range(40)]
    pb = build_problem(tasks, [_vehicle()], TravelModel(), 100)
    res = solve_ortools(pb, time_limit_s=0.05, solution_limit=None)
    assert res is not None and "TIME_LIMIT" in res.status
    assert "TIME_LIMIT" not in solve_ortools(pb, time_limit_s=60.0, solution_limit=20).status


def test_uncertain_high_risk_storm_still_raises_the_risk_alert(out_root: Path) -> None:
    b = fixture_items("B")[0]  # scor 0,78: peste pragul de alertă
    storm = variant(b, "CT-NESIGUR")
    storm["prediction"].update(abstain=True, abstain_reason="nu sunt sigur: test", confidence="low")
    storm["recommended_action"] = "human_review"
    write_items(out_root, "B", [storm])
    res = agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root)
    assert _decisions(res)[storm["work_item_id"]].decision.value == "human_review"
    risk = [a for a in res.plan.alerts if a.title_ro.startswith("Risc de avarii") and storm["work_item_id"] in a.work_item_ids]
    assert len(risk) == 1 and "decide dispecerul" in risk[0].title_ro
