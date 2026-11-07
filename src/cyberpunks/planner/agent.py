"""Agentul cap-coadă: Perceive → Estimate → Decide → Act, fără intervenție manuală între pași.

    uv run cyberpunks run --scenario demo-vara

- Perceive: configurația (echipe, baze, praguri, ipoteze), scenariul și data, ce date și modele există.
- Estimate: modelele noastre A, B, C (`cyberpunks.<fir>.predict.run(scenario, date)`). Dacă un model lipsește
  sau dă eroare, se folosește ultima lui ieșire, apoi exemplele din contracts/fixtures/; sursa e marcată.
- Decide: validarea (carantina), regulile cu prag (decide.py), traseele (routing.py).
- Act: planul, jurnalul, alertele, notificările, raportul și ordinele de lucru, în outputs/plans/<scenariu>/.
"""

from __future__ import annotations

import importlib
import json
import shutil
import time
from dataclasses import dataclass, field
from datetime import date as Date
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from cyberpunks.common.contracts import AuditRecord, Plan
from cyberpunks.common.paths import CONTRACTS, OUTPUTS
from cyberpunks.planner import planner_version
from cyberpunks.planner.actions import build_plan, finalize, quarantine_rows, write_json, write_jsonl
from cyberpunks.planner.decide import Context, Override, decide
from cyberpunks.planner.ingest import Origin, SourceLoad, finalize_status, infer_plan_date, load_source
from cyberpunks.planner.routing import Task, Vehicle, build_problem, minutes_of, solve
from cyberpunks.planner.settings import TZ, Scenario, Settings

PREDICTORS = {"A": "cyberpunks.a_contoare.predict", "B": "cyberpunks.b_furtuna.predict", "C": "cyberpunks.c_prosumatori.predict"}
FIXTURES = {s: CONTRACTS / "fixtures" / f"work_items_{s}.jsonl" for s in "ABC"}
Mode = Literal["auto", "existing", "fixtures"]


@dataclass
class SourcePick:
    path: Path | None
    origin: Origin
    note: str = ""
    seconds: float = 0.0


@dataclass
class RunResult:
    plan: Plan
    timings: dict[str, float]
    plan_dir: Path
    meta: dict[str, Any] = field(default_factory=dict)


# ------------------------------------------------------------------ Estimate: modelele A, B, C


def _work_items_file(out_root: Path, scenario: str, source: str) -> Path:
    return out_root / "work_items" / scenario / f"{source}.jsonl"


def _fixture_date() -> Date | None:
    return infer_plan_date(list(FIXTURES.values()))


def estimate(scenario: str, plan_date: Date | None, mode: Mode, out_root: Path) -> dict[str, SourcePick]:
    picks: dict[str, SourcePick] = {}
    fixture_date = _fixture_date()
    for src, module in PREDICTORS.items():
        existing = _work_items_file(out_root, scenario, src)
        t0 = time.perf_counter()
        note = ""
        if mode == "auto" and plan_date is not None:
            try:
                mod = importlib.import_module(module)
                runner = mod.run
            except (ImportError, AttributeError) as exc:
                note = f"modelul {src} nu e încă disponibil ({type(exc).__name__})"
            else:
                try:
                    path = Path(runner(scenario, plan_date.isoformat()))
                    picks[src] = SourcePick(path, "model", f"rulat {module}.run", time.perf_counter() - t0)
                    continue
                except Exception as exc:  # noqa: BLE001 - un model căzut nu oprește planul
                    note = f"modelul {src} a dat eroare: {type(exc).__name__}: {str(exc)[:200]}"
        if mode != "fixtures" and existing.exists():
            origin: Origin = "stale" if note and "eroare" in note else "model"
            picks[src] = SourcePick(existing, origin, note or "ieșirea existentă a modelului", time.perf_counter() - t0)
            continue
        if mode != "existing" and FIXTURES[src].exists() and (plan_date is None or plan_date == fixture_date):
            picks[src] = SourcePick(FIXTURES[src], "fixture", (note + "; " if note else "") + "exemple din contracts/fixtures/", time.perf_counter() - t0)
            continue
        picks[src] = SourcePick(None, "missing", note or "nicio ieșire pentru data planului", time.perf_counter() - t0)
    return picks


