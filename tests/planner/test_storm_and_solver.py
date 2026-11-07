"""Furtuna în plan (alegerea zonelor după echipele reale, coada dispecerului) și solverul care păstrează soluția mai bună.

Regresii găsite pe rulajul demo-vara de la 16:10: echipa din Arad trimisă 97 km la Lugoj, deși zona Arad (lângă bază, aceeași
valoare) rămânea la dispecer, și zona cu cel mai mare risc (Ineu, 58%, incertă) căzută din coada plină a dispecerului.
"""

from __future__ import annotations

from pathlib import Path

from cyberpunks.planner import agent, routing
from cyberpunks.planner.decide import pick_storm_zones
from cyberpunks.planner.geo import TravelModel
from cyberpunks.planner.routing import Task, Vehicle, build_problem, solution_value, solve, solve_greedy, solve_ortools
from cyberpunks.planner.settings import Settings

from .conftest import DATE, SCENARIO, fixture_items, variant, write_items


def _decisions(res) -> dict:
    return {d.work_item_id: d for d in res.plan.decisions}


def _banat_zone(b: dict, name: str, county: str, lat: float, lon: float) -> dict:
    return variant(b, name, **{"location.lat": lat, "location.lon": lon, "location.county": county, "location.zone_id": name,
                               "location.label": f"Zona {name}"})


def test_region_cap_keeps_the_zones_next_to_free_crews(out_root: Path) -> None:
    cap = int(Settings.load().rule("storm", "max_crews_per_region"))
    assert cap == 3  # testul e scris pentru plafonul din config (3 echipe pe regiune, 4 baze în Banat)
    b = fixture_items("B")[0]
    # Aceeași valoare peste tot; Lugoj e primul în fișier, dar e departe de orice bază. Zonele de lângă bazele din
    # Timișoara, Reșița și Arad aduc mai mult cu echipele de acolo, deci Lugoj cere întăriri, nu Arad.
    lugoj = _banat_zone(b, "TM-LUGOJ", "Timiș", 45.6886, 21.9031)
    tm = _banat_zone(b, "TM-TIMISOARA", "Timiș", 45.7537, 21.2257)
    res_ = _banat_zone(b, "CS-RESITA", "Caraș-Severin", 45.3008, 21.8892)
    arad = _banat_zone(b, "AR-ARAD", "Arad", 46.1866, 21.3123)
    write_items(out_root, "B", [lugoj, tm, res_, arad])
    d = _decisions(agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root))
    assert d[lugoj["work_item_id"]].rule_id == "R-B-REGION-CAP"
    assert "AR-ARAD" in d[lugoj["work_item_id"]].reason_ro  # explică unde merg echipele
    for z in (tm, res_, arad):
        assert d[z["work_item_id"]].rule_id == "R-B-PREPOSITION" and d[z["work_item_id"]].decision.value == "assigned"


def test_pick_storm_zones_is_an_assignment_not_a_ranking() -> None:
    # Echipa X: zona 1 = 10, zona 2 = 9; echipa Y: zona 1 = 9, zona 2 = 1. Cel mai bun total: X→2, Y→1 (18), nu X→1, Y→2 (11).
    nets = {1: {"X": 10.0, "Y": 9.0}, 2: {"X": 9.0, "Y": 1.0}, 3: {"X": 0.5}}
    assert pick_storm_zones(nets, {1: "R", 2: "R", 3: "R"}, cap=2) == {1, 2}
    assert pick_storm_zones(nets, {1: "R", 2: "R", 3: "R"}, cap=1) == {1}
    assert pick_storm_zones({}, {}, cap=3) == set()


def test_uncertain_storm_is_not_pushed_out_of_a_full_human_queue(out_root: Path) -> None:
    cap = int(Settings.load().rule("global", "human_review_max_per_day"))
    a = fixture_items("A")[1]
    rows = []
    for i in range(cap + 3):  # coada plină de contoare incerte cu valoare mare
        it = variant(a, f"MTR-Q9{i:03d}", **{"impact.value_if_true_lei": 20000.0})
        it["prediction"].update(abstain=True, abstain_reason="nu sunt sigur: test", confidence="low")
        it["recommended_action"] = "human_review"
        rows.append(it)
    write_items(out_root, "A", rows)
    b = fixture_items("B")[0]
    storm = variant(b, "CT-INCERT", **{"impact.value_if_true_lei": 6000.0})  # scor 0,78, peste pragul modelului B
    storm["prediction"].update(abstain=True, abstain_reason="nu sunt sigur: test", confidence="low")
    storm["recommended_action"] = "human_review"
    write_items(out_root, "B", [storm])
    d = _decisions(agent.run(SCENARIO, date=DATE, mode="existing", out_root=out_root))
    assert not any(x.decision.value == "rejected_invalid" for x in d.values())
    assert d[storm["work_item_id"]].decision.value == "human_review"  # furtuna de mâine nu așteaptă planul următor
    assert sum(1 for x in d.values() if x.decision.value == "human_review") == cap


def _vehicle() -> Vehicle:
    s = Settings.load()
    crew = next(c for c in s.crews if c.depot_id == "D-BUC-V")
    depot = s.depots["D-BUC-V"]
    return Vehicle(crew, depot, 8 * 60, 16 * 60, 1.2, 2.0)


def _task(tid: str, penalty: int, mandatory: bool, service: int = 300) -> Task:
    s = Settings.load()
    depot = s.depots["D-BUC-V"]
    return Task(tid, depot.lat, depot.lon, service, service, "metering", 2, 8 * 60, 16 * 60, False, penalty, mandatory, [0])


def test_ortools_prefers_the_more_valuable_mandatory_task() -> None:
    # Două lucrări obligatorii de 5 ore, o singură tură de 8 ore: încape doar una; trebuie aleasă cea mai valoroasă.
    pb = build_problem([_task("ieftina", 100, True), _task("valoroasa", 900_000, True)], [_vehicle()], TravelModel(), 100)
    res = solve_ortools(pb, time_limit_s=2.0, solution_limit=50)
    assert res is not None and set(res.assigned) == {"valoroasa"}


def test_solve_keeps_greedy_when_ortools_returns_a_worse_plan(monkeypatch) -> None:
    pb = build_problem([_task("a", 50_000, False, 60), _task("b", 40_000, False, 60)], [_vehicle()], TravelModel(), 100)
    empty = routing._collect(pb, {0: []}, "ortools", "SUCCESS", 0.5)
    monkeypatch.setattr(routing, "solve_ortools", lambda *a, **k: empty)
    res = solve(pb, "ortools", 1.0)
    assert res.solver == "greedy" and res.status.startswith("GREEDY_BETTER")
    assert solution_value(pb, res) > solution_value(pb, empty) and set(res.assigned) == {"a", "b"}
    assert solution_value(pb, solve_greedy(pb)) == solution_value(pb, res)
