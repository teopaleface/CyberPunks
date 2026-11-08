"""Agentul cap-coadă: Perceive → Estimate → Decide → Act, fără intervenție manuală între pași.

    uv run cyberpunks run --scenario demo-vara

- Perceive: configurația (echipe, baze, praguri, ipoteze), scenariul și data, ce date și modele există.
- Estimate: modelele noastre A, B, C (`cyberpunks.<fir>.predict.run(scenario, date)`). Dacă un model lipsește
  sau dă eroare, se folosește ultima lui ieșire pentru aceeași zi; altfel sursa e „lipsă”, cu motivul (exemplele din
  contracts/fixtures/ se folosesc doar în modul fixtures, cerut explicit).
- Decide: validarea (carantina), regulile cu prag (decide.py), traseele (routing.py).
- Act: planul, jurnalul, alertele, notificările, raportul și ordinele de lucru, în outputs/plans/<scenariu>/.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import shutil
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import date as Date
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import ValidationError

from cyberpunks.common.contracts import Alert, AuditRecord, BilantFusion, Plan, Source, WorkItem
from cyberpunks.common.paths import CONTRACTS, OUTPUTS
from cyberpunks.planner import planner_version
from cyberpunks.planner.actions import build_plan, finalize, quarantine_rows, write_json, write_jsonl
from cyberpunks.planner.decide import Context, Override, decide
from cyberpunks.planner.ingest import (
    Item,
    Origin,
    SourceLoad,
    finalize_status,
    infer_plan_date,
    load_source,
    semantic_errors,
)
from cyberpunks.planner.routing import Task, Vehicle, build_problem, minutes_of, solve
from cyberpunks.planner.settings import TZ, Scenario, Settings

# Fișierele de lucrări: A_bilant are tot sursa A (bilanțul pe post), în fișierul lui; sources_status["A"] le acoperă pe amândouă.
PREDICTORS = {
    "A": "cyberpunks.a_contoare.predict",
    "A_bilant": "cyberpunks.a_bilant.predict",
    "B": "cyberpunks.b_furtuna.predict",
    "C": "cyberpunks.c_prosumatori.predict",
}
SOURCE_OF = {"A": "A", "A_bilant": "A", "B": "B", "C": "C"}
OPTIONAL = {"A_bilant"}  # dacă modulul nu există încă, lipsa lui nu strică starea sursei A
FIXTURES = {k: CONTRACTS / "fixtures" / f"work_items_{k}.jsonl" for k in PREDICTORS}
FUSION_MODULE = "cyberpunks.a_bilant.fuse"
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


def _fresh_output(path: Path, plan_date: Date | None, max_age_hours: float) -> bool:
    """O ieșire existentă e refolosibilă dacă e pentru aceeași zi și nu e mai veche de `max_age_hours`."""
    if plan_date is None or not path.exists():
        return False
    if time.time() - path.stat().st_mtime > max_age_hours * 3600:
        return False
    return infer_plan_date([path]) == plan_date


def estimate(scenario: str, plan_date: Date | None, mode: Mode, out_root: Path, settings: Settings | None = None) -> dict[str, SourcePick]:
    picks: dict[str, SourcePick] = {}
    fixture_date = _fixture_date()
    settings = settings or Settings.load()
    sc = settings.scenarios.get(scenario)
    sc_fixed_date = bool(sc and sc.date_spec and sc.date_spec[:1].isdigit())
    slow = set(settings.rule("estimate", "reuse_fresh_output", default=[]) or [])
    max_age = float(settings.rule("estimate", "max_age_hours", default=12))
    for src, module in PREDICTORS.items():
        existing = _work_items_file(out_root, scenario, src)
        t0 = time.perf_counter()
        note = ""
        historical = sc_fixed_date and plan_date is not None  # zi istorică: aceleași intrări, ieșirea nu se învechește
        if mode == "auto" and src in slow and _fresh_output(existing, plan_date, float("inf") if historical else max_age):
            # Model lent (de exemplu bilanțul, ~4 minute): ieșirea lui pentru aceeași zi, din ultimele ore, se refolosește.
            ran_at = datetime.fromtimestamp(existing.stat().st_mtime, TZ).strftime("%H:%M")
            picks[src] = SourcePick(existing, "model", f"ieșirea modelului {src} pentru aceeași zi, rulată la {ran_at} (model lent, refolosit)",
                                    time.perf_counter() - t0)
            continue
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
                except (Exception, SystemExit) as exc:  # noqa: BLE001 - un model căzut (chiar cu SystemExit) nu oprește planul
                    note = f"modelul {src} a dat eroare: {type(exc).__name__}: {str(exc)[:200]}"
        if mode != "fixtures" and existing.exists():
            existing_date = infer_plan_date([existing])
            if mode == "auto" and plan_date is not None and existing_date is not None and existing_date != plan_date:
                # Ieșirea veche (rezerva unui model căzut) e pentru altă zi: lucrările ei ar ajunge toate în carantină.
                # Sursa e lipsă, cu motivul. În modul `existing`, fișierul dat se citește oricum (verificarea datelor greșite).
                why = f"ieșirea existentă a modelului e pentru {existing_date.isoformat()}, nu pentru {plan_date.isoformat()}"
                picks[src] = SourcePick(None, "missing", (note + "; " if note else "") + why, time.perf_counter() - t0)
                continue
            origin: Origin = "stale" if note and "eroare" in note else "model"
            picks[src] = SourcePick(existing, origin, note or "ieșirea existentă a modelului", time.perf_counter() - t0)
            continue
        if mode == "fixtures" and FIXTURES[src].exists() and (plan_date is None or plan_date == fixture_date):
            # Doar în modul fixtures, cerut explicit (teste, dezvoltarea interfeței): exemplele nu țin locul unui model căzut.
            picks[src] = SourcePick(FIXTURES[src], "fixture", "exemple din contracts/fixtures/ (mod fixtures, cerut explicit)", time.perf_counter() - t0)
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
        required = p.skills_required or frozenset({p.skill or wi.effort.crew_skill.value})
        skill = "+".join(sorted(required))
        size = p.crew_size or wi.effort.crew_size
        duration = p.duration_min or wi.effort.duration_min
        allowed = [v for v, veh in enumerate(vehicles) if required <= veh.crew.skills and veh.crew.size >= size]
        tasks.append(
            Task(
                id=p.id, lat=wi.location.lat, lon=wi.location.lon,
                service_min=0 if p.terminal else duration, display_min=duration,
                skill=skill, crew_size=size,
                earliest=minutes_of(p.earliest, ctx.plan_date), latest=minutes_of(p.latest, ctx.plan_date),
                terminal=p.terminal, penalty=round((p.priority or 0.0) * scale), mandatory=p.mandatory, allowed=allowed,
            )
        )
    return build_problem(tasks, vehicles, ctx.travel, scale)


def _unique_quarantine_ids(loads: dict[str, SourceLoad]) -> None:
    """Fiecare decizie are un ID unic: o linie respinsă nu ia ID-ul unei lucrări valide sau al altei linii respinse,
    nici din alt fișier (A.jsonl și A_bilant.jsonl au aceeași sursă)."""
    used = {it.id for load in loads.values() for it in load.items}
    for key, load in loads.items():
        for q in load.quarantined:
            qid = q.work_item_id
            if qid in used:
                base = qid.split("~", 1)[0]
                qid = f"{base}~{key}-linia{q.line}"
                n = 2
                while qid in used:
                    qid, n = f"{base}~{key}-linia{q.line}-{n}", n + 1
            q.work_item_id = qid
            used.add(qid)


def replay_fusion(items: list[Item], path: Path) -> tuple[list[Item], list[tuple[Item, BilantFusion]], dict[str, Any]]:
    """Fuziunea salvată la rulare, aplicată din nou la replanificare (aceleași intrări → aceleași decizii)."""
    saved = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            saved[row["work_item_id"]] = row
    out, events = [], []
    for it in items:
        row = saved.get(it.id)
        if row is None or row.get("sha256") != it.sha256:
            out.append(it)
            continue
        fused = Item(WorkItem.model_validate(row["item"]), it.sha256, it.line_no, it.origin)
        out.append(fused)
        events.append((fused, BilantFusion.model_validate(row["fusion"])))
    return out, events, {"status": "ok (reluată din rulare)", "fused": len(events), "rejected": 0}


def _module_available(name: str) -> bool:
    if name in sys.modules:
        return True
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


# ------------------------------------------------------------------ fuziunea cu bilanțul pe post


def apply_fusion(items: list[Item], scenario: str, plan_date: Date) -> tuple[list[Item], list[tuple[Item, BilantFusion]], dict[str, Any]]:
    """Aplică `cyberpunks.a_bilant.fuse.fuse` pe lucrările A, dacă modulul există. O lucrare fuzionată se păstrează doar
    dacă trece contractul, verificările de sens și are `extra["fusion"]` valid; altfel rămâne lucrarea originală."""
    a_items = [it for it in items if it.wi.source == Source.A]
    if not a_items:
        return items, [], {"status": "fără lucrări A"}
    try:
        mod = importlib.import_module(FUSION_MODULE)
        fuse = mod.fuse
    except (ImportError, AttributeError):
        return items, [], {"status": "indisponibilă (modulul bilanțului nu există încă)"}
    try:
        fused_raw = fuse([it.wi for it in a_items], scenario, plan_date.isoformat())
    except Exception as exc:  # noqa: BLE001 - fuziunea căzută nu oprește planul
        return items, [], {"status": "eroare", "note": f"{type(exc).__name__}: {str(exc)[:200]}"}
    fused: dict[str, WorkItem] = {}
    rejected = 0
    for w in fused_raw or []:
        try:
            wi = w if isinstance(w, WorkItem) else WorkItem.model_validate(w)
        except ValidationError:
            rejected += 1
            continue
        fused[wi.work_item_id] = wi
    out: list[Item] = []
    events: list[tuple[Item, BilantFusion]] = []
    for it in items:
        new = fused.get(it.id) if it.wi.source == Source.A else None
        raw_f = new.extra.get("fusion") if new is not None else None
        if new is None or raw_f is None:
            out.append(it)
            continue
        try:
            fusion = BilantFusion.model_validate(raw_f)
        except ValidationError:
            rejected += 1
            out.append(it)
            continue
        if semantic_errors(new, plan_date) or new.source != it.wi.source or new.asset_id != it.wi.asset_id:
            rejected += 1
            out.append(it)
            continue
        fused_item = Item(new, it.sha256, it.line_no, it.origin)
        out.append(fused_item)
        events.append((fused_item, fusion))
    return out, events, {"status": "ok", "fused": len(events), "rejected": rejected}


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
    _unique_quarantine_ids(loads)
    items = [it for key in loads for it in loads[key].items]
    plan_dir.mkdir(parents=True, exist_ok=True)
    if append_audit and (plan_dir / "fusion.jsonl").exists():
        items, fusion_events, fusion_meta = replay_fusion(items, plan_dir / "fusion.jsonl")  # replanificarea refolosește fuziunea rulării
    else:
        items, fusion_events, fusion_meta = apply_fusion(items, scenario, plan_date)
        write_jsonl(plan_dir / "fusion.jsonl", [{"work_item_id": it.id, "sha256": it.sha256, "item": it.wi.model_dump(mode="json"),
                                                 "fusion": f.model_dump(mode="json")} for it, f in fusion_events])
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
    plan_id = f"PLAN-{scenario}-{plan_date:%Y%m%d}-{generated_at:%H%M%S}-{uuid.uuid4().hex[:4]}"
    plan = build_plan(ctx, scenario, plan_id, planner_version(), generated_at, outcome, loads)

    plan_dir.mkdir(parents=True, exist_ok=True)
    if not append_audit and (plan_dir / "plan.json").exists():
        _archive(plan_dir)
    run_record = AuditRecord(
        audit_id=f"run-{plan_id}", ts=generated_at, actor="agent", action="replan" if append_audit else "run",
        rule_id=None, note=(
            f"scenariu {scenario}, data {plan_date.isoformat()}, surse "
            + ", ".join(f"{k}={loads[k].status}/{loads[k].origin}" for k in loads)
            + f"; solver {rr.solver} ({rr.status}, {rr.solve_seconds:.2f} s)"
        ),
    )
    fusion_rows = [
        AuditRecord(
            audit_id=str(uuid.uuid4()), ts=generated_at, actor="agent", action="fusion", work_item_id=it.id,
            prediction_id=it.wi.prediction.prediction_id, model_version=it.wi.prediction.model_version, rule_id="R-FUSION-BILANT",
            threshold={"a_score": f.a_score, "combined_score": f.combined_score, "post_excess_loss_lei_month": f.post_excess_loss_lei_month,
                       "post_excess_loss_kwh_day": f.post_excess_loss_kwh_day},
            inputs_sha256=it.sha256, note=f"{f.note_ro} (postul {f.post_id}, predicția bilanțului {f.bilant_prediction_id})",
        ).model_dump(mode="json")
        for it, f in fusion_events
    ]
    from cyberpunks.planner.context import day_context

    try:
        context_lines = day_context(ctx, outcome.final, meta.get("sources") or {})
    except Exception as exc:  # noqa: BLE001 - contextul e doar informativ; nu are voie să oprească planul
        context_lines = [f"Contextul zilei nu s-a putut calcula ({type(exc).__name__}); planul nu e afectat."]
    if context_lines:
        plan.alerts.append(Alert(alert_id=f"AL-{len(plan.alerts) + 1}", severity="info", title_ro="Contextul zilei",
                                 body_ro=" ".join(context_lines), channel="dispecerat", created_at=generated_at))
    meta["day_context"] = context_lines
    if fusion_meta.get("status") == "eroare":
        plan.alerts.append(Alert(alert_id=f"AL-{len(plan.alerts) + 1}", severity="warning", title_ro="Fuziunea cu bilanțul n-a mers",
                                 body_ro=f"Planul folosește scorurile A fără confirmarea bilanțului ({fusion_meta.get('note', '')}).",
                                 channel="dispecerat", created_at=generated_at))
    audit_rows = [run_record.model_dump(mode="json")] + fusion_rows + [a.model_dump(mode="json") for a in outcome.audit]
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
            "fusion": fusion_meta,
            "dispatch": ctx.dispatch,
            "remedies": [p.ladder for p in outcome.final.values() if p.ladder],
        }
    )
    write_json(plan_dir / "remedies.json", meta["remedies"])
    from cyberpunks.planner.posts import overview as posts_overview

    write_json(plan_dir / "posts.json", posts_overview(plan.model_dump(mode="json"), [it.wi.model_dump(mode="json") for it in items], settings))
    # Acțiunea fiecărei lucrări; la scara C, toate treptele cu echipă alese (de exemplu "phase_rebalance+adjust_tap").
    actions = {
        wid: ("+".join(p.ladder["crew_steps"]) if p.ladder and p.ladder.get("crew_steps") and p.decision.value == "assigned" else p.action)
        for wid, p in outcome.final.items()
    }
    write_json(plan_dir / "actions.json", actions)
    # Titlul deciziei, acolo unde tipul ei singur ar înșela (scara C: „mesaj către clienți” pentru o soluție în trei pași).
    write_json(plan_dir / "titles.json", {wid: p.ladder["title_ro"] for wid, p in outcome.final.items() if p.ladder and p.ladder.get("title_ro")})
    try:
        from cyberpunks.planner.workorders import write_work_orders

        meta["work_orders"] = [p.name for p in write_work_orders(plan, items, plan_dir, settings, actions=actions)]
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
    picks = estimate(scenario, plan_date, mode, out_root, settings)
    # Un model care nu poate da rezultate pentru ziua planului rămâne „lipsă”, cu motivul; exemplele de test nu îi iau locul.
    timings["estimate"] = round(time.perf_counter() - t1, 3)

    plan_dir = out_root / "plans" / scenario
    inputs_dir = plan_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    loads: dict[str, SourceLoad] = {}
    t2 = time.perf_counter()
    for key in PREDICTORS:
        pick = picks[key]
        snap = inputs_dir / f"{key}.jsonl"
        if pick.path is not None and pick.path.exists():
            shutil.copyfile(pick.path, snap)  # copia exactă a intrărilor, pentru replanificare și jurnal
        elif snap.exists():
            snap.unlink()
        load = load_source(SOURCE_OF[key], snap if pick.path else None, pick.origin, plan_date, seen)
        load.note = pick.note if not load.note else f"{pick.note}; {load.note}"
        finalize_status(load, settings)
        # Bilanțul e o completare: dacă lipsește ieșirea lui (modul absent sau încă nerulat), starea sursei A nu se strică.
        load.optional = key in OPTIONAL and load.origin == "missing"
        loads[key] = load
    ingest_s = time.perf_counter() - t2
    meta = {
        "mode": mode,
        "sources": {
            k: {"origin": loads[k].origin, "status": loads[k].status, "note": loads[k].note, "valid": len(loads[k].items),
                "invalid": len(loads[k].quarantined), "path": str(picks[k].path) if picks[k].path else None,
                "seconds": round(picks[k].seconds, 3), "optional": loads[k].optional}
            for k in PREDICTORS
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
    for key, info in old["sources"].items():
        snap = plan_dir / "inputs" / f"{key}.jsonl"
        load = load_source(SOURCE_OF.get(key, key[0]), snap if snap.exists() else None, info["origin"], plan_date, seen)
        load.note = info.get("note", "")
        finalize_status(load, settings)
        load.optional = bool(info.get("optional", False))
        loads[key] = load
    timings = {"perceive": 0.0, "estimate": 0.0}
    meta = {"mode": "replan", "sources": old["sources"]}
    result = _decide_and_act(
        settings=settings, scenario=scenario, plan_date=plan_date, loads=loads, as_of=as_of, plan_dir=plan_dir,
        timings=timings, meta=meta, append_audit=True, solver=None,
    )
    result.timings["replan_total"] = round(time.perf_counter() - t0, 3)
    return result
