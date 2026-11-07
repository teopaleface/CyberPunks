"""Act: din propuneri și trasee → decizii finale, plan, jurnal, alerte, notificări, fișiere.

Fiecare decizie are un AuditRecord cu ID-ul predicției, versiunea modelului, regula, pragurile și amprenta
SHA-256 a liniei primite. Așa orice acțiune se urmărește până la predicția care a produs-o.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from cyberpunks.common.contracts import (
    Alert,
    AuditRecord,
    Decision,
    DecisionType,
    Notification,
    Plan,
    PlanSummary,
    Route,
    Stop,
)
from cyberpunks.planner.decide import AlertSpec, Context, NotificationSpec, Proposal, _final
from cyberpunks.planner.ingest import Quarantined, SourceLoad
from cyberpunks.planner.routing import RoutingResult, at_minutes
from cyberpunks.planner.settings import TZ
from cyberpunks.planner.texts import SOURCE_RO, hhmm, lei

DROP_RULES = {
    "capacity": ("R-CAPACITY", "Nu a mai încăput în turele de mâine (prioritate {prio}); rămâne pentru planul următor."),
    "time_window": ("R-TIME-WINDOW", "Nicio echipă potrivită nu poate ajunge la timp (sosirea trebuie să fie până la {latest})."),
    "no_crew": ("R-NO-CREW", "Nicio echipă cu abilitatea cerută."),
    "not_worth": ("R-NOT-WORTH-TRIP", "Drumul dus-întors al unei echipe costă mai mult decât valoarea netă a lucrării ({prio}); fără deplasare dedicată."),
}
DROP_PREFIX = {
    "not_worth": "Drumul dus-întors al unei echipe costă mai mult decât valoarea netă a lucrării.",
    "capacity": "Echipele potrivite sunt pline mâine.",
    "time_window": "Nicio echipă potrivită nu poate ajunge la timp.",
    "no_crew": "Nicio echipă cu abilitatea cerută.",
}


@dataclass
class Outcome:
    decisions: list[Decision]
    audit: list[AuditRecord]
    alerts: list[Alert]
    notifications: list[Notification]
    routes: list[Route]
    final: dict[str, Proposal] = field(default_factory=dict)


def _f(d: dict[str, Any]) -> dict[str, float]:
    out = {}
    for k, v in d.items():
        if isinstance(v, bool):
            out[k] = 1.0 if v else 0.0
        elif isinstance(v, (int, float)):
            out[k] = float(v)
    return out


def _uid() -> str:
    return str(uuid.uuid4())


def finalize(
    ctx: Context,
    proposals: list[Proposal],
    routing: RoutingResult,
    loads: dict[str, SourceLoad],
    generated_at: datetime,
) -> Outcome:
    plan_date = ctx.plan_date
    by_id = {p.id: p for p in proposals}
    route_ranked = sorted([p for p in proposals if p.route], key=lambda p: (not p.mandatory, -(p.priority or 0.0)))
    rank_of = {p.id: i for i, p in enumerate(route_ranked, 1)}

    # ---- 1. decizia finală pentru fiecare propunere
    final: dict[str, Proposal] = {}
    eta_of: dict[str, datetime] = {}
    for r in routing.routes:
        for s in r.stops:
            eta_of[s.task_id] = at_minutes(s.arrival_min, plan_date)
    for p in proposals:
        if not p.route:
            final[p.id] = p
            continue
        if p.id in routing.assigned:
            crew, seq = routing.assigned[p.id]
            p.reason_ro = f"{p.reason_ro} Echipa {crew}, oprirea {seq}, sosire la {hhmm(eta_of[p.id])}."
            final[p.id] = p
            continue
        why = routing.dropped.get(p.id, "capacity")
        if p.mandatory:
            final[p.id] = _final(
                p.item, DecisionType.human_review, "R-SAFETY-NO-CREW",
                f"{p.reason_ro} Nicio echipă potrivită nu poate ajunge mâine: decide dispecerul azi (de exemplu ore suplimentare).",
                p.action, p.threshold, alerts=p.alerts + [AlertSpec("critical", f"Caz fără echipă: {p.wi.location.label or p.wi.asset_id}", "Lucrare obligatorie (siguranță sau aprobată de om) care nu încape în turele de mâine.")],
                priority=p.priority,
            )
            continue
        if p.fallback is not None:
            fb = p.fallback
            fb.priority = p.priority
            fb.alerts = p.alerts + fb.alerts
            if why != "capacity":
                fb.reason_ro = f"{DROP_PREFIX.get(why, '')} {fb.reason_ro}".strip()
            final[p.id] = fb
            continue
        rule_id, tmpl = DROP_RULES.get(why, DROP_RULES["capacity"])
        if why == "time_window" and p.action == "preposition_crew":
            rule_id = "R-B-TOO-LATE"
        latest = hhmm(p.latest.astimezone(TZ)) if p.latest else "-"
        final[p.id] = _final(
            p.item, DecisionType.deferred, rule_id,
            f"{p.reason_ro} {tmpl.format(prio=lei(p.priority or 0), latest=latest)}",
            p.action, p.threshold, alerts=p.alerts, notifications=p.notifications, priority=p.priority,
        )

    # ---- 2. decizii, jurnal, alerte, notificări
    decisions: list[Decision] = []
    audit: list[AuditRecord] = []
    alerts: list[Alert] = []
    notifications: list[Notification] = []

    def add_alert(spec: AlertSpec, ids: list[str]) -> None:
        alerts.append(
            Alert(alert_id=f"AL-{len(alerts) + 1}", severity=spec.severity, title_ro=spec.title_ro, body_ro=spec.body_ro,
                  work_item_ids=ids, channel=spec.channel, created_at=generated_at)
        )

    def add_notification(spec: NotificationSpec, asset_id: str, wid: str | None) -> None:
        notifications.append(
            Notification(notification_id=f"N-{len(notifications) + 1}", audience=spec.audience, asset_id=asset_id,
                         message_ro=spec.message_ro, scheduled_for=spec.scheduled_for, work_item_id=wid, demo_only=True)
        )

    order = sorted(final.values(), key=lambda p: (rank_of.get(p.id, 10**6), -(p.wi.impact.expected_value_lei)))
    for p in order:
        wi = p.wi
        aid = _uid()
        crew = routing.assigned.get(p.id, (None, None))[0] if p.decision == DecisionType.assigned else None
        decisions.append(
            Decision(
                work_item_id=p.id, decision=p.decision, reason_ro=p.reason_ro, rule_id=p.rule_id, threshold=_f(p.threshold),
                priority_score=p.priority if p.priority is not None else (by_id[p.id].priority if by_id.get(p.id) else None),
                rank=rank_of.get(p.id), crew_id=crew, audit_id=aid,
            )
        )
        audit.append(
            AuditRecord(
                audit_id=aid, ts=generated_at, actor="agent", action=p.decision.value, work_item_id=p.id,
                prediction_id=wi.prediction.prediction_id, model_version=wi.prediction.model_version, rule_id=p.rule_id,
                threshold=_f(p.threshold), inputs_sha256=p.item.sha256, note=p.reason_ro,
            )
        )
        for spec in p.alerts:
            add_alert(spec, [p.id])
        for spec in p.notifications:
            add_notification(spec, wi.asset_id, p.id)
        if p.decision == DecisionType.assigned and p.action == "preposition_crew" and crew:
            eta = eta_of.get(p.id)
            start = wi.time_window.start if wi.time_window else None
            msg = (
                f"Mâine, echipa {crew}: fiți în {wi.location.label or wi.asset_id} la {hhmm(eta) if eta else '-'}"
                + (f", înainte de {hhmm(start)}, când începe fereastra de risc" if start else "")
                + ". Rămâneți în zonă până la ridicarea alertei; materialele pentru linii aeriene în mașină."
            )
            add_notification(NotificationSpec("echipa", msg, generated_at + timedelta(minutes=1)), wi.asset_id, p.id)

    # ---- 3. carantina
    for load in loads.values():
        for q in load.quarantined:
            aid = _uid()
            decisions.append(
                Decision(work_item_id=q.work_item_id, decision=DecisionType.rejected_invalid,
                         reason_ro="Intrare greșită, pusă în carantină: " + "; ".join(q.errors), rule_id="R-QUARANTINE",
                         threshold={}, audit_id=aid)
            )
            pred = (q.raw.get("prediction") or {}) if isinstance(q.raw, dict) else {}
            audit.append(
                AuditRecord(audit_id=aid, ts=generated_at, actor="agent", action="rejected_invalid", work_item_id=q.work_item_id,
                            prediction_id=pred.get("prediction_id") if isinstance(pred.get("prediction_id"), str) else None,
                            model_version=pred.get("model_version") if isinstance(pred.get("model_version"), str) else None,
                            rule_id="R-QUARANTINE", inputs_sha256=q.sha256, note="; ".join(q.errors))
            )

    # ---- 4. alerte de ansamblu
    _global_alerts(ctx, final, loads, routing, add_alert)

    # ---- 5. trasee în formatul contractului
    routes = []
    for r in routing.routes:
        routes.append(
            Route(
                crew_id=r.vehicle.crew.crew_id, depot_id=r.vehicle.depot.depot_id,
                stops=[Stop(seq=s.seq, work_item_id=s.task_id, eta=at_minutes(s.arrival_min, plan_date), duration_min=max(1, s.display_min), travel_km=s.travel_km) for s in r.stops],
                total_km=r.total_km, total_work_min=r.total_work_min, total_travel_min=round(r.total_travel_min),
            )
        )
    return Outcome(decisions, audit, alerts, notifications, routes, final)


def _global_alerts(ctx: Context, final: dict[str, Proposal], loads: dict[str, SourceLoad], routing: RoutingResult, add_alert) -> None:
    for src, load in loads.items():
        if load.status == "missing":
            add_alert(AlertSpec("warning", f"Sursa {src} ({SOURCE_RO[src]}) lipsește", f"Planul merge mai departe fără ea ({load.note or 'nicio lucrare'})."), [])
        elif load.status == "degraded":
            why = {"fixture": "date de test (fixture), nu ieșirea modelului", "stale": "o ieșire mai veche a modelului"}.get(load.origin, "")
            bad = f"{len(load.quarantined)} linii respinse din {len(load.items) + len(load.quarantined)}" if load.quarantined else ""
            add_alert(AlertSpec("warning", f"Sursa {src} ({SOURCE_RO[src]}) e incompletă", ", ".join(x for x in (why, bad, load.note) if x) + "."), [])
    invalid = [q.work_item_id for load in loads.values() for q in load.quarantined]
    if invalid:
        add_alert(AlertSpec("warning", f"{len(invalid)} intrări greșite în carantină", "Nu intră în plan; motivele sunt în jurnal și în lista de carantină."), invalid)
    review = [p for p in final.values() if p.decision == DecisionType.human_review]
    if review:
        total = sum(p.wi.impact.expected_value_lei for p in review)
        add_alert(AlertSpec("info", f"{len(review)} lucrări așteaptă decizia unui om", f"Valoare așteptată totală {lei(total)}. Aprobă, respinge sau amână din consolă."), [p.id for p in review])
    cap = [p for p in final.values() if p.rule_id in ("R-CAPACITY", "R-CAPACITY-REMOTE")]
    if cap:
        total = sum(p.wi.impact.expected_value_lei for p in cap)
        add_alert(AlertSpec("warning", f"{len(cap)} lucrări n-au încăput în turele de mâine", f"Valoare așteptată {lei(total)}. Ce s-a putut, trece pe citire la distanță; restul rămâne pentru planul următor."), [p.id for p in cap])
    if routing.status.startswith("FALLBACK"):
        add_alert(AlertSpec("warning", "Optimizatorul a folosit metoda de rezervă", routing.status), [])


def build_plan(
    ctx: Context, scenario: str, plan_id: str, planner_version: str, generated_at: datetime, outcome: Outcome, loads: dict[str, SourceLoad]
) -> Plan:
    counts: dict[DecisionType, int] = {}
    for d in outcome.decisions:
        counts[d.decision] = counts.get(d.decision, 0) + 1
    valid = sum(len(load.items) for load in loads.values())
    invalid = sum(len(load.quarantined) for load in loads.values())
    assigned_ev = sum(p.wi.impact.expected_value_lei for p in outcome.final.values() if p.decision == DecisionType.assigned)
    summary = PlanSummary(
        items_in=valid + invalid, items_valid=valid, items_invalid=invalid,
        assigned=counts.get(DecisionType.assigned, 0), deferred=counts.get(DecisionType.deferred, 0),
        human_review=counts.get(DecisionType.human_review, 0), remote_actions=counts.get(DecisionType.remote_action, 0),
        notifications=len(outcome.notifications), crews_used=len(outcome.routes),
        expected_value_lei=round(assigned_ev, 2), total_km=round(sum(r.total_km for r in outcome.routes), 2),
    )
    return Plan(
        plan_id=plan_id, plan_date=ctx.plan_date, generated_at=generated_at, planner_version=planner_version, scenario=scenario,
        summary=summary, routes=outcome.routes, decisions=outcome.decisions, alerts=outcome.alerts,
        notifications=outcome.notifications, sources_status={s: loads[s].status for s in "ABC"},
    )


# ------------------------------------------------------------------ scrierea fișierelor


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def write_jsonl(path: Path, rows: list[Any], append: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    if append and path.exists():
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(text)
        return
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def quarantine_rows(loads: dict[str, SourceLoad]) -> list[dict[str, Any]]:
    rows: list[Quarantined] = [q for load in loads.values() for q in load.quarantined]
    return [q.to_json() for q in rows]
