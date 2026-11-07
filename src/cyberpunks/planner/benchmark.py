"""Măsurarea solverului: OR-Tools față de rezerva greedy, pe 100, 200 și 300 de lucrări candidate (lume SINTETICĂ).

    uv run python -m cyberpunks.planner.benchmark      # → reports/planner/solver_benchmark.json

Toate lucrările sunt candidate (premiul = valoarea așteptată − costul acțiunii), pe cele 11 echipe din config.
Se compară valoarea netă a traseelor (premiile lucrărilor făcute − costul drumurilor) și timpul de rezolvare.
"""

from __future__ import annotations

import argparse
import json
import platform
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from cyberpunks.common.paths import REPORTS
from cyberpunks.planner import planner_version
from cyberpunks.planner.decide import Context, estimate_costs
from cyberpunks.planner.evaluate import _baseline_action, _items
from cyberpunks.planner.routing import (
    Problem,
    RoutingResult,
    Task,
    Vehicle,
    build_problem,
    minutes_of,
    route_cost_lei,
    solve_greedy,
    solve_ortools,
)
from cyberpunks.planner.settings import TZ, Settings
from cyberpunks.planner.simulate import generate_day


def build_tasks(settings: Settings, n_tasks: int, seed: int) -> tuple[Problem, dict[str, float]]:
    day = generate_day(0, settings, seed=seed, n_meters=n_tasks, storm_prob=1.0, sunny_prob=1.0)
    items = _items(day)
    as_of = datetime.combine(day.plan_date - timedelta(days=1), datetime.min.time(), tzinfo=TZ).replace(hour=18)
    ctx = Context.build(settings, day.plan_date, as_of=as_of)
    start, end = ctx.shift()
    per_km = settings.econ("travel", "vehicle_cost_lei_per_km", 0.0)
    per_min = settings.econ("crew", "cost_lei_per_person_hour", 0.0) / 60.0
    vehicles = [
        Vehicle(c, settings.depots[c.depot_id], minutes_of(start, ctx.plan_date), minutes_of(end, ctx.plan_date), per_km, per_min * c.size)
        for c in settings.crews
    ]
    before = int(settings.rule("storm", "arrive_before_start_min", default=60))
    tasks, prize = [], {}
    for it in items:
        action = _baseline_action(it)
        if action is None:
            continue
        wi = it.wi
        costs = estimate_costs(ctx, wi, action)
        value = max(0.0, wi.impact.expected_value_lei - costs.action_cost - costs.outage_cost)
        terminal = action == "preposition_crew"
        latest = end - timedelta(minutes=wi.effort.duration_min)
        if terminal and wi.time_window is not None:
            latest = wi.time_window.start.astimezone(TZ) - timedelta(minutes=before)
        allowed = [v for v, veh in enumerate(vehicles) if wi.effort.crew_skill.value in veh.crew.skills and veh.crew.size >= wi.effort.crew_size]
        tasks.append(Task(it.id, wi.location.lat, wi.location.lon, 0 if terminal else wi.effort.duration_min, wi.effort.duration_min,
                          wi.effort.crew_skill.value, wi.effort.crew_size, minutes_of(start, ctx.plan_date), minutes_of(latest, ctx.plan_date),
                          terminal, round(value * 100), False, allowed))
        prize[it.id] = value
        if len(tasks) >= n_tasks:
            break
    return build_problem(tasks, vehicles, ctx.travel, 100), prize


def score(pb: Problem, res: RoutingResult, prize: dict[str, float]) -> dict[str, Any]:
    by_crew = {v.crew.crew_id: i for i, v in enumerate(pb.vehicles)}
    index = {t.id: k for k, t in enumerate(pb.tasks)}
    travel = sum(route_cost_lei(pb, by_crew[r.vehicle.crew.crew_id], [index[s.task_id] for s in r.stops]) for r in res.routes)
    collected = sum(prize[t] for t in res.assigned)
    return {
        "solver": res.solver,
        "status": res.status,
        "seconds": round(res.solve_seconds, 3),
        "assigned": len(res.assigned),
        "dropped": len(res.dropped),
        "value_collected_lei": round(collected, 2),
        "travel_cost_lei": round(travel, 2),
        "net_value_lei": round(collected - travel, 2),
        "km": round(sum(r.total_km for r in res.routes), 1),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", default="100,200,300")
    ap.add_argument("--seeds", default="1,2,3")
    ap.add_argument("--out", type=Path, default=REPORTS / "planner" / "solver_benchmark.json")
    args = ap.parse_args(argv)
    settings = Settings.load()
    limit = float(settings.rule("routing", "time_limit_s", default=10))
    sol_limit = settings.rule("routing", "solution_limit", default=400)
    rows = []
    for n in [int(x) for x in args.sizes.split(",")]:
        for seed in [int(x) for x in args.seeds.split(",")]:
            pb, prize = build_tasks(settings, n, seed)
            greedy = score(pb, solve_greedy(pb), prize)
            ort_cfg = solve_ortools(pb, limit, sol_limit)
            ort_long = solve_ortools(pb, 30.0, None)
            row = {"n_tasks": len(pb.tasks), "crews": len(pb.vehicles), "seed": seed, "greedy": greedy,
                   "ortools_config": score(pb, ort_cfg, prize) if ort_cfg else None,
                   "ortools_30s": score(pb, ort_long, prize) if ort_long else None}
            rows.append(row)
            oc = row["ortools_config"] or {}
            print(f"n={row['n_tasks']:>3} seed={seed}: greedy {greedy['net_value_lei']:>10,.0f} lei {greedy['seconds']:.2f}s | "
                  f"ortools(config) {oc.get('net_value_lei', 0):>10,.0f} lei {oc.get('seconds', 0):.2f}s | "
                  f"ortools(30s) {(row['ortools_30s'] or {}).get('net_value_lei', 0):>10,.0f} lei")
    report = {
        "description": "OR-Tools (setările din config/planner.yaml și 30 s fără limită de soluții) față de inserarea greedy, pe lucrări SINTETICE.",
        "reproduce_cmd": f"uv run python -m cyberpunks.planner.benchmark --sizes {args.sizes} --seeds {args.seeds}",
        "config": {"time_limit_s": limit, "solution_limit": sol_limit},
        "machine": {"platform": platform.platform(), "python": platform.python_version()},
        "planner_version": planner_version(),
        "created_at": datetime.now(TZ).replace(microsecond=0).isoformat(),
        "synthetic": True,
        "rows": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Scris {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