# ------------------------------------------------------------------ Decide: trasee


def build_routing(ctx: Context, proposals: list) -> Any:
    s = ctx.settings
    start, end = ctx.shift()
    per_km = s.econ("travel", "vehicle_cost_lei_per_km", 0.0)
    per_person_min = s.econ("crew", "cost_lei_per_person_hour", 0.0) / 60.0
    vehicles = [
        Vehicle(c, s.depots[c.depot_id], minutes_of(start, ctx.plan_date), minutes_of(end, ctx.plan_date), per_km, per_person_min * c.size)
        for c in s.crews
    ]
    scale = int(s.rule("routing", "value_scale", default=100))
    tasks = []
    for p in proposals:
        if not p.route:
            continue
        wi = p.wi
        allowed = [v for v, veh in enumerate(vehicles) if wi.effort.crew_skill.value in veh.crew.skills and veh.crew.size >= wi.effort.crew_size]
        tasks.append(
            Task(
                id=p.id, lat=wi.location.lat, lon=wi.location.lon,
                service_min=0 if p.terminal else wi.effort.duration_min, display_min=wi.effort.duration_min,
                skill=wi.effort.crew_skill.value, crew_size=wi.effort.crew_size,
                earliest=minutes_of(p.earliest, ctx.plan_date), latest=minutes_of(p.latest, ctx.plan_date),
                terminal=p.terminal, penalty=round((p.priority or 0.0) * scale), mandatory=p.mandatory, allowed=allowed,
            )
        )
    return build_problem(tasks, vehicles, ctx.travel, scale)


# ------------------------------------------------------------------ suprascrierile omului


def load_overrides(plan_dir: Path) -> dict[str, Override]:
    p = plan_dir / "overrides.json"
    if not p.exists():
        return {}
    raw = json.loads(p.read_text(encoding="utf-8"))
    return {
        wid: Override(o["decision"], o["reviewer"], o.get("note"), datetime.fromisoformat(o["ts"]), o["audit_id"])
        for wid, o in raw.items()
    }


# ------------------------------------------------------------------ rularea


