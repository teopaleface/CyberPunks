"""Ziua plecării: azi sau în tura de zonă de la sfârșitul săptămânii, fără să treacă vreodată termenul legal.

Mentorul PPC (7 nov. 2026): echipele nu pleacă automat a doua zi. Se evaluează urgența; dacă nu e ceva de tipul risc de
incendiu, lucrarea așteaptă sfârșitul săptămânii, până se adună mai multe lucrări în aceeași zonă (exemplul lui: clientul
cu contorul defect). Dar nicio lucrare nu are voie să treacă de termenul legal, orice s-ar fi stricat.

Pentru fiecare candidat de traseu care se poate amâna (`dispatch.batchable_rules`), în ordine:

1. Termenul legal: dacă ziua planului e ultima zi sigură (termenul minus `deadline_buffer_working_days`), lucrarea intră
   azi și e obligatorie (R-LEGAL-DEADLINE). Rezerva de o zi lucrătoare acoperă o echipă care nu termină la timp.
2. Ziua turei de zonă (`tour_weekdays`, implicit vineri; dacă e sărbătoare, ultima zi lucrătoare dinainte): intră azi
   (R-WEEKLY-TOUR).
3. Zona e plină: lucrările amânabile din aceeași celulă de `zone_cell_km` umplu o tură (`zone_full_share` din timpul
   de lucru); drumul se împarte deja, nu mai are rost să aștepte (R-ZONE-FULL).
4. Pe drum: o lucrare care oricum pleacă azi, cu aceeași abilitate, e la cel mult `piggyback_km`; lucrarea intră azi ca
   opțională, iar solverul o ia doar dacă ocolul e mai ieftin decât valoarea ei (R-ON-THE-WAY).
5. Altfel: amânată până la min(ziua turei, ultima zi sigură), cu termenul și costul așteptării scrise în motiv
   (R-WEEKLY-BATCH).

Nu se amână niciodată: siguranța (R-SAFETY), furtunile (B), tensiunea (C, are preaviz și ferestre proprii) și ce a aprobat
un om. Costul așteptării = valoarea așteptată pe zi (valoarea așteptată / `meters.detection_horizon_days`) × zilele de
așteptare: pierderea de energie continuă cât timp contorul nu e verificat.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from cyberpunks.common.contracts import DecisionType, WorkItem
from cyberpunks.planner.decide import Context, Proposal, _final, is_free_day
from cyberpunks.planner.settings import TZ
from cyberpunks.planner.texts import lei, num, zi

DEFAULT_BATCHABLE = ("R-A-VISIT", "R-A-VISIT-MEDIUM", "R-A-VISIT-NO-REMOTE", "R-BILANT-VISIT", "R-BILANT-GRID")


# ------------------------------------------------------------------ calendarul


def add_working_days(d: date, n: int) -> date:
    """d plus n zile lucrătoare (fără weekend și sărbători legale). n = 0 întoarce d."""
    while n > 0:
        d += timedelta(days=1)
        if not is_free_day(d):
            n -= 1
    return d


def sub_working_days(d: date, n: int) -> date:
    """d minus n zile lucrătoare; rezultatul e mereu o zi lucrătoare."""
    while n > 0 or is_free_day(d):
        d -= timedelta(days=1)
        if not is_free_day(d):
            n -= 1
    return d


def tour_day(d: date, weekdays: list[int]) -> date:
    """Ziua turei de zonă pentru o lucrare văzută în ziua d: prima zi din `weekdays` (0 = luni) de la d încolo.
    Dacă acea zi e sărbătoare, tura se face în ultima zi lucrătoare dinaintea ei (dar nu înainte de d); dacă nu există,
    în prima zi lucrătoare de după."""
    days = sorted({int(w) % 7 for w in weekdays}) or [4]
    t = d
    while t.weekday() not in days:
        t += timedelta(days=1)
    while is_free_day(t) and t > d:
        t -= timedelta(days=1)
    while is_free_day(t):
        t += timedelta(days=1)
    return t


# ------------------------------------------------------------------ termenul legal


@dataclass
class Timing:
    registered: date  # ziua sesizării (sau a primei detectări)
    limit_days: int  # zile lucrătoare până la termen
    legal: bool  # True: termen legal; False: limită internă (nu există un termen legal cunoscut)
    source_ro: str
    deadline: date  # până când trebuie făcută lucrarea
    last_safe: date  # ultima zi în care o planificăm (termenul minus rezerva)
    tour: date  # ziua turei de zonă
    due: date  # ziua plecării dacă nu o grăbește nimic: min(tour, last_safe), cel puțin ziua planului


def registered_on(wi: WorkItem) -> date:
    """Ziua de la care curge termenul: `extra.registered_at` (sesizarea clientului sau prima detectare, păstrată de la o zi
    la alta), altfel `created_at`. Varianta prudentă: la o detectare a modelului termenul curge de la detectare."""
    raw = wi.extra.get("registered_at")
    if isinstance(raw, str):
        try:
            t = datetime.fromisoformat(raw)
            return (t if t.tzinfo else t.replace(tzinfo=TZ)).astimezone(TZ).date()
        except ValueError:
            pass
    return wi.created_at.astimezone(TZ).date()


def legal_limit(ctx: Context, wi: WorkItem) -> tuple[int, bool, str]:
    """(zile lucrătoare, e termen legal, sursa). Contorul defect: termenul din standardul de performanță; restul: limita internă."""
    cfg: dict[str, Any] = ctx.settings.rule("dispatch", "legal_deadlines", default={}) or {}
    faulty = wi.prediction.label in ("faulty", "contor_defect", "contor_client")
    meter = cfg.get("meter_faulty") or {}
    if faulty and meter:
        days = int(meter.get("days", 10))
        kw = wi.extra.get("approved_power_kw")
        if isinstance(kw, (int, float)) and kw > float(meter.get("large_customer_kw", 100)):
            days = int(meter.get("large_customer_days", days))
        return days, True, str(meter.get("source_ro", "standardul de performanță ANRE"))
    days = int(ctx.settings.rule("dispatch", "internal_max_working_days", default=10))
    return days, False, "limită internă (nu știm de un termen legal pentru acest tip de lucrare)"


def timing(ctx: Context, wi: WorkItem) -> Timing:
    reg = registered_on(wi)
    days, legal, source = legal_limit(ctx, wi)
    buffer = int(ctx.settings.rule("dispatch", "deadline_buffer_working_days", default=1))
    deadline = add_working_days(reg, days)
    last_safe = sub_working_days(deadline, buffer) if buffer > 0 else deadline
    tour = tour_day(ctx.plan_date, ctx.settings.rule("dispatch", "tour_weekdays", default=[4]))
    due = max(ctx.plan_date, min(tour, last_safe))
    return Timing(reg, days, legal, source, deadline, last_safe, tour, due)


def waiting_cost_lei(ctx: Context, wi: WorkItem, days: int) -> float:
    """Pierderea estimată cât lucrarea așteaptă: valoarea așteptată pe zi × zilele de așteptare (calendaristice)."""
    horizon = ctx.settings.econ("meters", "detection_horizon_days", 90.0)
    return max(0.0, wi.impact.expected_value_lei) / max(1.0, horizon) * max(0, days)


# ------------------------------------------------------------------ zone și „pe drum”


def zone_key(ctx: Context, wi: WorkItem) -> tuple[str, int, int]:
    """Zona operativă tăiată în celule de `zone_cell_km` (o zonă ca B-S6 poate fi încă prea mare pentru o singură tură)."""
    cell = float(ctx.settings.rule("dispatch", "zone_cell_km", default=5.0))
    dlat = cell / 111.0
    dlon = cell / (111.0 * max(0.2, math.cos(math.radians(wi.location.lat))))
    return wi.location.zone_id, math.floor(wi.location.lat / dlat), math.floor(wi.location.lon / dlon)


def _skill(p: Proposal) -> str:
    return p.skill or p.wi.effort.crew_skill.value


def _minutes(p: Proposal) -> int:
    return int(p.duration_min or p.wi.effort.duration_min)


# ------------------------------------------------------------------ pasul propriu-zis


def schedule_dispatch(ctx: Context, proposals: list[Proposal]) -> dict[str, Any]:
    """Hotărăște ziua plecării pentru lucrările care se pot amâna; le înlocuiește pe cele amânate cu o decizie `deferred`.
    Întoarce un rezumat pentru plan (câte azi, câte amânate și de ce)."""
    summary: dict[str, Any] = {"enabled": False, "today": {}, "deferred": 0, "waiting_cost_lei": 0.0}
    if not bool(ctx.settings.rule("dispatch", "weekly_batching", default=False)):
        return summary
    summary["enabled"] = True
    batchable_rules = set(ctx.settings.rule("dispatch", "batchable_rules", default=list(DEFAULT_BATCHABLE)) or [])
    batch = [i for i, p in enumerate(proposals) if p.route and not p.mandatory and p.rule_id in batchable_rules]
    if not batch:
        return summary
    timings = {i: timing(ctx, proposals[i].wi) for i in batch}
    today: dict[int, str] = {}

    # 1. termenul legal și 2. ziua turei
    for i in batch:
        tm = timings[i]
        if tm.last_safe <= ctx.plan_date:
            today[i] = "R-LEGAL-DEADLINE"
        elif tm.tour <= ctx.plan_date:
            today[i] = "R-WEEKLY-TOUR"

    # 3. zona plină: lucrările amânabile din aceeași celulă umplu o tură
    start, end = ctx.shift()
    shift_min = max(60.0, (end - start).total_seconds() / 60.0)
    full_share = float(ctx.settings.rule("dispatch", "zone_full_share", default=0.75))
    local_min = float(ctx.settings.rule("dispatch", "zone_local_travel_min", default=15))
    zones: dict[tuple[str, str, int, int], list[int]] = {}
    for i in batch:
        z = zone_key(ctx, proposals[i].wi)
        zones.setdefault((_skill(proposals[i]), *z), []).append(i)
    zone_load: dict[int, float] = {}
    for members in zones.values():
        load = sum(_minutes(proposals[i]) + local_min for i in members)
        for i in members:
            zone_load[i] = load
            if i not in today and load >= full_share * shift_min:
                today[i] = "R-ZONE-FULL"

    # 4. pe drum: lângă o lucrare care oricum pleacă azi, cu aceeași abilitate
    radius = float(ctx.settings.rule("dispatch", "piggyback_km", default=3.0))
    anchors = [p for k, p in enumerate(proposals) if p.route and (k not in timings or k in today)]
    near: dict[int, float] = {}
    for i in batch:
        if i in today:
            continue
        wi = proposals[i].wi
        best = min(
            (ctx.travel.road_km(a.wi.location.lat, a.wi.location.lon, wi.location.lat, wi.location.lon)
             for a in anchors if _skill(a) == _skill(proposals[i]) and a.id != proposals[i].id),
            default=None,
        )
        if best is not None and best <= radius:
            today[i] = "R-ON-THE-WAY"
            near[i] = best

    # Textele și înlocuirea celor amânate
    buffer = int(ctx.settings.rule("dispatch", "deadline_buffer_working_days", default=1))
    for i in batch:
        p = proposals[i]
        tm = timings[i]
        term = (f"termenul legal e {zi(tm.deadline)} ({tm.limit_days} zile lucrătoare de la sesizarea din {zi(tm.registered)}, "
                f"{tm.source_ro})" if tm.legal else
                f"limita internă e {zi(tm.deadline)} ({tm.limit_days} zile lucrătoare de la detectarea din {zi(tm.registered)})")
        base = {"dispatch_limit_working_days": float(tm.limit_days), "dispatch_legal_deadline": 1.0 if tm.legal else 0.0,
                "deadline_buffer_working_days": float(buffer)}
        rule = today.get(i)
        if rule == "R-LEGAL-DEADLINE":
            p.mandatory = True
            p.reason_ro = (f"{p.reason_ro} Nu e urgentă ca risc, dar {term}: azi e ultima zi planificată cu rezervă, "
                           "deci intră obligatoriu în traseu.")
            p.rule_id = "R-LEGAL-DEADLINE"
        elif rule == "R-WEEKLY-TOUR":
            p.reason_ro = f"{p.reason_ro} Azi e tura de zonă a săptămânii: lucrările adunate se fac împreună; {term}."
        elif rule == "R-ZONE-FULL":
            p.reason_ro = (f"{p.reason_ro} Zona are deja lucrări pentru o tură (~{num(zone_load[i] / 60, 1)} ore din "
                           f"{num(shift_min / 60, 1)}): drumul se împarte, nu mai are rost să aștepte; {term}.")
        elif rule == "R-ON-THE-WAY":
            p.reason_ro = (f"{p.reason_ro} O echipă trece oricum azi la ~{num(near[i], 1)} km: o luăm pe drum dacă ocolul "
                           f"costă mai puțin decât valoarea ei; altfel așteaptă tura de zonă; {term}.")
        if rule:
            p.threshold.update({**base, "dispatch_today": 1.0})
            p.threshold["dispatch_" + rule.removeprefix("R-").lower().replace("-", "_")] = 1.0
            summary["today"][rule] = summary["today"].get(rule, 0) + 1
            continue
        wait_days = (tm.due - ctx.plan_date).days
        cost = waiting_cost_lei(ctx, p.wi, wait_days)
        reason = (f"{p.reason_ro} Nu e urgent (nu e risc de incendiu sau pentru oameni): așteaptă tura de zonă din {zi(tm.due)}, "
                  f"împreună cu celelalte lucrări din zonă, ca echipa să facă un singur drum. Termenul nu se depășește: {term}, "
                  f"cu rezervă de {buffer} zi lucrătoare. Costul așteptării: ~{lei(cost)} ({wait_days} zile de pierdere estimată).")
        threshold = {**p.threshold, **base, "dispatch_wait_days": float(wait_days), "waiting_cost_lei": round(cost, 2)}
        proposals[i] = _final(p.item, DecisionType.deferred, "R-WEEKLY-BATCH", reason, p.action, threshold,
                              costs=p.costs, priority=p.priority, alerts=p.alerts, notifications=p.notifications)
        summary["deferred"] += 1
        summary["waiting_cost_lei"] = round(summary["waiting_cost_lei"] + cost, 2)
    return summary
