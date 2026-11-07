"""Evaluarea agentului: simulare pe mai multe zile, agentul față de strategii simple, pe aceeași lume sintetică.

    uv run python -m cyberpunks.planner.evaluate            # 30 de zile, sămânța 7 → reports/planner/agent_eval.json

Strategii comparate (aceleași echipe, aceleași ture, aceleași restricții de abilități, ferestre și preaviz ANRE):
- agent:          stratul nostru de decizie (reguli cu prag, citire la distanță, om în buclă) + OR-Tools;
- top_k_scor:     trimite echipele la lucrările cu scorul cel mai mare, până se umplu turele;
- primul_venit:   în ordinea în care au sosit lucrările;
- aleator:        în ordine aleatoare;
- doar_contoare:  doar sursa A, după scor (cum ar arăta un sistem cu un singur model).

Contabilitatea e prudentă pentru agent: o citire la distanță, un mesaj sau un caz trimis la om nu primesc valoare
în ziua respectivă (doar costul lor); valoarea vine doar din lucrările făcute de echipe pe probleme reale.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from cyberpunks.common.contracts import DecisionType, WorkItem
from cyberpunks.common.paths import REPORTS
from cyberpunks.planner import planner_version
from cyberpunks.planner.actions import finalize
from cyberpunks.planner.agent import build_routing
from cyberpunks.planner.decide import Context, action_cost, decide, storm_onset
from cyberpunks.planner.ingest import Item
from cyberpunks.planner.routing import Task, Vehicle, build_problem, minutes_of, solve, solve_greedy
from cyberpunks.planner.settings import TZ, Settings
from cyberpunks.planner.simulate import SimDay, generate_day

STRATEGIES = ["agent", "top_k_scor", "primul_venit", "aleator", "doar_contoare"]


@dataclass
class DayResult:
    value_captured_lei: float = 0.0
    action_costs_lei: float = 0.0
    travel_costs_lei: float = 0.0
    km: float = 0.0
    visits: int = 0
    useful_visits: int = 0
    useless_visits: int = 0
    urgent_total: int = 0
    urgent_missed: int = 0
    storms_true: int = 0
    storms_covered: int = 0
    remote_readings: int = 0
    remote_true: int = 0
    human_review: int = 0
    human_true: int = 0
    notifications: int = 0
    solve_seconds: float = 0.0
    by_source_value: dict[str, float] = field(default_factory=lambda: {"A": 0.0, "B": 0.0, "C": 0.0})
    by_source_visits: dict[str, int] = field(default_factory=lambda: {"A": 0, "B": 0, "C": 0})
    by_source_useless: dict[str, int] = field(default_factory=lambda: {"A": 0, "B": 0, "C": 0})

    @property
    def net_value_lei(self) -> float:
        return self.value_captured_lei - self.action_costs_lei - self.travel_costs_lei


def _items(day: SimDay) -> list[Item]:
    out = []
    for i, raw in enumerate(day.items, 1):
        text = json.dumps(raw, ensure_ascii=False, sort_keys=True)
        out.append(Item(WorkItem.model_validate(raw), hashlib.sha256(text.encode()).hexdigest(), i, "model"))
    return out


def _travel_cost(settings: Settings, routes: list, crews_size: dict[str, int]) -> tuple[float, float]:
    per_km = settings.econ("travel", "vehicle_cost_lei_per_km", 0.0)
    per_person_min = settings.econ("crew", "cost_lei_per_person_hour", 0.0) / 60.0
    km = sum(r.total_km for r in routes)
    cost = sum(
        r.total_km * per_km + r.total_travel_min * per_person_min * crews_size[r.vehicle.crew.crew_id] for r in routes
    )
    return km, cost


def _visit_outcome(res: DayResult, ctx: Context, it: Item, action: str, truth: bool) -> None:
    wi = it.wi
    res.visits += 1
    res.by_source_visits[wi.source.value] += 1
    res.action_costs_lei += action_cost(ctx, wi, action)
    if action == "adjust_tap" and wi.effort.requires_planned_outage:
        res.action_costs_lei += (
            wi.impact.customers_affected
            * ctx.settings.econ("voltage", "planned_outage_hours", 1.0)
            * ctx.settings.econ("storm", "cost_per_customer_hour_lei")
        )
    captures = action in ("inspect_on_site", "preposition_crew", "adjust_tap")
    if truth:
        res.useful_visits += 1
        if captures:
            res.value_captured_lei += wi.impact.value_if_true_lei
            res.by_source_value[wi.source.value] += wi.impact.value_if_true_lei
    else:
        res.useless_visits += 1
        res.by_source_useless[wi.source.value] += 1


def _urgent(it: Item, truth: bool) -> bool:
    return truth and (it.wi.source.value == "B" or it.wi.impact.safety_flag)


def run_agent(day: SimDay, settings: Settings) -> DayResult:
    items = _items(day)
    as_of = datetime.combine(day.plan_date - timedelta(days=1), datetime.min.time(), tzinfo=TZ).replace(hour=18)
    ctx = Context.build(settings, day.plan_date, as_of=as_of)
    proposals = decide(ctx, items)
    pb = build_routing(ctx, proposals)
    rr = solve(
        pb,
        solver=str(settings.rule("routing", "solver", default="ortools")),
        time_limit_s=float(settings.rule("routing", "time_limit_s", default=10)),
        solution_limit=settings.rule("routing", "solution_limit", default=400),
    )
    outcome = finalize(ctx, proposals, rr, {}, datetime.now(TZ))
    res = DayResult(solve_seconds=rr.solve_seconds)
    sizes = {c.crew_id: c.size for c in settings.crews}
    res.km, res.travel_costs_lei = _travel_cost(settings, rr.routes, sizes)
    by_id = {it.id: it for it in items}
    for wid, p in outcome.final.items():
        it, truth = by_id[wid], day.truth[wid]
        res.urgent_total += _urgent(it, truth)
        if it.wi.source.value == "B" and truth:
            res.storms_true += 1
        if p.decision == DecisionType.assigned:
            _visit_outcome(res, ctx, it, p.action, truth)
            if it.wi.source.value == "B" and truth:
                res.storms_covered += 1
        else:
            res.urgent_missed += _urgent(it, truth)
            if p.decision == DecisionType.remote_action:
                res.remote_readings += 1
                res.remote_true += truth
                res.action_costs_lei += action_cost(ctx, it.wi, "remote_reading")
            elif p.decision == DecisionType.human_review:
                res.human_review += 1
                res.human_true += truth
            elif p.decision == DecisionType.notify:
                res.notifications += 1
                res.action_costs_lei += action_cost(ctx, it.wi, "notify_customers")
    return res


def _baseline_action(it: Item) -> str | None:
    wi = it.wi
    if wi.source.value == "A":
        return "inspect_on_site"
    if wi.source.value == "B":
        return "preposition_crew"
    if wi.recommended_action.value == "adjust_tap" or wi.effort.requires_planned_outage:
        # o strategie naivă respectă totuși legea: fără preaviz nu se face întreruperea pentru priză
        return "adjust_tap" if wi.extra.get("planned_outage_notified") else None
    return "measurement_campaign"


def run_baseline(day: SimDay, settings: Settings, strategy: str, seed: int) -> DayResult:
    items = _items(day)
    as_of = datetime.combine(day.plan_date - timedelta(days=1), datetime.min.time(), tzinfo=TZ).replace(hour=18)
    ctx = Context.build(settings, day.plan_date, as_of=as_of)
    if strategy == "doar_contoare":
        pool = [it for it in items if it.wi.source.value == "A"]
    else:
        pool = list(items)
    if strategy in ("top_k_scor", "doar_contoare"):
        pool.sort(key=lambda it: -it.wi.prediction.score)
    elif strategy == "primul_venit":
        pool.sort(key=lambda it: it.wi.created_at)
    elif strategy == "aleator":
        random.Random(seed).shuffle(pool)
    start, end = ctx.shift()
    per_km = settings.econ("travel", "vehicle_cost_lei_per_km", 0.0)
    per_person_min = settings.econ("crew", "cost_lei_per_person_hour", 0.0) / 60.0
    vehicles = [
        Vehicle(
            c,
            settings.depots[c.depot_id],
            minutes_of(start, ctx.plan_date),
            minutes_of(end, ctx.plan_date),
            per_km,
            per_person_min * c.size,
        )
        for c in settings.crews
    ]
    before = int(settings.rule("storm", "arrive_before_start_min", default=60))
    tasks, action_of = [], {}
    n = len(pool)
    for rank, it in enumerate(pool):
        action = _baseline_action(it)
        if action is None:
            continue
        wi = it.wi
        terminal = action == "preposition_crew"
        latest = end - timedelta(minutes=wi.effort.duration_min)
        onset = storm_onset(wi) if terminal else None
        if onset is not None:
            latest = onset.astimezone(TZ) - timedelta(minutes=before)
        allowed = [
            v
            for v, veh in enumerate(vehicles)
            if wi.effort.crew_skill.value in veh.crew.skills and veh.crew.size >= wi.effort.crew_size
        ]
        tasks.append(
            Task(
                it.id,
                wi.location.lat,
                wi.location.lon,
                0 if terminal else wi.effort.duration_min,
                wi.effort.duration_min,
                wi.effort.crew_skill.value,
                wi.effort.crew_size,
                minutes_of(start, ctx.plan_date),
                minutes_of(latest, ctx.plan_date),
                terminal,
                n - rank,
                True,
                allowed,
            )
        )
        action_of[it.id] = action
    pb = build_problem(tasks, vehicles, ctx.travel, 100)
    t0 = time.perf_counter()
    rr = solve_greedy(pb)
    res = DayResult(solve_seconds=time.perf_counter() - t0)
    sizes = {c.crew_id: c.size for c in settings.crews}
    res.km, res.travel_costs_lei = _travel_cost(settings, rr.routes, sizes)
    for it in items:
        truth = day.truth[it.id]
        res.urgent_total += _urgent(it, truth)
        if it.wi.source.value == "B" and truth:
            res.storms_true += 1
        if it.id in rr.assigned:
            _visit_outcome(res, ctx, it, action_of[it.id], truth)
            if it.wi.source.value == "B" and truth:
                res.storms_covered += 1
        else:
            res.urgent_missed += _urgent(it, truth)
    return res


def _summary(days: list[DayResult]) -> dict[str, Any]:
    def mean(f) -> float:
        return round(statistics.fmean(f(d) for d in days), 2)

    def total(f) -> float:
        return round(sum(f(d) for d in days), 2)

    visits = sum(d.visits for d in days)
    urgent = sum(d.urgent_total for d in days)
    storms = sum(d.storms_true for d in days)
    return {
        "net_value_lei_total": total(lambda d: d.net_value_lei),
        "net_value_lei_per_day": mean(lambda d: d.net_value_lei),
        "net_value_lei_per_day_std": round(statistics.pstdev(d.net_value_lei for d in days), 2),
        "value_captured_lei_total": total(lambda d: d.value_captured_lei),
        "costs_lei_total": total(lambda d: d.action_costs_lei + d.travel_costs_lei),
        "km_total": total(lambda d: d.km),
        "km_per_day": mean(lambda d: d.km),
        "visits_total": visits,
        "useless_visits_total": sum(d.useless_visits for d in days),
        "useless_visit_rate": round(sum(d.useless_visits for d in days) / visits, 4) if visits else 0.0,
        "urgent_total": urgent,
        "urgent_missed_total": sum(d.urgent_missed for d in days),
        "urgent_missed_rate": round(sum(d.urgent_missed for d in days) / urgent, 4) if urgent else 0.0,
        "storms_true_total": storms,
        "storms_covered_total": sum(d.storms_covered for d in days),
        "remote_readings_total": sum(d.remote_readings for d in days),
        "remote_readings_true": sum(d.remote_true for d in days),
        "human_review_total": sum(d.human_review for d in days),
        "human_review_true": sum(d.human_true for d in days),
        "notifications_total": sum(d.notifications for d in days),
        "value_by_source_lei": {s: round(sum(d.by_source_value[s] for d in days), 2) for s in "ABC"},
        "visits_by_source": {s: sum(d.by_source_visits[s] for d in days) for s in "ABC"},
        "useless_visits_by_source": {s: sum(d.by_source_useless[s] for d in days) for s in "ABC"},
        "solve_seconds_mean": round(statistics.fmean(d.solve_seconds for d in days), 3),
    }


def evaluate(
    days: int = 30, seed: int = 7, n_meters: int = 120, miscalibration: float = 1.0, settings: Settings | None = None
) -> dict[str, Any]:
    settings = settings or Settings.load()
    per_strategy: dict[str, list[DayResult]] = {s: [] for s in STRATEGIES}
    worlds = []
    for d in range(days):
        day = generate_day(d, settings, seed=seed, n_meters=n_meters, miscalibration=miscalibration)
        worlds.append({"date": day.plan_date.isoformat(), **day.meta})
        per_strategy["agent"].append(run_agent(day, settings))
        for s in STRATEGIES[1:]:
            per_strategy[s].append(run_baseline(day, settings, s, seed * 1000 + d))
    summary = {s: _summary(r) for s, r in per_strategy.items()}
    agent_net = summary["agent"]["net_value_lei_total"]
    for s in STRATEGIES[1:]:
        base = summary[s]["net_value_lei_total"]
        summary[s]["agent_minus_strategy_net_lei"] = round(agent_net - base, 2)
    return {
        "days": days,
        "seed": seed,
        "n_meters_per_day": n_meters,
        "miscalibration": miscalibration,
        "strategies": summary,
        "per_day_net_value_lei": {s: [round(d.net_value_lei, 2) for d in r] for s, r in per_strategy.items()},
        "worlds": worlds,
    }


ABLATIONS: dict[str, tuple[str, list[tuple[tuple[str, ...], Any]]]] = {
    "fara_prag_etic": ("Fără pragul etic (vizită și sub scorul 0,5, dacă merită)", [(("meters", "visit_min_score"), 0.0)]),
    "greedy_in_loc_de_ortools": ("Aceleași reguli, trasee făcute greedy în loc de OR-Tools", [(("routing", "solver"), "greedy")]),
}


def _with(overrides: list[tuple[tuple[str, ...], Any]], economics: bool = False) -> Settings:
    s = Settings.load()
    for path, value in overrides:
        node = s.economics if economics else s.planner
        for key in path[:-1]:
            node = node.setdefault(key, {})
        node[path[-1]] = value
    return s


def _agent_only(days: int, seed: int, n_meters: int, settings: Settings) -> dict[str, Any]:
    results = [run_agent(generate_day(d, settings, seed=seed, n_meters=n_meters), settings) for d in range(days)]
    return _summary(results)


def ablations(days: int, seed: int, n_meters: int) -> dict[str, Any]:
    """Ce aduce fiecare piesă: agentul cu o regulă sau o componentă scoasă, pe aceleași zile."""
    return {name: {"label_ro": label, **_agent_only(days, seed, n_meters, _with(ov))} for name, (label, ov) in ABLATIONS.items()}


def sensitivity(days: int, seed: int, n_meters: int) -> list[dict[str, Any]]:
    """Agentul față de top_k_scor când variem ipotezele fără sursă (intervalele din docs/research/planificator.md)."""
    cases = [
        ("cost_per_customer_hour_lei", ("storm", "cost_per_customer_hour_lei"), [5.5, 15.0]),
        ("preposition_cost_lei_per_crew_shift", ("storm", "preposition_cost_lei_per_crew_shift"), [1500.0, 4100.0]),
        ("inspection_visit_cost_lei", ("meters", "inspection_visit_cost_lei"), [180.0, 340.0]),
    ]
    out = []
    for name, path, values in cases:
        for value in values:
            s = _with([(path, value)], economics=True)
            agent_days, base_days = [], []
            for d in range(days):
                day = generate_day(d, s, seed=seed, n_meters=n_meters)
                agent_days.append(run_agent(day, s))
                base_days.append(run_baseline(day, s, "top_k_scor", seed * 1000 + d))
            a, b = _summary(agent_days), _summary(base_days)
            adv = round(100 * (a["net_value_lei_total"] - b["net_value_lei_total"]) / abs(b["net_value_lei_total"]), 1) if b["net_value_lei_total"] else None
            out.append({"parameter": name, "value": value, "agent_net_lei_per_day": a["net_value_lei_per_day"],
                        "top_k_scor_net_lei_per_day": b["net_value_lei_per_day"], "agent_advantage_pct": adv})
    return out


NAMES_RO = {
    "agent": "Agentul (reguli + OR-Tools)",
    "top_k_scor": "Top-K după scor",
    "primul_venit": "Primul venit",
    "aleator": "Aleator",
    "doar_contoare": "Doar contoare (o singură sursă)",
}


def _fmt(x: float, d: int = 0) -> str:
    s = f"{x:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def render_markdown(report: dict[str, Any]) -> str:
    """Tabelele din agent_eval.json, în markdown (reports/planner/agent_eval.md). Toate cifrele vin din raport."""
    m = report["main"]
    s = m["strategies"]
    lines = [
        "# Evaluarea agentului: cifrele (generat de script)",
        "",
        (
            f"Generat automat de `{report['reproduce_cmd']}` la {report['created_at']} (`{report['planner_version']}`). "
            f"Lume SINTETICĂ, {m['days']} de zile, {m['n_meters_per_day']} de lucrări A pe zi. Metoda: `reports/planner/README.md`."
        ),
        "",
        "| Strategie | Valoare netă pe zi (lei) | Km pe zi | Vizite fără problemă reală | Urgențe ratate | Furtuni reale acoperite |",
        "|---|---|---|---|---|---|",
    ]
    for name in STRATEGIES:
        r = s[name]
        lines.append(
            f"| {NAMES_RO[name]} | {_fmt(r['net_value_lei_per_day'])} | {_fmt(r['km_per_day'])} | {_fmt(100 * r['useless_visit_rate'], 1)}% "
            f"| {_fmt(100 * r['urgent_missed_rate'], 1)}% | {r['storms_covered_total']} din {r['storms_true_total']} |"
        )
    a = s["agent"]
    best = max((n for n in STRATEGIES[1:]), key=lambda n: s[n]["net_value_lei_total"])
    gain = 100 * (a["net_value_lei_total"] - s[best]["net_value_lei_total"]) / abs(s[best]["net_value_lei_total"])
    lines += [
        "",
        f"Agentul aduce cu {_fmt(gain, 0)}% mai multă valoare netă decât cea mai bună strategie simplă ({NAMES_RO[best].lower()}).",
        "",
        "## Pe surse (vizite fără problemă reală / vizite)",
        "",
        "| Strategie | Contoare (A) | Furtună (B) | Tensiune (C) |",
        "|---|---|---|---|",
    ]
    for name in STRATEGIES:
        r = s[name]
        cells = [f"{r['useless_visits_by_source'][x]} / {r['visits_by_source'][x]}" for x in "ABC"]
        lines.append(f"| {NAMES_RO[name]} | " + " | ".join(cells) + " |")
    lines += [
        "",
        (
            f"Agentul a mai trimis {a['remote_readings_total']} citiri la distanță (din care {a['remote_readings_true']} pe probleme reale) "
            f"și {a['human_review_total']} cazuri la om (din care {a['human_review_true']} reale). "
            "În evaluare ele nu primesc valoare în ziua respectivă, doar costul."
        ),
    ]
    if "robustness_overconfident_model" in report:
        r = report["robustness_overconfident_model"]
        rs = r["strategies"]
        lines += ["", f"## Robustețe: model supra-încrezător ({r['days']} zile, adevărul ~ Bernoulli(scor^{r['miscalibration']}))", "",
                  "| Strategie | Valoare netă pe zi (lei) | Urgențe ratate |", "|---|---|---|"]
        for name in STRATEGIES:
            lines.append(f"| {NAMES_RO[name]} | {_fmt(rs[name]['net_value_lei_per_day'])} | {_fmt(100 * rs[name]['urgent_missed_rate'], 1)}% |")
    if "ablations" in report:
        lines += ["", "## Ablații: ce aduce fiecare piesă (aceleași zile)", "", "| Varianta | Valoare netă pe zi (lei) | Km pe zi | Vizite fără problemă reală |", "|---|---|---|---|",
                  f"| Agentul complet | {_fmt(a['net_value_lei_per_day'])} | {_fmt(a['km_per_day'])} | {_fmt(100 * a['useless_visit_rate'], 1)}% |"]
        for v in report["ablations"].values():
            lines.append(f"| {v['label_ro']} | {_fmt(v['net_value_lei_per_day'])} | {_fmt(v['km_per_day'])} | {_fmt(100 * v['useless_visit_rate'], 1)}% |")
    if "sensitivity" in report:
        lines += ["", "## Sensibilitate la ipotezele fără sursă", "", "| Parametru | Valoare | Agentul (lei/zi) | Top-K (lei/zi) | Avantajul agentului |", "|---|---|---|---|---|"]
        for row in report["sensitivity"]:
            lines.append(f"| `{row['parameter']}` | {_fmt(row['value'], 1)} | {_fmt(row['agent_net_lei_per_day'])} | {_fmt(row['top_k_scor_net_lei_per_day'])} | +{_fmt(row['agent_advantage_pct'], 1)}% |")
    return "\n".join(lines) + "\n"


def render_chart(report: dict[str, Any], path: Path) -> Path:
    """Graficul evaluării (PNG): valoarea netă pe zi și urgențele ratate, pe strategii; agentul evidențiat.
    Două panouri cu aceeași ordine (nu o axă dublă); valorile scrise direct pe bare; tabelul complet e în agent_eval.md."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    fonts = Path(__file__).parent / "assets" / "fonts"
    for f in ("NotoSans-Regular.ttf", "NotoSans-Bold.ttf"):
        font_manager.fontManager.addfont(str(fonts / f))
    plt.rcParams.update({"font.family": "Noto Sans", "font.size": 10})
    surface, ink, ink2, grid = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
    accent, muted = "#2a78d6", "#a9a79f"
    s = report["main"]["strategies"]
    order = list(STRATEGIES)
    labels = [NAMES_RO[n].replace(" (reguli + OR-Tools)", "").replace(" (o singură sursă)", "") for n in order]
    panels = [
        ("Valoare netă pe zi (lei)", [s[n]["net_value_lei_per_day"] for n in order], lambda v: _fmt(v)),
        ("Urgențe ratate (mai puțin e mai bine)", [100 * s[n]["urgent_missed_rate"] for n in order], lambda v: f"{_fmt(v, 0)}%"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.6), dpi=160, gridspec_kw={"wspace": 0.55})
    fig.patch.set_facecolor(surface)
    for ax, (title, values, fmt) in zip(axes, panels, strict=True):
        ax.set_facecolor(surface)
        ys = list(range(len(order)))[::-1]
        colors = [accent if n == "agent" else muted for n in order]
        ax.barh(ys, values, height=0.56, color=colors, edgecolor=surface, linewidth=2)
        top = max(values) or 1.0
        for y, v, n in zip(ys, values, order, strict=True):
            ax.text(v + top * 0.02, y, fmt(v), va="center", ha="left", color=ink if n == "agent" else ink2,
                    fontweight="bold" if n == "agent" else "normal", fontsize=9.5)
        ax.set_yticks(ys, labels, color=ink)
        ax.set_xlim(0, top * 1.25)
        ax.set_title(title, loc="left", color=ink, fontsize=11, fontweight="bold", pad=8)
        ax.grid(axis="x", color=grid, linewidth=0.8)
        ax.set_axisbelow(True)
        ax.tick_params(axis="x", colors=ink2, labelsize=8.5, length=0)
        ax.tick_params(axis="y", length=0)
        ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins=4))
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _pos: _fmt(v)))
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(grid)
    m = report["main"]
    fig.text(0.01, 0.995, f"Agentul față de strategii simple: {m['days']} de zile SINTETICE, aceleași 11 echipe și restricții",
             ha="left", va="top", color=ink2, fontsize=9)
    fig.text(0.01, 0.01, f"Refacere: {report['reproduce_cmd']}. Tabelul complet: reports/planner/agent_eval.md",
             ha="left", va="bottom", color=ink2, fontsize=7.5)
    fig.subplots_adjust(left=0.13, right=0.97, top=0.82, bottom=0.17)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=surface)
    plt.close(fig)
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Evaluarea agentului față de strategii simple (lume sintetică).")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--meters", type=int, default=120, help="câte lucrări A pe zi")
    ap.add_argument("--out", type=Path, default=REPORTS / "planner" / "agent_eval.json")
    ap.add_argument("--no-robustness", action="store_true", help="fără rularea cu model supra-încrezător")
    args = ap.parse_args(argv)
    t0 = time.perf_counter()
    settings = Settings.load()
    main_run = evaluate(args.days, args.seed, args.meters, 1.0, settings)
    report: dict[str, Any] = {
        "description": "Agentul față de strategii simple, pe o lume SINTETICĂ cu adevărul cunoscut (scoruri calibrate prin construcție).",
        "reproduce_cmd": f"uv run python -m cyberpunks.planner.evaluate --days {args.days} --seed {args.seed} --meters {args.meters}",
        "planner_version": planner_version(),
        "created_at": datetime.now(TZ).replace(microsecond=0).isoformat(),
        "synthetic": True,
        "main": main_run,
    }
    if not args.no_robustness:
        report["robustness_overconfident_model"] = evaluate(
            max(10, args.days // 3), args.seed + 1, args.meters, 1.6, settings
        )
        report["ablations"] = ablations(args.days, args.seed, args.meters)
        report["sensitivity"] = sensitivity(args.days, args.seed, args.meters)
    report["runtime_s"] = round(time.perf_counter() - t0, 1)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.out.with_suffix(".md").write_text(render_markdown(report), encoding="utf-8")
    render_chart(report, args.out.with_suffix(".png"))
    s = main_run["strategies"]
    print(f"Scris {args.out} ({report['runtime_s']} s)")
    print(f"{'strategie':<15}{'valoare netă/zi':>17}{'km/zi':>9}{'vizite inutile':>16}{'urgențe ratate':>16}")
    for name in STRATEGIES:
        r = s[name]
        print(
            f"{name:<15}{r['net_value_lei_per_day']:>17,.0f}{r['km_per_day']:>9,.0f}{r['useless_visit_rate']:>16.1%}{r['urgent_missed_rate']:>16.1%}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