def _decide_and_act(
    *, settings: Settings, scenario: str, plan_date: Date, loads: dict[str, SourceLoad], as_of: datetime | None,
    plan_dir: Path, timings: dict[str, float], meta: dict[str, Any], append_audit: bool, solver: str | None,
) -> RunResult:
    t0 = time.perf_counter()
    # Deciziile omului se reaplică doar la replanificare; o rulare nouă pornește de la zero (cele vechi rămân în history/).
    overrides = load_overrides(plan_dir) if append_audit else {}
    ctx = Context.build(settings, plan_date, as_of=as_of, overrides=overrides)
    items = [it for s in "ABC" for it in loads[s].items]
    proposals = decide(ctx, items)
    pb = build_routing(ctx, proposals)
    rr = solve(
        pb,
        solver=solver or str(settings.rule("routing", "solver", default="ortools")),
        time_limit_s=float(settings.rule("routing", "time_limit_s", default=10)),
        solution_limit=settings.rule("routing", "solution_limit", default=400),
    )
    timings["decide"] = round(time.perf_counter() - t0, 3)

    t1 = time.perf_counter()
    generated_at = datetime.now(TZ).replace(microsecond=0)
    outcome = finalize(ctx, proposals, rr, loads, generated_at)
    plan_id = f"PLAN-{scenario}-{plan_date:%Y%m%d}-{generated_at:%H%M%S}"
    plan = build_plan(ctx, scenario, plan_id, planner_version(), generated_at, outcome, loads)

    plan_dir.mkdir(parents=True, exist_ok=True)
    if not append_audit and (plan_dir / "plan.json").exists():
        _archive(plan_dir)
    run_record = AuditRecord(
        audit_id=f"run-{plan_id}", ts=generated_at, actor="agent", action="replan" if append_audit else "run",
        rule_id=None, note=(
            f"scenariu {scenario}, data {plan_date.isoformat()}, surse "
            + ", ".join(f"{s}={loads[s].status}/{loads[s].origin}" for s in "ABC")
            + f"; solver {rr.solver} ({rr.status}, {rr.solve_seconds:.2f} s)"
        ),
    )
    audit_rows = [run_record.model_dump(mode="json")] + [a.model_dump(mode="json") for a in outcome.audit]
    write_jsonl(plan_dir / "audit.jsonl", audit_rows, append=append_audit)
    write_json(plan_dir / "plan.json", plan.model_dump(mode="json"))
    write_jsonl(plan_dir / "work_items.jsonl", [it.wi.model_dump(mode="json") for it in items])
    write_jsonl(plan_dir / "quarantine.jsonl", quarantine_rows(loads))
    write_json(plan_dir / "alerts.json", [a.model_dump(mode="json") for a in plan.alerts])
    write_json(plan_dir / "notifications.json", [n.model_dump(mode="json") for n in plan.notifications])

    meta.update(
        {
            "plan_id": plan_id, "scenario": scenario, "plan_date": plan_date.isoformat(), "as_of": ctx.as_of.isoformat(),
            "generated_at": generated_at.isoformat(), "planner_version": planner_version(),
            "solver": {"name": rr.solver, "status": rr.status, "seconds": round(rr.solve_seconds, 3),
                       "objective_lei": rr.objective_lei, "tasks": len(pb.tasks), "crews": len(pb.vehicles)},
            "overrides": len(overrides),
        }
    )
    try:
        from cyberpunks.planner.workorders import write_work_orders

        meta["work_orders"] = [p.name for p in write_work_orders(plan, items, plan_dir, settings)]
    except ImportError:
        meta["work_orders"] = []
    try:
        from cyberpunks.planner.report import render_report

        (plan_dir / "report.md").write_text(render_report(plan, items, meta, timings | {"act": 0.0}), encoding="utf-8")
    except ImportError:
        pass
    timings["act"] = round(time.perf_counter() - t1, 3)
    meta["timings"] = timings
    write_json(plan_dir / "run.json", meta)
    return RunResult(plan=plan, timings=timings, plan_dir=plan_dir, meta=meta)


def _archive(plan_dir: Path) -> None:
    """Planul vechi (și jurnalul lui) se mută în history/<plan_id>/ înainte de o rulare nouă."""
    try:
        old_id = json.loads((plan_dir / "plan.json").read_text(encoding="utf-8")).get("plan_id", "vechi")
    except (OSError, json.JSONDecodeError):
        old_id = "vechi"
    dest = plan_dir / "history" / old_id
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("plan.json", "audit.jsonl", "run.json", "report.md", "overrides.json"):
        if (plan_dir / name).exists():
            shutil.move(str(plan_dir / name), dest / name)
    history = sorted((plan_dir / "history").iterdir(), key=lambda p: p.stat().st_mtime)
    for old in history[:-5]:  # păstrăm doar ultimele 5 planuri
        shutil.rmtree(old, ignore_errors=True)


