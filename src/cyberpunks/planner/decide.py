"""Stratul de decizie: reguli scrise în cod, cu nume (`rule_id`) și cu pragurile scrise în fiecare decizie.

Pentru fiecare lucrare validă se evaluează regulile în ordine; prima care se potrivește decide.
Rezultatul e o propunere: fie o decizie finală (om, citire la distanță, mesaj, amânare), fie o candidatură
pentru traseele echipelor. Candidaturile le împarte apoi optimizatorul (routing.py) pe echipe; ce nu
încape primește o decizie de rezervă (de exemplu citire la distanță în loc de vizită).

Costul unei acțiuni: costul acțiunii (config/economics.yaml) + deplasarea estimată de la cea mai apropiată bază
cu o echipă potrivită + costul social al unei întreruperi planificate (doar la schimbarea prizei).
Valoarea netă = expected_value_lei − cost. Prioritatea = valoarea netă × factorul de urgență (× 3 la siguranță).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

from cyberpunks.common.contracts import Confidence, DecisionType, RecommendedAction, Source, WorkItem
from cyberpunks.planner.geo import TravelModel
from cyberpunks.planner.ingest import Item
from cyberpunks.planner.settings import TZ, Crew, Settings
from cyberpunks.planner.texts import ACTION_RO, SKILL_RO, hhmm, lei, num, pct, zi

CREW_ACTIONS = {"inspect_on_site", "preposition_crew", "adjust_tap", "measurement_campaign"}


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


def urgency_factor(ctx: Context, wi: WorkItem) -> float:
    ref = float(ctx.g("urgency_reference_hours", 24))
    floor = float(ctx.g("urgency_min_factor", 0.25))
    return max(floor, min(1.0, ref / wi.impact.urgency_hours))


def priority_of(ctx: Context, wi: WorkItem, net: float) -> float:
    p = max(0.0, net) * urgency_factor(ctx, wi)
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


def _route(ctx: Context, item: Item, rule_id: str, reason: str, action: str, costs: Costs, threshold: dict, **kw: Any) -> Proposal:
    wi = item.wi
    start, end = ctx.shift()
    net = wi.impact.expected_value_lei - costs.total
    p = Proposal(
        item=item,
        decision=DecisionType.assigned,
        rule_id=rule_id,
        reason_ro=reason,
        action=action,
        threshold=threshold,
        costs=costs,
        priority=priority_of(ctx, wi, net),
        route=True,
        earliest=start,
        latest=end - timedelta(minutes=wi.effort.duration_min),
    )
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _final(item: Item, decision: DecisionType, rule_id: str, reason: str, action: str, threshold: dict | None = None, **kw: Any) -> Proposal:
    p = Proposal(item=item, decision=decision, rule_id=rule_id, reason_ro=reason, action=action, threshold=threshold or {})
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
    action = {
        Source.A: "inspect_on_site",
        Source.B: "preposition_crew",
        Source.C: "adjust_tap" if _tap_notice_ok(ctx, wi) and wi.recommended_action == RecommendedAction.adjust_tap else "measurement_campaign",
    }[wi.source]
    costs = estimate_costs(ctx, wi, action)
    p = _route(ctx, item, "R-HUMAN-APPROVE", f"Aprobat de om ({who}): {ACTION_RO[action]}.", action, costs, {"human": 1.0})
    p.mandatory = True
    p.priority = max(p.priority or 0.0, round(wi.impact.expected_value_lei, 2))
    if wi.source == Source.B:
        _storm_window(ctx, p)
    return p


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
        f"Modelul nu e sigur: {wi.prediction.abstain_reason}. Decide un om.",
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
    wi = item.wi
    if not wi.impact.safety_flag:
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
    if pr.confidence == Confidence.high and net_visit > min_net:
        reason = (
            f"{_factors(wi)}. Scor {pct(pr.score)}, încredere mare. Valoarea așteptată {lei(ev)} depășește costul "
            f"({visit.explain()} = {lei(visit.total)}) cu {lei(net_visit)}."
        )
        return _route(ctx, item, "R-A-VISIT", reason, "inspect_on_site", visit, th, fallback=remote_fallback)
    if smart and pr.score >= remote_min and ev - remote.total > 0:
        if pr.confidence == Confidence.medium and net_visit > min_net:
            why = f"Încredere medie (scor {pct(pr.score)}): întâi citire la distanță ({lei(remote.total)}), fără deplasare."
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
    return _final(
        item,
        DecisionType.deferred,
        "R-A-WATCH",
        f"Scor {pct(pr.score)}: valoarea așteptată ({lei(ev)}) nu justifică acum nici vizita ({lei(visit.total)}), "
        f"nici citirea la distanță (prag {pct(remote_min)}). Rămâne la urmărire.",
        "watchlist",
        {**th, "remote_min_score": remote_min},
    )


# ---- B: furtună


def _storm_window(ctx: Context, p: Proposal) -> None:
    wi = p.wi
    before = int(ctx.settings.rule("storm", "arrive_before_start_min", default=60))
    start, _ = ctx.shift()
    if wi.time_window is not None:
        p.latest = wi.time_window.start.astimezone(TZ) - timedelta(minutes=before)
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
    p = _route(ctx, item, "R-B-PREPOSITION", reason, "preposition_crew", costs, th, alerts=alerts)
    _storm_window(ctx, p)
    return p


# ---- C: tensiune


def _tap_notice_ok(ctx: Context, wi: WorkItem) -> bool:
    if wi.extra.get("planned_outage_notified"):
        return True
    level = ctx.settings.rule("voltage", "outage_voltage_level", default="lv")
    notice = int(ctx.settings.econ("outages", f"planned_notice_working_days_{level}", 2))
    return working_days_between(ctx.as_of.date(), wi.target_date) >= notice


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
        if _tap_notice_ok(ctx, wi):
            reason = (
                f"{_factors(wi)}; {vtxt} față de limita {num(limit, 2)}. Întreruperea a fost anunțată la timp; "
                f"valoarea netă a schimbării prizei e {lei(net_tap)} ({tap.explain()})."
            )
            return _route(ctx, item, "R-C-TAP", reason, "adjust_tap", tap, th, notifications=[prosumers])
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
    crews = ctx.eligible_crews(wi.effort.crew_skill.value, wi.effort.crew_size)
    if crews:
        return p
    reason = f"Nicio echipă cu abilitatea {SKILL_RO[wi.effort.crew_skill.value]} și cel puțin {wi.effort.crew_size} oameni."
    alerts = [AlertSpec("warning", f"Fără echipă potrivită: {_label(wi)}", reason)]
    if p.fallback is not None:
        p.fallback.alerts += alerts
        p.fallback.reason_ro = f"{reason} {p.fallback.reason_ro}"
        return p.fallback
    return _final(p.item, DecisionType.human_review if p.mandatory else DecisionType.deferred, "R-NO-CREW", reason, p.action, p.threshold, alerts=p.alerts + alerts)


def cap_storm_per_region(ctx: Context, proposals: list[Proposal]) -> None:
    """Cel mult `max_crews_per_region` echipe trimise din timp într-o regiune; restul rămân pentru lucrările curente."""
    cap = int(ctx.settings.rule("storm", "max_crews_per_region", default=2))
    by_region: dict[str, list[int]] = {}
    for i, p in enumerate(proposals):
        if p.route and p.action == "preposition_crew" and not p.mandatory:
            region = ctx.settings.region_of_county(p.wi.location.county) or "necunoscută"
            by_region.setdefault(region, []).append(i)
    for region, idxs in by_region.items():
        idxs.sort(key=lambda i: proposals[i].priority or 0.0, reverse=True)
        for i in idxs[cap:]:
            p = proposals[i]
            proposals[i] = _final(
                p.item,
                DecisionType.deferred,
                "R-B-REGION-CAP",
                f"{p.reason_ro} Dar în regiunea {region} sunt deja {cap} echipe trimise din timp (plafonul din config); rămâne în alertă.",
                "watchlist",
                {**p.threshold, "max_crews_per_region": float(cap)},
                alerts=p.alerts,
            )


# ------------------------------------------------------------------ intrarea principală

RULES = [rule_human_override, rule_abstain, rule_data_quality, rule_uncertain, rule_safety]


def propose(ctx: Context, item: Item) -> Proposal:
    for rule in RULES:
        p = rule(ctx, item)
        if p is not None:
            return check_crews(ctx, p)
    by_source = {Source.A: rule_meters, Source.B: rule_storm, Source.C: rule_voltage}
    return check_crews(ctx, by_source[item.wi.source](ctx, item))


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
}
