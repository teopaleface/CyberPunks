"""Cât economisește tura de zonă de la sfârșitul săptămânii față de plecarea a doua zi (lume SINTETICĂ).

    uv run python -m cyberpunks.planner.batching_benchmark      # → reports/planner/weekly_batching.{json,md}

Patru săptămâni de contoare semnalate în București-Ilfov (generatorul din simulate.py, aceleași lucrări pentru ambele
politici), planificate zi lucrătoare cu zi lucrătoare, cu aceleași reguli, aceleași echipe și același solver:

- „a doua zi”: orice vizită care merită pleacă în prima zi lucrătoare după semnalare (dispatch.weekly_batching = false);
- „tura de zonă”: pasul din planner/dispatch.py (vineri, zona plină, pe drum sau termenul legal).

Ce nu încape într-o zi rămâne pentru ziua următoare, cu data sesizării păstrată (extra.registered_at). Se compară
kilometrii, costul drumului (vehicul + oamenii pe drum), zilele-echipă folosite, vizitele făcute, așteptarea, costul
așteptării (pierderea de energie care continuă) și depășirile de termen.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any

from cyberpunks.common.contracts import WorkItem
from cyberpunks.common.paths import REPORTS
from cyberpunks.planner.agent import build_routing
from cyberpunks.planner.decide import Context, decide, is_free_day
from cyberpunks.planner.dispatch import timing, waiting_cost_lei
from cyberpunks.planner.ingest import Item
from cyberpunks.planner.routing import route_cost_lei, solve
from cyberpunks.planner.settings import TZ, Settings
from cyberpunks.planner.simulate import gen_meters


@dataclass
class Pending:
    item: Item
    registered: date


@dataclass
class PolicyResult:
    name: str
    km: float = 0.0
    travel_cost_lei: float = 0.0
    crew_days: int = 0
    visits: int = 0
    stops_per_crew_day: float = 0.0
    waiting_cost_lei: float = 0.0
    wait_working_days: list[int] = field(default_factory=list)
    breaches: int = 0
    left_over: int = 0
    by_day: list[dict[str, Any]] = field(default_factory=list)


def _working_days_after(d0: date, d1: date) -> int:
    n, d = 0, d0
    while d < d1:
        d += timedelta(days=1)
        if not is_free_day(d):
            n += 1
    return n


def arrivals(settings: Settings, start: date, days: int, per_day: int, seed: int) -> dict[date, list[Item]]:
    """Lucrările semnalate în fiecare zi calendaristică (modelele rulează și în weekend). Se păstrează doar contoarele fără
    risc pentru oameni: la cele urgente ambele politici fac același lucru."""
    rng = random.Random(seed)
    out: dict[date, list[Item]] = {}
    for k in range(days):
        d = start + timedelta(days=k)
        created = datetime.combine(d, time(6, 0), tzinfo=TZ)
        raws, _ = gen_meters(rng, d, settings, per_day, 1.0, created)
        items = []
        for i, raw in enumerate(raws):
            raw["impact"]["safety_flag"] = False
            raw["extra"]["registered_at"] = created.isoformat()
            text = json.dumps(raw, sort_keys=True)
            items.append(Item(WorkItem.model_validate(raw), hashlib.sha256(text.encode()).hexdigest(), i, "model"))
        out[d] = items
    return out


def run_policy(settings: Settings, name: str, batching: bool, flow: dict[date, list[Item]], end: date,
               time_limit_s: float) -> PolicyResult:
    s = Settings(**{**settings.__dict__, "planner": json.loads(json.dumps(settings.planner))})
    s.planner.setdefault("dispatch", {})["weekly_batching"] = batching
    res = PolicyResult(name)
    pending: dict[str, Pending] = {}
    days = sorted(flow)
    d = days[0] + timedelta(days=1)
    stops_total = 0
    while d <= end or (pending and d <= end + timedelta(days=21)):
        for a in flow.get(d - timedelta(days=1), []):  # semnalate ieri, planificate de azi încolo
            pending.setdefault(a.id, Pending(a, d - timedelta(days=1)))
        if is_free_day(d):
            d += timedelta(days=1)
            continue
        ctx = Context.build(s, d, as_of=datetime.combine(d - timedelta(days=1), time(18, 0), tzinfo=TZ))
        items = [p.item for p in pending.values()]
        proposals = decide(ctx, items)
        for p in proposals:  # ce nu e vizită (citire la distanță, urmărire, om) iese din coadă la fel la ambele politici
            if not p.route and p.rule_id != "R-WEEKLY-BATCH":
                pending.pop(p.id, None)
        pb = build_routing(ctx, proposals)
        rr = solve(pb, solver="ortools", time_limit_s=time_limit_s, solution_limit=200)
        by_crew = {veh.crew.crew_id: v for v, veh in enumerate(pb.vehicles)}
        index = {t.id: k for k, t in enumerate(pb.tasks)}
        day_km = day_cost = 0.0
        for r in rr.routes:
            res.crew_days += 1
            day_km += r.total_km
            day_cost += route_cost_lei(pb, by_crew[r.vehicle.crew.crew_id], [index[st.task_id] for st in r.stops])
            stops_total += len(r.stops)
        for tid in rr.assigned:
            pend = pending.pop(tid)
            tm = timing(ctx, pend.item.wi)
            res.visits += 1
            res.wait_working_days.append(_working_days_after(pend.registered, d))
            res.waiting_cost_lei += waiting_cost_lei(ctx, pend.item.wi, (d - pend.registered).days)
            res.breaches += int(d > tm.deadline)
        res.km += day_km
        res.travel_cost_lei += day_cost
        res.by_day.append({"date": d.isoformat(), "routes": len(rr.routes), "visits": len(rr.assigned), "km": round(day_km, 1),
                           "pending_after": len(pending)})
        d += timedelta(days=1)
    res.left_over = len(pending)
    res.stops_per_crew_day = stops_total / max(1, res.crew_days)
    return res


def summary(r: PolicyResult, crew_day_cost: float) -> dict[str, Any]:
    w = sorted(r.wait_working_days) or [0]
    return {
        "policy": r.name,
        "visits": r.visits,
        "crew_days": r.crew_days,
        "stops_per_crew_day": round(r.stops_per_crew_day, 2),
        "km": round(r.km, 1),
        "km_per_visit": round(r.km / max(1, r.visits), 2),
        "travel_cost_lei": round(r.travel_cost_lei, 2),
        "travel_cost_per_visit_lei": round(r.travel_cost_lei / max(1, r.visits), 2),
        "crew_day_cost_lei": round(r.crew_days * crew_day_cost, 2),
        "waiting_cost_lei": round(r.waiting_cost_lei, 2),
        "wait_working_days_mean": round(sum(w) / len(w), 2),
        "wait_working_days_max": max(w),
        "deadline_breaches": r.breaches,
        "left_over": r.left_over,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", default="2026-11-02", help="prima zi cu semnalări (luni)")
    ap.add_argument("--weeks", type=int, default=4)
    ap.add_argument("--per-day", type=int, default=40, help="contoare semnalate pe zi (din care o parte merită vizită)")
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--time-limit", type=float, default=5.0)
    ap.add_argument("--out", default=str(REPORTS / "planner"))
    args = ap.parse_args(argv)

    settings = Settings.load()
    start = date.fromisoformat(args.start)
    days = 7 * args.weeks
    flow = arrivals(settings, start, days, args.per_day, args.seed)
    end = start + timedelta(days=days)
    daily = run_policy(settings, "a doua zi", False, flow, end, args.time_limit)
    weekly = run_policy(settings, "tura de zonă (vineri)", True, flow, end, args.time_limit)

    shift_h = (datetime.combine(start, settings.shift_end) - datetime.combine(start, settings.shift_start)).seconds / 3600
    crew_day_cost = shift_h * settings.econ("crew", "cost_lei_per_person_hour") * 2  # echipă de contorizare: 2 oameni
    a, b = summary(daily, crew_day_cost), summary(weekly, crew_day_cost)
    delta = {k: round(b[k] - a[k], 2) for k in a if isinstance(a[k], (int, float)) and k != "policy"}
    saved = {
        "km": round(a["km"] - b["km"], 1),
        "km_pct": round(100 * (a["km"] - b["km"]) / max(1e-9, a["km"]), 1),
        "travel_cost_lei": round(a["travel_cost_lei"] - b["travel_cost_lei"], 2),
        "crew_days": a["crew_days"] - b["crew_days"],
        "crew_day_cost_lei": round(a["crew_day_cost_lei"] - b["crew_day_cost_lei"], 2),
        "extra_waiting_cost_lei": round(b["waiting_cost_lei"] - a["waiting_cost_lei"], 2),
    }
    saved["net_lei"] = round(saved["travel_cost_lei"] + saved["crew_day_cost_lei"] - saved["extra_waiting_cost_lei"], 2)
    report = {
        "synthetic": True,
        "note_ro": "Lume SINTETICĂ (generatorul din planner/simulate.py); cifrele arată ordinul de mărime, nu date PPC.",
        "params": {"start": args.start, "weeks": args.weeks, "per_day": args.per_day, "seed": args.seed,
                   "crews": [c.crew_id for c in settings.crews if "metering" in c.skills], "crew_day_cost_lei": round(crew_day_cost, 2)},
        "policies": [a, b],
        "delta_weekly_minus_daily": delta,
        "saved": saved,
        "by_day": {"a doua zi": daily.by_day, "tura de zonă": weekly.by_day},
    }
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "weekly_batching.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = [
        ("Vizite făcute", "visits", ""), ("Zile-echipă pe teren", "crew_days", ""), ("Opriri pe zi-echipă", "stops_per_crew_day", ""),
        ("Kilometri", "km", ""), ("Km pe vizită", "km_per_visit", ""), ("Costul drumului", "travel_cost_lei", " lei"),
        ("Costul drumului pe vizită", "travel_cost_per_visit_lei", " lei"), ("Costul așteptării (pierdere)", "waiting_cost_lei", " lei"),
        ("Așteptare medie (zile lucrătoare)", "wait_working_days_mean", ""), ("Așteptare maximă (zile lucrătoare)", "wait_working_days_max", ""),
        ("Depășiri de termen", "deadline_breaches", ""), ("Rămase la final", "left_over", ""),
    ]
    md = [
        "# Tura de zonă de vineri față de plecarea a doua zi",
        "",
        (f"Lume **sintetică**: {args.weeks} săptămâni din {args.start}, {args.per_day} contoare semnalate pe zi în București-Ilfov, "
        f"seed {args.seed}. Aceleași lucrări, reguli, echipe și solver pentru ambele politici. "
        "Comanda: `uv run python -m cyberpunks.planner.batching_benchmark`."),
        "",
        "| | a doua zi | tura de zonă |",
        "|---|---:|---:|",
        *[f"| {label} | {a[k]}{u} | {b[k]}{u} |" for label, k, u in rows],
        "",
        (f"**Economie:** {saved['km']} km ({saved['km_pct']}%), {saved['travel_cost_lei']} lei pe drum și "
        f"{saved['crew_days']} zile-echipă ({saved['crew_day_cost_lei']} lei, la {round(crew_day_cost)} lei pe zi-echipă). "
        f"Așteptarea costă în plus {saved['extra_waiting_cost_lei']} lei (energie pierdută până la vizită). "
        f"**Net: {saved['net_lei']} lei.**"),
        "",
        ("Zilele-echipă eliberate nu sunt bani plătiți mai puțin: echipele fac în acele zile alte lucrări (avarii, branșamente). "
        "Le socotim la costul unei zile de muncă, ca valoare a timpului eliberat."),
    ]
    (out / "weekly_batching.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