def run(
    scenario: str = "demo-vara",
    date: str | Date | None = None,
    *,
    mode: Mode = "auto",
    out_root: Path = OUTPUTS,
    settings: Settings | None = None,
    as_of: datetime | None = None,
    solver: str | None = None,
) -> RunResult:
    """Rulează agentul cap-coadă și scrie rezultatele în <out_root>/plans/<scenariu>/."""
    timings: dict[str, float] = {}
    t0 = time.perf_counter()
    settings = settings or Settings.load()
    sc = settings.scenarios.get(scenario) or Scenario(scenario, scenario, None, None)
    # În modul fixtures, data vine din exemple (nu din scenariu), ca exemplele să nu fie respinse pe dată.
    plan_date = _fixture_date() if (mode == "fixtures" and date is None) else sc.resolve_date(date)
    if plan_date is None:  # data scenariului nu e încă aleasă: o luăm din ieșirile existente sau din fixture-uri
        existing = [_work_items_file(out_root, scenario, s) for s in "ABC"] if mode != "fixtures" else []
        plan_date = infer_plan_date(existing) or _fixture_date()
    if plan_date is None:
        raise SystemExit(f"Nu știu data planului pentru scenariul {scenario!r}: dă --date YYYY-MM-DD.")
    timings["perceive"] = round(time.perf_counter() - t0, 3)

    t1 = time.perf_counter()
    picks = estimate(scenario, plan_date, mode, out_root)
    fixture_date = _fixture_date()
    if mode == "auto" and date is None and fixture_date and fixture_date != plan_date and all(p.origin == "missing" for p in picks.values()):
        # Niciun model nu are încă ieșiri pentru data scenariului: planul rulează pe exemple, marcat clar (surse "degraded").
        note = f"nicio ieșire de model pentru {plan_date.isoformat()}; plan pe exemplele din contracts/fixtures/ ({fixture_date.isoformat()})"
        plan_date = fixture_date
        picks = estimate(scenario, plan_date, "fixtures", out_root)
        for pick in picks.values():
            pick.note = f"{note}; {pick.note}"
    timings["estimate"] = round(time.perf_counter() - t1, 3)

    plan_dir = out_root / "plans" / scenario
    inputs_dir = plan_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    loads: dict[str, SourceLoad] = {}
    t2 = time.perf_counter()
    for s in "ABC":
        pick = picks[s]
        snap = inputs_dir / f"{s}.jsonl"
        if pick.path is not None and pick.path.exists():
            shutil.copyfile(pick.path, snap)  # copia exactă a intrărilor, pentru replanificare și jurnal
        elif snap.exists():
            snap.unlink()
        load = load_source(s, snap if pick.path else None, pick.origin, plan_date, seen)
        load.note = pick.note if not load.note else f"{pick.note}; {load.note}"
        finalize_status(load, settings)
        loads[s] = load
    ingest_s = time.perf_counter() - t2
    meta = {
        "mode": mode,
        "sources": {
            s: {"origin": loads[s].origin, "status": loads[s].status, "note": loads[s].note, "valid": len(loads[s].items),
                "invalid": len(loads[s].quarantined), "path": str(picks[s].path) if picks[s].path else None, "seconds": round(picks[s].seconds, 3)}
            for s in "ABC"
        },
    }
    result = _decide_and_act(
        settings=settings, scenario=scenario, plan_date=plan_date, loads=loads, as_of=as_of, plan_dir=plan_dir,
        timings=timings, meta=meta, append_audit=False, solver=solver,
    )
    result.timings["decide"] = round(result.timings["decide"] + ingest_s, 3)
    result.meta["timings"] = result.timings
    write_json(plan_dir / "run.json", result.meta)
    return result


def replan(scenario: str, *, out_root: Path = OUTPUTS, settings: Settings | None = None) -> RunResult:
    """Recalculează planul din intrările salvate, cu deciziile omului (overrides.json). Jurnalul se continuă."""
    settings = settings or Settings.load()
    plan_dir = out_root / "plans" / scenario
    meta_path = plan_dir / "run.json"
    if not meta_path.exists():
        raise KeyError(f"nu există o rulare a agentului pentru scenariul {scenario!r}; rulează întâi `cyberpunks run`")
    old = json.loads(meta_path.read_text(encoding="utf-8"))
    plan_date = Date.fromisoformat(old["plan_date"])
    as_of = datetime.fromisoformat(old["as_of"])
    t0 = time.perf_counter()
    seen: set[str] = set()
    loads: dict[str, SourceLoad] = {}
    for s in "ABC":
        info = old["sources"][s]
        snap = plan_dir / "inputs" / f"{s}.jsonl"
        load = load_source(s, snap if snap.exists() else None, info["origin"], plan_date, seen)
        load.note = info.get("note", "")
        finalize_status(load, settings)
        loads[s] = load
    timings = {"perceive": 0.0, "estimate": 0.0}
    meta = {"mode": "replan", "sources": old["sources"]}
    result = _decide_and_act(
        settings=settings, scenario=scenario, plan_date=plan_date, loads=loads, as_of=as_of, plan_dir=plan_dir,
        timings=timings, meta=meta, append_audit=True, solver=None,
    )
    result.timings["replan_total"] = round(time.perf_counter() - t0, 3)
    return result
