"""Stratul de decizie: reguli scrise în cod, cu nume (`rule_id`) și cu pragurile scrise în fiecare decizie.

Pentru fiecare lucrare validă se evaluează regulile în ordine; prima care se potrivește decide.
Rezultatul e o propunere: fie o decizie finală (om, citire la distanță, mesaj, amânare), fie o candidatură
pentru traseele echipelor. Candidaturile le împarte apoi optimizatorul (routing.py) pe echipe; ce nu
încape primește o decizie de rezervă (de exemplu citire la distanță în loc de vizită).

Costul unei acțiuni: costul acțiunii (config/economics.yaml) + deplasarea estimată de la cea mai apropiată bază
cu o echipă potrivită + costul social al unei întreruperi planificate (doar la schimbarea prizei).
Valoarea netă = expected_value_lei − cost (pragul: o echipă merge doar dacă e pozitivă).
Prioritatea (premiul în trasee) = expected_value_lei − costul acțiunii (× 3 la siguranță); drumul îl socotește solverul.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

from pydantic import ValidationError

from cyberpunks.common.contracts import (
    AssetType,
    Confidence,
    DecisionType,
    RecommendedAction,
    RemedyOption,
    Source,
    WorkItem,
)
from cyberpunks.planner.geo import TravelModel
from cyberpunks.planner.ingest import Item
from cyberpunks.planner.settings import TZ, Crew, Settings
from cyberpunks.planner.texts import ACTION_RO, SKILL_RO, hhmm, lei, num, pct, zi

CREW_ACTIONS = {"inspect_on_site", "preposition_crew", "adjust_tap", "measurement_campaign", "grid_inspection", "phase_rebalance"}


# ------------------------------------------------------------------ ce produce stratul de decizie


@dataclass
class AlertSpec:
    severity: str  # info | warning | critical
    title_ro: str
    body_ro: str
    channel: str = "dispecerat"


@dataclass
class NotificationSpec:
    audience: str  # prosumatori | clienti_zona | echipa
    message_ro: str
    scheduled_for: datetime


@dataclass
class Costs:
    action: str
    action_cost: float = 0.0
    travel_km: float = 0.0
    travel_min: float = 0.0
    travel_cost: float = 0.0
    outage_cost: float = 0.0
    depot_id: str | None = None

    @property
    def total(self) -> float:
        return self.action_cost + self.travel_cost + self.outage_cost

    def explain(self) -> str:
        parts = [f"{ACTION_RO.get(self.action, self.action)} {lei(self.action_cost)}"]
        if self.travel_cost:
            parts.append(f"deplasare ~{num(self.travel_km, 1)} km {lei(self.travel_cost)}")
        if self.outage_cost:
            parts.append(f"întreruperea planificată {lei(self.outage_cost)}")
        return " + ".join(parts)


@dataclass
class Proposal:
    item: Item
    decision: DecisionType
    rule_id: str
    reason_ro: str
    action: str
    threshold: dict[str, float] = field(default_factory=dict)
    costs: Costs | None = None
    priority: float | None = None
    route: bool = False  # candidat pentru traseele echipelor
    mandatory: bool = False  # siguranță: nu se lasă afară dacă există o echipă potrivită
    earliest: datetime | None = None  # sosirea cel mai devreme
    latest: datetime | None = None  # sosirea cel mai târziu
    terminal: bool = False  # B: echipa rămâne în zonă până trece furtuna
    alerts: list[AlertSpec] = field(default_factory=list)
    notifications: list[NotificationSpec] = field(default_factory=list)
    fallback: Proposal | None = None  # ce se face dacă nu încape în trasee
    duration_min: int | None = None  # dacă diferă de effort.duration_min (de exemplu treptele alese din scara C)
    skill: str | None = None
    crew_size: int | None = None
    lei_per_hour: float | None = None  # valoarea netă pe oră de lucru (durata + drumul estimat): ordinea listei pe echipe
    ladder: dict[str, Any] | None = None  # scara de soluții C: varianta aleasă și de ce
    skills_required: frozenset[str] | None = None  # combinații de trepte: echipa trebuie să aibă toate abilitățile

    @property
    def wi(self) -> WorkItem:
        return self.item.wi

    @property
    def id(self) -> str:
        return self.item.id


@dataclass
class Override:
    """Decizia unui om (POST /review), reaplicată la fiecare replanificare."""

    decision: str  # approve | reject | defer
    reviewer: str
    note: str | None
    ts: datetime
    audit_id: str


# ------------------------------------------------------------------ contextul unei rulări


@dataclass
class Context:
    settings: Settings
    plan_date: date
    as_of: datetime  # momentul deciziei (seara dinainte, pentru scenariile istorice)
    travel: TravelModel
    overrides: dict[str, Override] = field(default_factory=dict)

    @classmethod
    def build(cls, settings: Settings, plan_date: date, as_of: datetime | None = None, overrides: dict | None = None) -> Context:
        evening_before = datetime.combine(plan_date - timedelta(days=1), datetime.min.time(), tzinfo=TZ).replace(hour=18)
        now = datetime.now(TZ)
        return cls(
            settings=settings,
            plan_date=plan_date,
            as_of=as_of or min(now, evening_before),
            travel=TravelModel.from_economics(settings.economics),
            overrides=overrides or {},
        )

    def g(self, key: str, default: Any = None) -> Any:
        return self.settings.rule("global", key, default=default)

    def eligible_crews(self, skill: str, size: int) -> list[Crew]:
        return [c for c in self.settings.crews if skill in c.skills and c.size >= size]

    def shift(self) -> tuple[datetime, datetime]:
        start, end = self.settings.shift_bounds(self.plan_date)
        briefing = int(self.settings.rule("routing", "briefing_min", default=0))
        brk = int(self.settings.rule("routing", "break_min", default=0))
        return start + timedelta(minutes=briefing), end - timedelta(minutes=brk)


# ------------------------------------------------------------------ costuri


def action_cost(ctx: Context, wi: WorkItem, action: str) -> float:
    s = ctx.settings
    if action == "inspect_on_site":
        return s.econ("meters", "inspection_visit_cost_lei")
    if action == "remote_reading":
        return s.econ("meters", "remote_reading_cost_lei")
    if action == "preposition_crew":
        crews_needed = max(1, -(-wi.effort.crew_size // 3))
        return s.econ("storm", "preposition_cost_lei_per_crew_shift") * crews_needed
    if action == "adjust_tap":
        return s.econ("voltage", "tap_change_visit_cost_lei")
    if action == "measurement_campaign":
        return s.econ("voltage", "measurement_campaign_cost_lei")
    if action == "notify_customers":
        return s.econ("voltage", "notification_cost_lei_per_customer", 0.0) * max(1, wi.impact.customers_affected)
    if action == "office_correction":
        return s.econ("bilant", "office_correction_cost_lei", 15.0)
    if action == "grid_inspection":
        return s.econ("bilant", "grid_inspection_cost_lei", 486.0)
    if action == "phase_rebalance":
        return s.econ("voltage", "phase_rebalance_cost_lei", 350.0)
    if action == "offer_battery":
        return s.econ("voltage", "battery_offer_cost_lei_per_customer", 2.0) * max(1, wi.impact.customers_affected)
    if action == "export_limit":
        return s.econ("voltage", "export_limit_cost_lei", 150.0)
    if action == "transformer_upgrade":
        return s.econ("voltage", "transformer_upgrade_cost_lei", 120000.0)
    return 0.0


def estimate_costs(ctx: Context, wi: WorkItem, action: str) -> Costs:
    costs = Costs(action=action, action_cost=action_cost(ctx, wi, action))
    if action in CREW_ACTIONS:
        crews = ctx.eligible_crews(wi.effort.crew_skill.value, wi.effort.crew_size)
        if crews:
            best = min(
                crews,
                key=lambda c: ctx.travel.road_km(ctx.settings.depots[c.depot_id].lat, ctx.settings.depots[c.depot_id].lon, wi.location.lat, wi.location.lon),
            )
            depot = ctx.settings.depots[best.depot_id]
            km = ctx.travel.road_km(depot.lat, depot.lon, wi.location.lat, wi.location.lon)
            minutes = ctx.travel.minutes(km)
            per_km = ctx.settings.econ("travel", "vehicle_cost_lei_per_km", 0.0)
            per_hour = ctx.settings.econ("crew", "cost_lei_per_person_hour", 0.0) * wi.effort.crew_size
            costs.depot_id, costs.travel_km, costs.travel_min = best.depot_id, km, minutes
            costs.travel_cost = km * per_km + minutes / 60.0 * per_hour
        if action == "adjust_tap" and wi.effort.requires_planned_outage:
            hours = ctx.settings.econ("voltage", "planned_outage_hours", 1.0)
            costs.outage_cost = wi.impact.customers_affected * hours * ctx.settings.econ("storm", "cost_per_customer_hour_lei")
    return costs


def priority_of(ctx: Context, wi: WorkItem, costs: Costs) -> float:
    """Premiul din trasee (lei): valoarea așteptată minus costul acțiunii și al întreruperii; drumul îl socotește solverul.
    La siguranță, prioritatea se înmulțește (config: safety_priority_multiplier)."""
    p = max(0.0, wi.impact.expected_value_lei - costs.action_cost - costs.outage_cost)
    if wi.impact.safety_flag:
        p *= float(ctx.g("safety_priority_multiplier", 3.0))
    return round(p, 2)


# ------------------------------------------------------------------ ajutoare de text


def _factors(wi: WorkItem, n: int = 2) -> str:
    top = sorted(wi.explanation.top_factors, key=lambda f: abs(f.contribution), reverse=True)[:n]
    return "; ".join(f.label_ro for f in top)


def _label(wi: WorkItem) -> str:
    return wi.location.label or wi.asset_id


def working_days_between(d0: date, d1: date) -> int:
    """Zile lucrătoare (luni-vineri) strict între d0 și d1. Sărbătorile legale nu sunt încă în calcul."""
    n, d = 0, d0 + timedelta(days=1)
    while d < d1:
        if d.weekday() < 5:
            n += 1
        d += timedelta(days=1)
    return n


def earliest_outage_date(announce: date, notice_days: int) -> date:
    """Prima zi lucrătoare în care se poate face întreruperea, după `notice_days` zile lucrătoare pline de preaviz."""
    d = announce + timedelta(days=1)
    while working_days_between(announce, d) < notice_days or d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def _send_time(ctx: Context) -> datetime:
    hh, mm = str(ctx.settings.rule("voltage", "notify_send_time", default="18:00")).split(":")
    t = ctx.as_of.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
    return t if t > ctx.as_of else ctx.as_of + timedelta(minutes=5)


# ------------------------------------------------------------------ regulile


def _cost_keys(costs: Costs | None) -> dict[str, float]:
    """Costul folosit la decizie, scris în `threshold` (cerut de interfață): total, acțiune, deplasare, întrerupere."""
    if costs is None:
        return {}
    out = {"cost_lei": round(costs.total, 2), "action_cost_lei": round(costs.action_cost, 2)}
    if costs.travel_cost:
        out["travel_cost_lei"] = round(costs.travel_cost, 2)
        out["travel_km_est"] = round(costs.travel_km, 2)
    if costs.outage_cost:
        out["outage_cost_lei"] = round(costs.outage_cost, 2)
    return out


def _route(ctx: Context, item: Item, rule_id: str, reason: str, action: str, costs: Costs, threshold: dict, **kw: Any) -> Proposal:
    wi = item.wi
    start, end = ctx.shift()
    threshold = {**threshold, **_cost_keys(costs)}
    duration = int(kw.get("duration_min") or wi.effort.duration_min)
    value = max(0.0, wi.impact.expected_value_lei - costs.action_cost - costs.outage_cost)
    hours = max(0.25, (duration + costs.travel_min) / 60.0)
    threshold["lei_per_work_hour"] = round(value / hours, 2)
    p = Proposal(
        item=item,
        decision=DecisionType.assigned,
        rule_id=rule_id,
        reason_ro=reason,
        action=action,
        threshold=threshold,
        costs=costs,
        priority=priority_of(ctx, wi, costs),
        route=True,
        earliest=start,
        latest=end - timedelta(minutes=duration),
        lei_per_hour=round(value / hours, 2),
    )
    for k, v in kw.items():
        setattr(p, k, v)
    if wi.source == Source.A and wi.time_window is not None:
        # La contoare, fereastra e intervalul în care se poate ajunge la client; la C e intervalul cu risc, nu de lucru.
        tw_start, tw_end = wi.time_window.start.astimezone(TZ), wi.time_window.end.astimezone(TZ)
        p.earliest = max(start, tw_start)
        p.latest = min(end, tw_end) - timedelta(minutes=duration)
        p.threshold["access_window"] = 1.0
    return p


def _final(item: Item, decision: DecisionType, rule_id: str, reason: str, action: str, threshold: dict | None = None, **kw: Any) -> Proposal:
    threshold = {**(threshold or {}), **_cost_keys(kw.get("costs"))}
    p = Proposal(item=item, decision=decision, rule_id=rule_id, reason_ro=reason, action=action, threshold=threshold)
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _uncertain_route(ctx: Context, item: Item, rule_id: str, why: str, threshold: dict) -> Proposal:
    wi = item.wi
    min_ev = float(ctx.g("human_review_min_ev_lei", 150))
    threshold = {**threshold, "human_review_min_ev_lei": min_ev, "expected_value_lei": round(wi.impact.expected_value_lei, 2)}
    if wi.impact.expected_value_lei >= min_ev or wi.impact.safety_flag:
        alerts = []
        if wi.impact.safety_flag:
            alerts.append(
                AlertSpec("critical", f"Siguranță, de decis azi: {_label(wi)}", f"{why} Cazul are risc pentru oameni; un dispecer trebuie să decidă azi.")
            )
        return _final(item, DecisionType.human_review, rule_id, f"{why} Decide un om.", "human_review", threshold, alerts=alerts)
    return _final(
        item,
        DecisionType.deferred,
        rule_id + "-WATCH",
        f"{why} Valoarea așteptată ({lei(wi.impact.expected_value_lei)}) e sub pragul pentru timpul unui om ({lei(min_ev)}): urmărire.",
        "watchlist",
        threshold,
    )


def rule_human_override(ctx: Context, item: Item) -> Proposal | None:
    ov = ctx.overrides.get(item.id)
    if ov is None:
        return None
    wi = item.wi
    who = f"{ov.reviewer}" + (f": {ov.note}" if ov.note else "")
    if ov.decision == "reject":
        return _final(item, DecisionType.deferred, "R-HUMAN-REJECT", f"Respins de om ({who}).", "no_action", {"human": 1.0})
    if ov.decision == "defer":
        return _final(item, DecisionType.deferred, "R-HUMAN-DEFER", f"Amânat de om ({who}).", "watchlist", {"human": 1.0})
    # Aprobarea confirmă decizia agentului (cu acțiunea ei); doar unde agentul nu era sigur, omul aprobă recomandarea modelului.
    base = propose_rules(ctx, item)
    if base.route or base.decision != DecisionType.human_review:
        base.rule_id = "R-HUMAN-APPROVE"
        base.reason_ro = f"Aprobat de om ({who}). {base.reason_ro}"
        base.threshold = {**base.threshold, "human": 1.0}
        if base.route:
            base.mandatory = True
            base.priority = max(base.priority or 0.0, round(wi.impact.expected_value_lei, 2))
            base.fallback = None
        return base
    action = _approved_action(ctx, wi)
    if action in ("office_correction", "remote_reading"):
        costs = estimate_costs(ctx, wi, action)
        return _final(item, DecisionType.remote_action, "R-HUMAN-APPROVE", f"Aprobat de om ({who}): {ACTION_RO.get(action, action)}.",
                      action, {"human": 1.0}, costs=costs)
    costs = estimate_costs(ctx, wi, action)
    p = _route(ctx, item, "R-HUMAN-APPROVE", f"Aprobat de om ({who}): {ACTION_RO.get(action, action)}.", action, costs, {"human": 1.0})
    p.mandatory = True
    p.priority = max(p.priority or 0.0, round(wi.impact.expected_value_lei, 2))
    if wi.source == Source.B:
        _storm_window(ctx, p)
    if action == "adjust_tap" and notice_mode(ctx, wi) == "announce_now":
        p.notifications.append(_outage_notice(ctx, wi, wi.target_date))
    return p


def _approved_action(ctx: Context, wi: WorkItem) -> str:
    """Ce face echipa când un om aprobă un caz pe care agentul l-a trimis la el: recomandarea modelului, dacă e o acțiune."""
    rec = wi.recommended_action.value
    if wi.source == Source.A and wi.asset_type == AssetType.transformer_post:
        if rec in ("grid_inspection", "inspect_on_site", "office_correction", "remote_reading"):
            return rec
        return "grid_inspection" if wi.effort.crew_skill.value == "lv_grid" else "inspect_on_site"
    if wi.source == Source.A:
        return "inspect_on_site"
    if wi.source == Source.B:
        return "preposition_crew"
    return "adjust_tap" if rec == "adjust_tap" and _tap_notice_ok(ctx, wi) else "measurement_campaign"


def _strip_unsure(reason: str | None) -> str:
    """Motivul modelului fără un „nu sunt sigur” repetat la început (îl spune deja regula)."""
    text = (reason or "").strip().rstrip(".")
    for prefix in ("nu sunt sigur:", "nu sunt sigur -", "nu sunt sigur,", "nu sunt sigur"):
        if text.lower().startswith(prefix):
            text = text[len(prefix):].strip()
            break
    return text or "fără motiv dat"


def rule_abstain(ctx: Context, item: Item) -> Proposal | None:
    wi = item.wi
    if not wi.prediction.abstain:
        return None
    alerts = []
    if wi.impact.safety_flag:
        alerts.append(
            AlertSpec("critical", f"Siguranță, de decis azi: {_label(wi)}", f"Modelul nu e sigur ({wi.prediction.abstain_reason}), dar cazul are risc pentru oameni.")
        )
    return _final(
        item,
        DecisionType.human_review,
        "R-ABSTAIN",
        f"Modelul nu e sigur: {_strip_unsure(wi.prediction.abstain_reason)}. Decide un om.",
        "human_review",
        {"abstain": 1.0},
        alerts=alerts,
    )


def rule_data_quality(ctx: Context, item: Item) -> Proposal | None:
    wi = item.wi
    limit = float(ctx.g("max_missing_ratio", 0.4))
    if wi.data_quality.missing_ratio <= limit:
        return None
    why = f"Prea multe date lipsă la intrare ({pct(wi.data_quality.missing_ratio)}, pragul e {pct(limit)})."
    return _uncertain_route(ctx, item, "R-DATA-QUALITY", why, {"max_missing_ratio": limit, "missing_ratio": wi.data_quality.missing_ratio})


def rule_uncertain(ctx: Context, item: Item) -> Proposal | None:
    wi = item.wi
    pr = wi.prediction
    width_limit = float(ctx.g("max_interval_width", 0.5))
    width = (pr.interval_high - pr.interval_low) if pr.interval_low is not None and pr.interval_high is not None else 0.0
    if pr.confidence == Confidence.low:
        why = f"Încrederea modelului e mică (scor {pct(pr.score)})."
        return _uncertain_route(ctx, item, "R-LOW-CONFIDENCE", why, {"confidence_low": 1.0, "score": pr.score})
    if width > width_limit:
        why = f"Intervalul de încredere e prea larg ({pct(pr.interval_low)}-{pct(pr.interval_high)}, pragul e {num(width_limit, 2)})."
        return _uncertain_route(ctx, item, "R-WIDE-INTERVAL", why, {"max_interval_width": width_limit, "interval_width": round(width, 3)})
    return None


def rule_safety(ctx: Context, item: Item) -> Proposal | None:
    """Risc pentru oameni (A: șunt cu risc de incendiu; C). La B, safety_flag înseamnă rafale ≥ 75 km/h, adică lucru
    periculos la înălțime pentru echipă: se tratează în rule_storm ca avertisment, nu ca prioritate obligatorie."""
    wi = item.wi
    if not wi.impact.safety_flag or wi.source == Source.B:
        return None
    action = {Source.A: "inspect_on_site", Source.B: "preposition_crew", Source.C: "measurement_campaign"}[wi.source]
    costs = estimate_costs(ctx, wi, action)
    mult = float(ctx.g("safety_priority_multiplier", 3.0))
    reason = f"Risc pentru siguranța oamenilor ({_factors(wi, 1)}, scor {pct(wi.prediction.score)}): intră primul în traseu, oricare ar fi costul."
    p = _route(ctx, item, "R-SAFETY", reason, action, costs, {"safety_flag": 1.0, "safety_priority_multiplier": mult})
    p.mandatory = True
    p.priority = max(p.priority or 0.0, round(wi.impact.expected_value_lei * mult, 2))
    p.alerts.append(
        AlertSpec(
            "critical",
            f"Risc de siguranță: {_label(wi)}",
            f"{wi.explanation.summary_ro} Echipa merge fără să atingă instalația până la verificare; lucrul se face doar cu formele de organizare (AL/DV).",
        )
    )
    if wi.source == Source.B:
        _storm_window(ctx, p)
    return p


# ---- A: contoare


def rule_meters(ctx: Context, item: Item) -> Proposal:
    wi = item.wi
    pr = wi.prediction
    min_net = float(ctx.g("min_net_value_lei", 0))
    remote_min = float(ctx.settings.rule("meters", "remote_min_score", default=0.3))
    smart = bool(wi.extra.get("smart_meter", ctx.settings.rule("meters", "smart_meter_default", default=True)))
    visit = estimate_costs(ctx, wi, "inspect_on_site")
    remote = estimate_costs(ctx, wi, "remote_reading")
    ev = wi.impact.expected_value_lei
    net_visit = ev - visit.total
    breakeven = visit.total / wi.impact.value_if_true_lei if wi.impact.value_if_true_lei else 1.0
    th = {
        "min_net_value_lei": min_net,
        "expected_value_lei": round(ev, 2),
        "visit_cost_lei": round(visit.total, 2),
        "net_value_lei": round(net_visit, 2),
        "breakeven_score": round(breakeven, 3),
        "score": pr.score,
    }
    remote_fallback = None
    if smart and pr.score >= remote_min:
        remote_fallback = _final(
            item,
            DecisionType.remote_action,
            "R-CAPACITY-REMOTE",
            f"Vizita merita ({lei(net_visit)} valoare netă), dar echipele de contorizare sunt pline: citire la distanță azi ({lei(remote.total)}), vizita în planul următor.",
            "remote_reading",
            {**th, "remote_min_score": remote_min},
            costs=remote,
        )
    margin = float(ctx.settings.rule("meters", "medium_confidence_margin", default=0.25)) * visit.total
    th["medium_confidence_margin_lei"] = round(margin, 2)
    visit_min = float(ctx.settings.rule("meters", "visit_min_score", default=0.0))
    th["visit_min_score"] = visit_min
    if pr.score < visit_min and smart and pr.score >= remote_min and ev - remote.total > 0:
        return _final(
            item,
            DecisionType.remote_action,
            "R-A-REMOTE-FIRST",
            f"Scor {pct(pr.score)}: e mai probabil ca clientul să nu aibă nicio problemă (pragul pentru o vizită e {pct(visit_min)}), "
            f"așa că nu trimitem echipa la ușa lui. Întâi citire la distanță ({lei(remote.total)}); vizita doar dacă se confirmă.",
            "remote_reading",
            {**th, "remote_min_score": remote_min},
            costs=remote,
        )
    if pr.score < visit_min:
        return _final(
            item, DecisionType.deferred, "R-A-WATCH",
            f"Scor {pct(pr.score)}, sub pragul pentru o vizită ({pct(visit_min)}), iar contorul nu se poate citi de la distanță: urmărire.",
            "watchlist", {**th, "remote_min_score": remote_min},
        )
    if pr.confidence == Confidence.high and net_visit > min_net:
        reason = (
            f"{_factors(wi)}. Scor {pct(pr.score)}, încredere mare. Valoarea așteptată {lei(ev)} depășește costul "
            f"({visit.explain()} = {lei(visit.total)}) cu {lei(net_visit)}."
        )
        return _route(ctx, item, "R-A-VISIT", reason, "inspect_on_site", visit, th, fallback=remote_fallback)
    if pr.confidence == Confidence.medium and net_visit > min_net + margin:
        reason = (
            f"{_factors(wi)}. Scor {pct(pr.score)}, încredere medie, dar valoarea netă a vizitei ({lei(net_visit)}) "
            f"trece și de marja cerută la încredere medie ({lei(margin)}; costul: {visit.explain()})."
        )
        return _route(ctx, item, "R-A-VISIT-MEDIUM", reason, "inspect_on_site", visit, th, fallback=remote_fallback)
    if smart and pr.score >= remote_min and ev - remote.total > 0:
        if pr.confidence == Confidence.medium and net_visit > min_net:
            why = (
                f"Încredere medie (scor {pct(pr.score)}) și valoare netă mică ({lei(net_visit)}, sub marja de {lei(margin)}): "
                f"întâi citire la distanță ({lei(remote.total)}), fără deplasare."
            )
        else:
            why = (
                f"Valoarea așteptată ({lei(ev)}) nu acoperă vizita ({lei(visit.total)}; scorul ar trebui să fie peste "
                f"{pct(breakeven)}): citire la distanță ({lei(remote.total)})."
            )
        return _final(
            item,
            DecisionType.remote_action,
            "R-A-REMOTE-FIRST",
            f"{why} Dacă citirea confirmă problema sau contorul nu răspunde, vizita intră în planul următor.",
            "remote_reading",
            {**th, "remote_min_score": remote_min},
            costs=remote,
        )
    if not smart and net_visit > min_net and pr.confidence == Confidence.medium:
        reason = f"Contorul nu se poate citi de la distanță; valoarea netă a vizitei e {lei(net_visit)} (încredere medie)."
        return _route(ctx, item, "R-A-VISIT-NO-REMOTE", reason, "inspect_on_site", visit, th)
    if not smart:
        why = (f"Scor {pct(pr.score)}: valoarea așteptată ({lei(ev)}) nu justifică acum vizita ({lei(visit.total)}), "
               "iar contorul nu se poate citi de la distanță.")
    else:
        why = (f"Scor {pct(pr.score)}: valoarea așteptată ({lei(ev)}) nu justifică acum nici vizita ({lei(visit.total)}), "
               f"nici citirea la distanță (prag {pct(remote_min)}).")
    return _final(item, DecisionType.deferred, "R-A-WATCH", f"{why} Rămâne la urmărire.", "watchlist",
                  {**th, "remote_min_score": remote_min, "smart_meter": 1.0 if smart else 0.0})


def _fusion_note(wi: WorkItem) -> tuple[str, dict[str, float]]:
    """Textul și pragurile pentru un contor confirmat de bilanțul postului (extra["fusion"], contractul BilantFusion)."""
    f = wi.extra.get("fusion")
    if not isinstance(f, dict):
        return "", {}
    try:
        a, c = float(f["a_score"]), float(f["combined_score"])
        loss = float(f.get("post_excess_loss_lei_month", 0.0))
        post = str(f.get("post_id", "?"))
    except (KeyError, TypeError, ValueError):
        return "", {}
    text = f"Confirmat de bilanțul postului {post}: lipsă peste normal de ~{lei(loss)} pe lună; scorul a urcat de la {pct(a)} la {pct(c)}. "
    return text, {"fusion_a_score": a, "fusion_combined_score": c, "fusion_post_loss_lei_month": round(loss, 2)}


def rule_meters_fused(ctx: Context, item: Item) -> Proposal:
    p = rule_meters(ctx, item)
    text, th = _fusion_note(item.wi)
    if text:
        for q in (p, p.fallback):
            if q is not None:
                q.reason_ro = text + q.reason_ro
                q.threshold.update(th)
    return p


# ---- A: bilanț pe post (lucrări la nivel de post, din A_bilant.jsonl)

DIAG_RO = {
    "contor_defect": "contor defect sub post",
    "furt_inainte_de_contor": "furt înainte de contor",
    "pierdere_tehnica": "pierdere tehnică (cabluri, faze dezechilibrate)",
    "post_gresit": "client trecut la postul greșit în bază",
    "contor_post_x2": "contorul de bilanț al postului setat greșit",
}


def is_bilant_post(wi: WorkItem) -> bool:
    return wi.source == Source.A and (wi.asset_type == AssetType.transformer_post or wi.prediction.model_id.startswith("bilant-"))


def rule_bilant(ctx: Context, item: Item) -> Proposal:
    wi = item.wi
    if wi.asset_type != AssetType.transformer_post:
        return rule_meters_fused(ctx, item)  # contor găsit de bilanț: aceleași reguli ca la A (și pragul etic)
    pr = wi.prediction
    min_net = float(ctx.g("min_net_value_lei", 0))
    ev = wi.impact.expected_value_lei
    loss = wi.extra.get("post_excess_loss_lei_month")
    diag = DIAG_RO.get(pr.label, pr.label.replace("_", " "))
    head = f"Bilanțul postului {wi.asset_id}: {diag} (probabilitate {pct(pr.score)})"
    if isinstance(loss, (int, float)):
        head += f", lipsă peste normal ~{lei(float(loss))} pe lună"
    head += "."
    th: dict[str, float] = {"score": pr.score, "expected_value_lei": round(ev, 2), "min_net_value_lei": min_net}
    if isinstance(loss, (int, float)):
        th["post_excess_loss_lei_month"] = round(float(loss), 2)
    rec = wi.recommended_action
    if rec == RecommendedAction.office_correction:
        costs = estimate_costs(ctx, wi, "office_correction")
        return _final(item, DecisionType.remote_action, "R-BILANT-OFFICE",
                      f"{head} Corecție în baza de date (clientul la postul corect), fără deplasare ({lei(costs.total)}): intră în coada biroului de date.",
                      "office_correction", th, costs=costs)
    if rec == RecommendedAction.remote_reading:
        costs = estimate_costs(ctx, wi, "remote_reading")
        return _final(item, DecisionType.remote_action, "R-BILANT-REMOTE",
                      f"{head} Întâi verificări de la distanță ({lei(costs.total)}): recitirea contoarelor de sub post și jurnalul lor de evenimente; echipa doar dacă se confirmă.",
                      "remote_reading", th, costs=costs)
    if rec in (RecommendedAction.grid_inspection, RecommendedAction.inspect_on_site):
        action = rec.value
        costs = estimate_costs(ctx, wi, action)
        net = ev - costs.total
        th["net_value_lei"] = round(net, 2)
        if net > min_net:
            rule_id = "R-BILANT-GRID" if action == "grid_inspection" else "R-BILANT-VISIT"
            who = "echipa de rețea (joasă tensiune)" if action == "grid_inspection" else "echipa de contoare"
            reason = f"{head} Merge {who}: valoarea așteptată {lei(ev)} depășește costul ({costs.explain()} = {lei(costs.total)}) cu {lei(net)}."
            return _route(ctx, item, rule_id, reason, action, costs, th)
        return _final(item, DecisionType.deferred, "R-BILANT-WATCH",
                      f"{head} Valoarea așteptată ({lei(ev)}) nu acoperă deplasarea ({lei(costs.total)}): postul rămâne la urmărire.",
                      "watchlist", th, costs=costs)
    if rec == RecommendedAction.human_review:
        return _final(item, DecisionType.human_review, "R-BILANT-REVIEW", f"{head} Cauza nu e clară: decide un om.", "human_review", th)
    return _final(item, DecisionType.deferred, "R-BILANT-WATCH", f"{head} Postul rămâne la urmărire.", "watchlist", th)


# ---- B: furtună


def storm_onset(wi: WorkItem) -> datetime | None:
    """Începutul estimat al furtunii: extra.storm_onset (firul B), altfel începutul ferestrei de timp."""
    raw = wi.extra.get("storm_onset")
    if isinstance(raw, str):
        try:
            t = datetime.fromisoformat(raw)
            return t if t.tzinfo else t.replace(tzinfo=TZ)
        except ValueError:
            pass
    return wi.time_window.start if wi.time_window is not None else None


def _storm_window(ctx: Context, p: Proposal) -> None:
    wi = p.wi
    before = int(ctx.settings.rule("storm", "arrive_before_start_min", default=60))
    start, _ = ctx.shift()
    onset = storm_onset(wi)
    if onset is not None:
        p.latest = onset.astimezone(TZ) - timedelta(minutes=before)
    p.earliest = start
    p.terminal = True
    p.threshold.setdefault("arrive_before_start_min", float(before))


def rule_storm(ctx: Context, item: Item) -> Proposal:
    wi = item.wi
    pr = wi.prediction
    min_net = float(ctx.g("min_net_value_lei", 0))
    alert_min = float(ctx.settings.rule("storm", "alert_min_score", default=0.4))
    crit_min = float(ctx.settings.rule("storm", "critical_alert_min_score", default=0.75))
    costs = estimate_costs(ctx, wi, "preposition_crew")
    ev = wi.impact.expected_value_lei
    net = ev - costs.total
    tw = wi.time_window
    onset = storm_onset(wi)
    if onset is not None and tw is not None:
        window_ro = f"Furtuna e așteptată de la {hhmm(onset.astimezone(TZ))} (fereastra {hhmm(tw.start.astimezone(TZ))}-{hhmm(tw.end.astimezone(TZ))})"
    else:
        window_ro = f"Fereastra de risc: {hhmm(tw.start.astimezone(TZ))}-{hhmm(tw.end.astimezone(TZ))}" if tw else "Fereastra de risc: mâine"
    p90 = f"; în scenariul pesimist (P90), {num(pr.point_interval[1])} clienți fără curent" if pr.point_interval else ""
    risk = f"{_factors(wi).capitalize()}. {window_ro}. Probabilitate de avarii {pct(pr.score)}{p90}."
    th = {
        "min_net_value_lei": min_net,
        "expected_value_lei": round(ev, 2),
        "preposition_cost_lei": round(costs.total, 2),
        "net_value_lei": round(net, 2),
        "score": pr.score,
        "alert_min_score": alert_min,
    }
    alerts: list[AlertSpec] = []
    if pr.score >= alert_min:
        sev = "critical" if pr.score >= crit_min else "warning"
        alerts.append(AlertSpec(sev, f"Risc de avarii: {_label(wi)}", risk))
    if net <= min_net:
        return _final(
            item,
            DecisionType.deferred,
            "R-B-BELOW-COST",
            f"{risk} Valoarea așteptată ({lei(ev)}) nu acoperă o tură trimisă din timp ({costs.explain()} = {lei(costs.total)}). "
            "Dispeceratul e anunțat; echipele de intervenție rămân la bază.",
            "watchlist",
            th,
            alerts=alerts,
        )
    reason = f"{risk} Valoarea așteptată {lei(ev)} depășește costul turei ({lei(costs.total)}) cu {lei(net)}."
    if wi.recommended_action != RecommendedAction.preposition_crew:
        reason += f" Modelul a recomandat „{ACTION_RO.get(wi.recommended_action.value, wi.recommended_action.value)}”; decide pragul de cost."
    if wi.impact.safety_flag:
        gust = wi.extra.get("gust_max_kmh")
        reason += f" Rafale{f' de {num(float(gust))} km/h' if isinstance(gust, (int, float)) else ' puternice'}: echipa nu lucrează la înălțime până scade vântul."
        th["crew_safety_gusts"] = 1.0
    p = _route(ctx, item, "R-B-PREPOSITION", reason, "preposition_crew", costs, th, alerts=alerts)
    _storm_window(ctx, p)
    return p


# ---- C: tensiune


def notice_mode(ctx: Context, wi: WorkItem) -> str:
    """Preavizul ANRE pentru o întrerupere planificată: "notified" (anunțată deja), "announce_now" (mai e timp să o
    anunțăm azi, cu preavizul legal) sau "too_late" (nu se mai poate face la data lucrării)."""
    if wi.extra.get("planned_outage_notified"):
        return "notified"
    level = ctx.settings.rule("voltage", "outage_voltage_level", default="lv")
    notice = int(ctx.settings.econ("outages", f"planned_notice_working_days_{level}", 2))
    return "announce_now" if working_days_between(ctx.as_of.date(), wi.target_date) >= notice else "too_late"


def _tap_notice_ok(ctx: Context, wi: WorkItem) -> bool:
    return notice_mode(ctx, wi) != "too_late"


def _prosumer_message(ctx: Context, wi: WorkItem) -> NotificationSpec:
    if wi.time_window is not None:
        a, b = hhmm(wi.time_window.start.astimezone(TZ)), hhmm(wi.time_window.end.astimezone(TZ))
    else:
        a, b = ctx.settings.rule("voltage", "notify_window", default=["11:00", "15:00"])
    msg = (
        f"Mâine, {zi(wi.target_date)}, între {a} și {b} e soare puternic, iar tensiunea în rețeaua din zona {_label(wi)} "
        "poate trece de limită. Dacă puteți, porniți atunci aparatele mari (mașina de spălat, boilerul, încărcarea mașinii). "
        "Așa folosiți energia produsă de panouri, iar invertorul nu se mai oprește singur."
    )
    return NotificationSpec("prosumatori", msg, _send_time(ctx))


def _outage_notice(ctx: Context, wi: WorkItem, on: date) -> NotificationSpec:
    hours = ctx.settings.econ("voltage", "planned_outage_hours", 1.0)
    end_h = 9 + round(hours)
    msg = (
        f"Rețele Electrice: {zi(on)}, între 09:00 și {end_h:02d}:00, alimentarea cu energie electrică va fi întreruptă "
        f"în zona postului de transformare {_label(wi)}, pentru lucrări de reglaj al tensiunii. Ne cerem scuze pentru neplăcere."
    )
    return NotificationSpec("clienti_zona", msg, _send_time(ctx))


REMEDY_RO = {
    "phase_rebalance": "mutarea a câteva case pe altă fază",
    "adjust_tap": "coborârea prizei transformatorului",
    "notify_customers": "mesajele către clienții Ore Smart",
    "offer_battery": "oferta de baterii",
    "export_limit": "limita de injecție pe oră",
    "transformer_upgrade": "transformatorul nou",
}


def _combo_ro(combo: tuple[RemedyOption, ...]) -> str:
    names = [REMEDY_RO.get(o.action.value, o.action.value) for o in combo]
    text = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " și " + names[-1]
    if len(combo) == 1 and combo[0].action == RecommendedAction.notify_customers:
        text += " singure"
    elif len(combo) == 1 and combo[0].action == RecommendedAction.offer_battery:
        text += " singură"
    rates = [o.participation_rate for o in combo if o.participation_rate is not None]
    return text + (f" (la {pct(rates[0])} participare)" if rates else "")


def _ladder_notifications(ctx: Context, wi: WorkItem, combo: tuple[RemedyOption, ...]) -> list[NotificationSpec]:
    out = []
    for o in combo:
        hours = ", ".join(o.risk_hours) if o.risk_hours else None
        if o.action == RecommendedAction.notify_customers:
            msg = o.message_preview_ro or _prosumer_message(ctx, wi).message_ro
            out.append(NotificationSpec("prosumatori", msg, _send_time(ctx)))
        elif o.action == RecommendedAction.offer_battery:
            kwh = f"{num(o.battery_kwh_total)} kWh de baterii pe post" if o.battery_kwh_total else "baterii"
            payback = f", recuperare în ~{num(o.payback_years, 1)} ani" if o.payback_years else ""
            msg = (o.message_preview_ro or
                   f"PPC Energie: pentru prosumatorii din zona {_label(wi)}, o baterie ar păstra energia de la prânz pentru seară "
                   f"și ar opri deconectările invertorului. Propunere: {kwh}{payback}. Detalii în magazinele PPC.")
            out.append(NotificationSpec("prosumatori", msg, _send_time(ctx)))
        elif o.action == RecommendedAction.export_limit:
            msg = o.message_preview_ro or (
                f"Rețele Electrice: propunem prosumatorilor din zona {_label(wi)} o limită de injecție în rețea"
                + (f" în orele {hours}" if hours else " la prânz") + ", ca tensiunea să rămână sub 253 V și invertoarele să nu se oprească.")
            out.append(NotificationSpec("prosumatori", msg, _send_time(ctx)))
    return out


def rule_remedy_ladder(ctx: Context, item: Item, th: dict[str, float]) -> Proposal | None:
    """Scara de soluții (R-REMEDY-LADDER): cea mai ieftină combinație de trepte care aduce P90 sub limită.
    Efectele treptelor combinate se adună (P90 = P90 inițial + suma efectelor); o treaptă singură folosește p90_after_pu."""
    wi = item.wi
    raw = wi.extra.get("remedy_options")
    if not isinstance(raw, list) or not raw:
        return None
    opts: list[RemedyOption] = []
    for o in raw:
        try:
            opts.append(RemedyOption.model_validate(o))
        except ValidationError:
            continue
    if not opts:
        return None
    s = ctx.settings
    pr = wi.prediction
    limit = s.econ("voltage", "overvoltage_limit_pu", 1.10)
    base = pr.point_interval[1] if pr.point_interval else (pr.point_estimate if pr.point_estimate is not None else max(o.p90_after_pu - o.effect_pu for o in opts))
    max_k = int(s.rule("remedy", "max_combination", default=3))
    upgrade = RecommendedAction.transformer_upgrade
    cands: list[tuple[tuple[RemedyOption, ...], float, float]] = []
    for k in range(1, min(max_k, len(opts)) + 1):
        for combo in itertools.combinations(opts, k):
            if k > 1 and (not all(o.combinable for o in combo) or any(o.action == upgrade for o in combo)):
                continue
            p90 = combo[0].p90_after_pu if k == 1 else base + sum(o.effect_pu for o in combo)
            cands.append((combo, round(p90, 4), round(sum(o.cost_lei for o in combo), 2)))
    conf = {"high": 0, "medium": 1, "low": 2}
    feasible = [c for c in cands if c[1] < limit]
    if feasible:
        combo, p90_after, cost = min(feasible, key=lambda c: (c[2], len(c[0]), max(conf[o.confidence.value] for o in c[0]), c[1]))
    else:
        combo, p90_after, cost = min(cands, key=lambda c: (c[1], c[2]))
    cheaper = sorted({(c[2], c[1], _combo_ro(c[0])) for c in cands if c[2] < cost})
    why_not = [f"{name} ({lei(c_cost)}) scade tensiunea doar până la {num(c_p90, 3)} pu" for c_cost, c_p90, name in cheaper[:3]]
    th = {**th, "p90_before_pu": round(base, 4), "p90_after_pu": p90_after, "remedy_cost_lei": cost, "remedy_steps": float(len(combo)),
          "remedy_options_checked": float(len(cands))}
    rates = [o.participation_rate for o in combo if o.participation_rate is not None]
    if rates:
        th["participation_rate"] = float(rates[0])
    chosen_txt = f"Aleg {_combo_ro(combo)} ({lei(cost)}): P90 scade de la {num(base, 3)} la {num(p90_after, 3)} pu, sub limita de {num(limit, 2)}."
    why_txt = (" N-am ales o variantă mai ieftină: " + "; ".join(why_not) + ".") if why_not else " E cea mai ieftină treaptă din scară."
    battery = next((o for o in combo if o.action == RecommendedAction.offer_battery), None)
    ladder = {
        "post_id": wi.asset_id, "work_item_id": wi.work_item_id, "label": _label(wi), "feasible": bool(feasible),
        "chosen": [o.action.value for o in combo], "cost_lei": cost, "p90_before_pu": round(base, 4), "p90_after_pu": p90_after,
        "why_not_cheaper": why_not, "invest": any(o.action == upgrade for o in combo),
        "battery": None if battery is None else {"battery_kwh_total": battery.battery_kwh_total, "revenue_lei": battery.revenue_lei,
                                                  "payback_years": battery.payback_years, "customers_targeted": battery.customers_targeted},
        "inverter_trips_avoided": sum(o.inverter_trips_avoided or 0.0 for o in combo),
    }
    notes = _ladder_notifications(ctx, wi, combo)
    notify_costs = Costs(action="notify_customers", action_cost=sum(o.cost_lei for o in combo if not o.needs_crew))
    if not feasible:
        reason = (f"{_factors(wi)}. Nicio combinație de cel mult {max_k} trepte nu aduce P90 sub {num(limit, 2)} pu "
                  f"(cel mai bun: {_combo_ro(combo)}, {num(p90_after, 3)} pu). Decide un om; probabil e nevoie de investiție.")
        return _final(item, DecisionType.human_review, "R-REMEDY-LADDER", reason, "human_review", th, notifications=notes, ladder=ladder)
    if ladder["invest"]:
        reason = (f"{_factors(wi)}. {chosen_txt}{why_txt} E o investiție: intră în raportul de investiții, nu în traseele de mâine.")
        return _final(item, DecisionType.deferred, "R-REMEDY-LADDER", reason, "transformer_upgrade", th, ladder=ladder)
    crew = [o for o in combo if o.needs_crew]
    if not crew:
        reason = f"{_factors(wi)}. {chosen_txt}{why_txt} Fără echipă: mesajele și ofertele pleacă din sistem (demo, nu se trimite nimic)."
        return _final(item, DecisionType.notify, "R-REMEDY-LADDER", reason, "notify_customers", th, notifications=notes, costs=notify_costs, ladder=ladder)
    needs_notice = {str(a) for a in (s.rule("remedy", "crew_steps_need_notice", default=["adjust_tap", "phase_rebalance"]) or [])}
    if any(o.action.value in needs_notice for o in crew) and not _tap_notice_ok(ctx, wi):
        level = s.rule("voltage", "outage_voltage_level", default="lv")
        notice = int(s.econ("outages", f"planned_notice_working_days_{level}", 2))
        on = earliest_outage_date(ctx.as_of.date(), notice)
        th["planned_notice_working_days"] = float(notice)
        reason = (f"{_factors(wi)}. {chosen_txt}{why_txt} Treptele cu echipă cer o întrerupere planificată, anunțată cu cel puțin "
                  f"{notice} zile lucrătoare înainte (Ord. ANRE 46/2021, art. 12): le programez pe {zi(on)}."
                  + (" Până atunci: mesajele de mai jos." if notes else ""))
        return _final(item, DecisionType.notify, "R-REMEDY-LADDER", reason, "notify_customers", th,
                      notifications=notes + [_outage_notice(ctx, wi, on)], costs=notify_costs, ladder=ladder)
    primary = crew[0]
    costs = estimate_costs(ctx, wi, primary.action.value)
    costs.action, costs.action_cost, costs.outage_cost = "remedy", cost, 0.0
    duration = sum(o.duration_min for o in crew) or wi.effort.duration_min
    skills = frozenset(o.crew_skill.value if o.crew_skill else wi.effort.crew_skill.value for o in crew)
    if any(o.action.value in needs_notice for o in crew):
        if notice_mode(ctx, wi) == "notified":
            when = " Întreruperea a fost anunțată deja; echipa merge mâine."
        else:
            when = " Anunț întreruperea azi, cu preavizul cerut de Ord. ANRE 46/2021; echipa merge la data lucrării."
            notes = notes + [_outage_notice(ctx, wi, wi.target_date)]
    else:
        when = " Fără întrerupere; echipa merge mâine."
    reason = f"{_factors(wi)}. {chosen_txt}{why_txt}{when}"
    p = _route(ctx, item, "R-REMEDY-LADDER", reason, primary.action.value, costs, th, notifications=notes, ladder=ladder,
               duration_min=duration, skills_required=skills)
    p.fallback = _final(item, DecisionType.notify, "R-REMEDY-LADDER", reason.replace("echipa merge mâine", "echipele sunt pline mâine: doar mesajele"),
                        "notify_customers", th, notifications=notes, costs=notify_costs, ladder=ladder)
    return p


def rule_voltage(ctx: Context, item: Item) -> Proposal:
    wi = item.wi
    pr = wi.prediction
    s = ctx.settings
    min_score = float(s.rule("voltage", "min_score", default=0.5))
    limit = s.econ("voltage", "overvoltage_limit_pu", 1.10)
    min_net = float(ctx.g("min_net_value_lei", 0))
    ev = wi.impact.expected_value_lei
    p90 = pr.point_interval[1] if pr.point_interval else pr.point_estimate
    th: dict[str, float] = {"min_score": min_score, "overvoltage_limit_pu": limit, "score": pr.score, "expected_value_lei": round(ev, 2)}
    if p90 is not None:
        th["vmax_p90_pu"] = float(p90)
    vtxt = f"tensiunea maximă estimată {num(pr.point_estimate, 3)} pu" if pr.point_estimate is not None else "tensiunea"
    if pr.score < min_score or (p90 is not None and p90 < limit):
        why = f"scorul {pct(pr.score)} e sub pragul {pct(min_score)}" if pr.score < min_score else f"chiar și în scenariul pesimist (P90) tensiunea rămâne sub {num(limit, 2)} pu"
        return _final(item, DecisionType.deferred, "R-C-WATCH", f"{vtxt.capitalize()}; {why}. Postul rămâne la urmărire.", "watchlist", th)

    ladder = rule_remedy_ladder(ctx, item, th)
    if ladder is not None:
        return ladder
    tap = estimate_costs(ctx, wi, "adjust_tap")
    measure = estimate_costs(ctx, wi, "measurement_campaign")
    notify = estimate_costs(ctx, wi, "notify_customers")
    net_tap, net_measure = ev - tap.total, ev - measure.total
    th.update({"min_net_value_lei": min_net, "tap_cost_lei": round(tap.total, 2), "measurement_cost_lei": round(measure.total, 2)})
    prosumers = _prosumer_message(ctx, wi)
    rec = wi.recommended_action

    if (rec == RecommendedAction.adjust_tap or wi.effort.requires_planned_outage) and net_tap <= min_net:
        th["net_tap_value_lei"] = round(net_tap, 2)
        why = (
            f"{_factors(wi)}; {vtxt}. Schimbarea prizei nu se justifică acum: costul ei ({tap.explain()} = {lei(tap.total)}) "
            f"depășește valoarea așteptată ({lei(ev)})."
        )
        if pr.confidence == Confidence.medium and net_measure > min_net:
            p = _route(ctx, item, "R-C-MEASURE", f"{why} Un analizor la post ({lei(measure.total)}) arată cât de des se întâmplă.", "measurement_campaign", measure, th, notifications=[prosumers])
            p.fallback = _final(item, DecisionType.notify, "R-C-NOTIFY", why + " Mâine: mesaj către prosumatori.", "notify_customers", th, notifications=[prosumers], costs=notify)
            return p
        return _final(item, DecisionType.notify, "R-C-NOTIFY", why + " Mâine: mesaj către prosumatori să consume la prânz.", "notify_customers", th, notifications=[prosumers], costs=notify)
    if rec == RecommendedAction.adjust_tap or wi.effort.requires_planned_outage:
        level = s.rule("voltage", "outage_voltage_level", default="lv")
        notice = int(s.econ("outages", f"planned_notice_working_days_{level}", 2))
        th["planned_notice_working_days"] = float(notice)
        th["net_tap_value_lei"] = round(net_tap, 2)
        mode = notice_mode(ctx, wi)
        if mode != "too_late":
            notices = [prosumers]
            if mode == "notified":
                when = "Întreruperea a fost anunțată deja"
            else:
                when = f"Anunț întreruperea azi, cu {notice} zile lucrătoare înainte, cum cere Ord. ANRE 46/2021"
                notices.append(_outage_notice(ctx, wi, wi.target_date))
            reason = (
                f"{_factors(wi)}; {vtxt} față de limita {num(limit, 2)}. {when}; "
                f"valoarea netă a schimbării prizei e {lei(net_tap)} ({tap.explain()})."
            )
            return _route(ctx, item, "R-C-TAP", reason, "adjust_tap", tap, th, notifications=notices)
        on = earliest_outage_date(ctx.as_of.date(), notice)
        outage = _outage_notice(ctx, wi, on)
        base = (
            f"{_factors(wi)}; {vtxt} față de limita {num(limit, 2)}. Schimbarea prizei cere o întrerupere planificată, "
            f"anunțată cu cel puțin {notice} zile lucrătoare înainte (Ord. ANRE 46/2021, art. 12): o programez pe {zi(on)}."
        )
        if pr.confidence == Confidence.medium and net_measure > min_net:
            reason = f"{base} Încredere medie: mâine montăm un analizor la post ({lei(measure.total)}), ca să confirmăm înainte de întrerupere."
            p = _route(ctx, item, "R-C-MEASURE-THEN-TAP", reason, "measurement_campaign", measure, th, notifications=[prosumers, outage])
            p.fallback = _final(item, DecisionType.notify, "R-C-TAP-NOTICE", base + " Mâine: mesaj către prosumatori.", "notify_customers", th, notifications=[prosumers, outage], costs=notify)
            return p
        return _final(
            item, DecisionType.notify, "R-C-TAP-NOTICE", base + " Până atunci, mâine: mesaj către prosumatori.", "notify_customers", th,
            notifications=[prosumers, outage], costs=notify,
        )
    if rec == RecommendedAction.measurement_campaign and net_measure > min_net:
        reason = f"{_factors(wi)}; {vtxt}. Un analizor la post ({lei(measure.total)}) confirmă problema înainte de o intervenție."
        p = _route(ctx, item, "R-C-MEASURE", reason, "measurement_campaign", measure, th, notifications=[prosumers])
        p.fallback = _final(item, DecisionType.notify, "R-C-NOTIFY", reason + " Echipele sunt pline: doar mesaj către prosumatori.", "notify_customers", th, notifications=[prosumers], costs=notify)
        return p
    return _final(
        item, DecisionType.notify, "R-C-NOTIFY",
        f"{_factors(wi)}; {vtxt}. Fără echipă: mesaj către prosumatori să consume la prânz ({lei(notify.total)}).",
        "notify_customers", th, notifications=[prosumers], costs=notify,
    )


# ------------------------------------------------------------------ verificarea echipelor și plafonul regional


def check_crews(ctx: Context, p: Proposal) -> Proposal:
    """O candidatură fără nicio echipă potrivită (abilitate, mărime) nu poate intra în trasee."""
    if not p.route:
        return p
    wi = p.wi
    size = p.crew_size or wi.effort.crew_size
    required = p.skills_required or frozenset({p.skill or wi.effort.crew_skill.value})
    crews = [c for c in ctx.settings.crews if required <= c.skills and c.size >= size]
    if crews:
        return p
    skill = " + ".join(SKILL_RO.get(s, s) for s in sorted(required))
    reason = f"Nicio echipă cu abilitatea {skill} și cel puțin {size} oameni."
    alerts = [AlertSpec("warning", f"Fără echipă potrivită: {_label(wi)}", reason)]
    if p.fallback is not None:
        p.fallback.alerts += alerts
        p.fallback.reason_ro = f"{reason} {p.fallback.reason_ro}"
        return p.fallback
    return _final(p.item, DecisionType.human_review if p.mandatory else DecisionType.deferred, "R-NO-CREW", reason, p.action, p.threshold, alerts=p.alerts + alerts)


def _drop_unreachable_storms(ctx: Context, proposals: list[Proposal]) -> None:
    """O furtună la care nicio echipă potrivită nu poate ajunge înainte de ora limită nu ocupă plafonul regional."""
    start, _ = ctx.shift()
    for i, p in enumerate(proposals):
        if not (p.route and p.action == "preposition_crew" and p.latest is not None):
            continue
        wi = p.wi
        crews = ctx.eligible_crews(wi.effort.crew_skill.value, wi.effort.crew_size)
        if not crews:
            continue
        fastest = min(ctx.travel.minutes(ctx.travel.road_km(ctx.settings.depots[c.depot_id].lat, ctx.settings.depots[c.depot_id].lon,
                                                               wi.location.lat, wi.location.lon)) for c in crews)
        if start + timedelta(minutes=fastest) > p.latest:
            proposals[i] = _final(
                p.item, DecisionType.deferred, "R-B-TOO-LATE",
                f"{p.reason_ro} Dar nicio echipă potrivită nu poate ajunge până la {hhmm(p.latest.astimezone(TZ))} "
                f"(cel mai scurt drum: {round(fastest)} min de la plecarea de la {hhmm(start)}).",
                "watchlist", p.threshold, alerts=p.alerts, priority=p.priority,
            )


def cap_storm_per_region(ctx: Context, proposals: list[Proposal]) -> None:
    """Cel mult `max_crews_per_region` echipe trimise din timp într-o regiune; restul rămân pentru lucrările curente."""
    _drop_unreachable_storms(ctx, proposals)
    cap = int(ctx.settings.rule("storm", "max_crews_per_region", default=2))
    by_region: dict[str, list[int]] = {}
    for i, p in enumerate(proposals):
        if p.route and p.action == "preposition_crew" and not p.mandatory:
            rid = ctx.settings.region_of_county(p.wi.location.county) or ""
            region = (ctx.settings.regions.get(rid) or {}).get("label_ro", "zona necunoscută")
            by_region.setdefault(region, []).append(i)
    for region, idxs in by_region.items():
        idxs.sort(key=lambda i: proposals[i].priority or 0.0, reverse=True)
        for i in idxs[cap:]:
            p = proposals[i]
            # Valoare peste cost, dar plafonul regional e atins: agentul nu amână în tăcere, cere întăriri și lasă decizia
            # dispecerului (aprobarea face lucrarea obligatorie și o trimite cu prima echipă liberă).
            proposals[i] = _final(
                p.item,
                DecisionType.human_review,
                "R-B-REGION-CAP",
                f"{p.reason_ro} Dar în regiunea {region} sunt deja {cap} echipe trimise din timp (plafonul din config): "
                "cer întăriri (echipe din alte regiuni sau contractori); decide dispecerul.",
                "human_review",
                {**p.threshold, "max_crews_per_region": float(cap)},
                alerts=p.alerts,
                priority=p.priority,
            )


# ------------------------------------------------------------------ intrarea principală

RULES = [rule_human_override, rule_abstain, rule_data_quality, rule_uncertain, rule_safety]


def propose_rules(ctx: Context, item: Item) -> Proposal:
    """Decizia agentului fără suprascrierea omului (folosită și la aprobare, ca omul să aprobe exact decizia agentului)."""
    for rule in RULES[1:]:
        p = rule(ctx, item)
        if p is not None:
            return check_crews(ctx, p)
    wi = item.wi
    if is_bilant_post(wi):
        return check_crews(ctx, rule_bilant(ctx, item))
    by_source = {Source.A: rule_meters_fused, Source.B: rule_storm, Source.C: rule_voltage}
    return check_crews(ctx, by_source[wi.source](ctx, item))


def propose(ctx: Context, item: Item) -> Proposal:
    for rule in RULES:
        p = rule(ctx, item)
        if p is not None:
            return check_crews(ctx, p)
    wi = item.wi
    if is_bilant_post(wi):
        return check_crews(ctx, rule_bilant(ctx, item))
    by_source = {Source.A: rule_meters_fused, Source.B: rule_storm, Source.C: rule_voltage}
    return check_crews(ctx, by_source[wi.source](ctx, item))


def decide(ctx: Context, items: list[Item]) -> list[Proposal]:
    proposals = [propose(ctx, it) for it in items]
    cap_storm_per_region(ctx, proposals)
    return proposals


RULE_CATALOG: dict[str, str] = {
    "R-QUARANTINE": "Intrare greșită (contract sau verificări de sens): carantină, nu intră în plan.",
    "R-HUMAN-APPROVE": "Un om a aprobat lucrarea: intră în traseu cu prioritate.",
    "R-HUMAN-REJECT": "Un om a respins lucrarea.",
    "R-HUMAN-DEFER": "Un om a amânat lucrarea.",
    "R-ABSTAIN": "Modelul s-a abținut ('nu sunt sigur'): decide un om.",
    "R-DATA-QUALITY": "Prea multe date lipsă la intrare: decide un om (sau urmărire, dacă valoarea e mică).",
    "R-LOW-CONFIDENCE": "Încredere mică: decide un om (sau urmărire, dacă valoarea e mică).",
    "R-WIDE-INTERVAL": "Interval de încredere prea larg: decide un om (sau urmărire).",
    "R-SAFETY": "Risc pentru oameni: prioritate maximă, alertă critică, intră primul în traseu.",
    "R-A-VISIT": "Contor, încredere mare, valoarea așteptată peste costul vizitei: echipă.",
    "R-A-VISIT-MEDIUM": "Contor, încredere medie, valoarea netă peste marja de siguranță: echipă (citire la distanță dacă nu încape).",
    "R-A-VISIT-NO-REMOTE": "Contor fără citire la distanță, încredere medie, valoare netă pozitivă: echipă.",
    "R-A-REMOTE-FIRST": "Contor, încredere medie sau valoare sub costul vizitei: citire la distanță întâi.",
    "R-A-WATCH": "Contor cu scor mic: urmărire.",
    "R-CAPACITY-REMOTE": "Vizita merita, dar echipele sunt pline: citire la distanță azi.",
    "R-B-PREPOSITION": "Furtună: valoarea așteptată peste costul turei; echipa ajunge înainte de fereastra de risc.",
    "R-B-BELOW-COST": "Furtună cu risc mic: doar alertă la dispecerat.",
    "R-B-REGION-CAP": "Furtună: plafonul de echipe pe regiune e atins.",
    "R-B-TOO-LATE": "Furtună: nicio echipă nu poate ajunge înainte de fereastra de risc.",
    "R-C-WATCH": "Tensiune: sub prag sau sub limită chiar și în scenariul pesimist: urmărire.",
    "R-C-TAP": "Tensiune: întreruperea a fost anunțată la timp, schimbarea prizei merită: echipă.",
    "R-C-TAP-NOTICE": "Tensiune: priza cere preaviz ANRE; întreruperea se programează, mâine mesaj către prosumatori.",
    "R-C-MEASURE-THEN-TAP": "Tensiune, încredere medie: analizor mâine, priza după preaviz.",
    "R-C-MEASURE": "Tensiune: analizor la post înainte de intervenție.",
    "R-C-NOTIFY": "Tensiune: mesaj către prosumatori, fără echipă.",
    "R-CAPACITY": "Nu a încăput în turele de mâine: amânat.",
    "R-TIME-WINDOW": "Nicio echipă potrivită nu poate ajunge în fereastra de timp: amânat.",
    "R-NOT-WORTH-TRIP": "Nici singură în traseu lucrarea nu acoperă drumul dus-întors: fără deplasare dedicată.",
    "R-NO-CREW": "Nicio echipă cu abilitatea și mărimea cerute.",
    "R-SAFETY-NO-CREW": "Caz de siguranță fără echipă disponibilă: decide dispecerul azi.",
    "R-FUSION-BILANT": "Contor marcat de A confirmat de bilanțul postului: scorul combinat înlocuiește scorul A (în jurnal).",
    "R-BILANT-OFFICE": "Bilanț: client la postul greșit în bază, corecție în birou fără deplasare.",
    "R-BILANT-REMOTE": "Bilanț: întâi verificări de la distanță (recitire, jurnal de evenimente).",
    "R-BILANT-GRID": "Bilanț: pierdere tehnică; echipa de rețea, dacă valoarea acoperă deplasarea.",
    "R-BILANT-VISIT": "Bilanț: echipa de contoare la post (de exemplu contorul de bilanț setat greșit).",
    "R-BILANT-WATCH": "Bilanț: valoarea nu acoperă deplasarea, postul rămâne la urmărire.",
    "R-BILANT-REVIEW": "Bilanț: cauza nu e clară, decide un om.",
    "R-REMEDY-LADDER": "Tensiune: cea mai ieftină combinație de trepte care aduce P90 sub 1,10 pu; explică de ce nu una mai ieftină.",
}
