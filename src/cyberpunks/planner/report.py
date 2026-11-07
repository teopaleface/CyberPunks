"""Raportul zilei (report.md): cifrele planului, traseele, ce merge la om, alertele, timpii. Doar din plan, fără LLM."""

from __future__ import annotations

from collections import Counter
from typing import Any

from cyberpunks.common.contracts import Plan
from cyberpunks.planner.ingest import Item
from cyberpunks.planner.texts import SOURCE_RO, hhmm, lei, num, zi

DECISION_RO = {
    "assigned": "în traseu",
    "deferred": "amânat",
    "human_review": "la om",
    "remote_action": "citire la distanță",
    "notify": "mesaj",
    "rejected_invalid": "carantină",
}
MAX_LIST = 25  # listele lungi se scurtează în raport; planul și API-ul le au complete
KIND_RO = {"meter_inspection": "verificare contor", "storm_prepositioning": "echipă trimisă din timp", "voltage_mitigation": "tensiune la post"}
STATUS_RO = {"ok": "ok", "degraded": "incompletă", "missing": "lipsește"}
ORIGIN_RO = {"model": "modelul nostru", "stale": "ieșire mai veche a modelului", "fixture": "exemple de test (fixture)", "missing": "-"}


def render_report(plan: Plan, items: list[Item], meta: dict[str, Any], timings: dict[str, float]) -> str:
    by_id = {it.id: it.wi for it in items}
    s = plan.summary
    lines = [
        f"# Planul pentru {zi(plan.plan_date)}",
        "",
        f"Scenariu: `{plan.scenario}`. Plan `{plan.plan_id}`, generat la {plan.generated_at:%Y-%m-%d %H:%M} de `{plan.planner_version}`.",
        "Activele și echipele din demo sunt sintetice, plasate pe hartă reală. Nimic nu a fost trimis în afară.",
        "",
        "## Pe scurt",
        "",
        f"- Lucrări primite: {s.items_in} ({s.items_valid} valide, {s.items_invalid} în carantină).",
        f"- În trasee: {s.assigned}, cu {s.crews_used} echipe și {num(s.total_km, 1)} km; valoare așteptată {lei(s.expected_value_lei)}.",
        f"- Citiri la distanță: {s.remote_actions}. Mesaje (demo): {s.notifications}. La om: {s.human_review}. Amânate: {s.deferred}.",
        "",
        "## Sursele",
        "",
        "| Sursă | Stare | De unde | Valide | Respinse |",
        "|---|---|---|---|---|",
    ]
    for key, info in (meta.get("sources") or {}).items():
        if info.get("optional") and info.get("origin") == "missing":
            continue
        label = "A, bilanț pe post" if key == "A_bilant" else f"{key} ({SOURCE_RO.get(key, key)})"
        status = plan.sources_status.get(key, info.get("status", "missing")) if key in "ABC" else info.get("status", "missing")
        lines.append(
            f"| {label} | {STATUS_RO.get(status, status)} | {ORIGIN_RO.get(info.get('origin', 'missing'), '-')} "
            f"| {info.get('valid', 0)} | {info.get('invalid', 0)} |"
        )
    dec = {d.work_item_id: d for d in plan.decisions}
    remote = [d for d in plan.decisions if d.decision.value == "remote_action"]
    lines += ["", "## Întâi: verificări de la distanță și corecții în birou", ""]
    if not remote:
        lines.append("Niciuna.")
    for d in remote[:MAX_LIST]:
        lines.append(f"- `{d.work_item_id}` (`{d.rule_id}`): {d.reason_ro}")
    if len(remote) > MAX_LIST:
        lines.append(f"- … și încă {len(remote) - MAX_LIST} (toate sunt în `plan.json` și în consolă).")
    ranked = sorted((d for d in plan.decisions if d.rank is not None), key=lambda d: d.rank or 0)
    lines += ["", "## Lista pe echipe, după lei pe oră de lucru", "", "| Rang | Lucrare | Lei pe oră | Decizie | Echipa |", "|---|---|---|---|---|"]
    for d in ranked[: 2 * MAX_LIST]:
        lph = d.threshold.get("lei_per_work_hour")
        lines.append(f"| {d.rank} | `{d.work_item_id}` | {num(lph) if lph is not None else '-'} | {DECISION_RO.get(d.decision.value, d.decision.value)} | {d.crew_id or '-'} |")
    lines += ["", "Lista o aprobă un om (consola: aprobă traseul echipei); verdictul de după vizită intră în jurnal ca etichetă pentru reantrenare."]
    lines += ["", "## Traseele", ""]
    if not plan.routes:
        lines.append("Nicio echipă nu are lucrări mâine.")
    for r in plan.routes:
        n_stops = "1 oprire" if len(r.stops) == 1 else f"{len(r.stops)} opriri"
        lines.append(f"### {r.crew_id} (baza {r.depot_id}): {n_stops}, {num(r.total_km, 1)} km, {r.total_travel_min} min de drum")
        lines.append("")
        lines.append("| # | Sosire | Lucrare | Ce | Regula |")
        lines.append("|---|---|---|---|---|")
        for st in r.stops:
            wi = by_id.get(st.work_item_id)
            label = (wi.location.label or wi.asset_id) if wi else st.work_item_id
            what = KIND_RO.get(wi.kind.value, wi.kind.value) if wi else ""
            if wi is not None and wi.asset_type.value == "transformer_post" and wi.source.value == "A":
                what = "bilanț pe post"
            lines.append(f"| {st.seq} | {hhmm(st.eta)} | {label} | {what} | `{dec[st.work_item_id].rule_id}` |")
        lines.append("")
    review = [d for d in plan.decisions if d.decision.value == "human_review"]
    lines += ["## La om (\"nu sunt sigur\")", ""]
    if not review:
        lines.append("Niciun caz.")
    for d in review[:MAX_LIST]:
        lines.append(f"- `{d.work_item_id}`: {d.reason_ro}")
    if len(review) > MAX_LIST:
        lines.append(f"- … și încă {len(review) - MAX_LIST} (toate sunt în coada „nu sunt sigur” din consolă).")
    lines += ["", "## Alerte", ""]
    if not plan.alerts:
        lines.append("Nicio alertă.")
    for a in plan.alerts:
        lines.append(f"- **{a.severity}** {a.title_ro}. {a.body_ro}")
    remedies = meta.get("remedies") or []
    if remedies:
        lines += ["", "## Scara de soluții pentru tensiune", "", "| Post | Aleasă | Cost | P90 înainte → după | De ce nu una mai ieftină |", "|---|---|---|---|---|"]
        for r in remedies:
            why = "; ".join(r.get("why_not_cheaper") or []) or "e cea mai ieftină treaptă"
            lines.append(f"| {r['label']} | {', '.join(r['chosen'])} | {lei(r['cost_lei'])} | {num(r['p90_before_pu'], 3)} → {num(r['p90_after_pu'], 3)} pu | {why} |")
        offers = [r for r in remedies if r.get("battery")]
        lines += ["", "### Pentru PPC Energie: oferte de baterii", ""]
        if not offers:
            lines.append("Niciun post unde bateriile sunt treapta aleasă.")
        for r in offers:
            b = r["battery"]
            parts = [f"{num(b['battery_kwh_total'])} kWh" if b.get("battery_kwh_total") else None,
                     f"{b['customers_targeted']} prosumatori" if b.get("customers_targeted") else None,
                     f"venit estimat {lei(b['revenue_lei'])}" if b.get("revenue_lei") else None,
                     f"recuperare ~{num(b['payback_years'], 1)} ani" if b.get("payback_years") else None]
            lines.append(f"- {r['label']}: " + ", ".join(x for x in parts if x) + ". Canal: magazinele PPC (demo, nu s-a trimis nimic).")
        invest = [r for r in remedies if r.get("invest") or not r.get("feasible")]
        lines += ["", "### Investiții (raportul firului C)", ""]
        if not invest:
            lines.append("Niciun post nu are nevoie de investiție.")
        for r in invest:
            lines.append(f"- {r['label']}: " + ("transformator nou" if r.get("invest") else "nicio combinație de trepte nu ajunge") + f" (P90 {num(r['p90_before_pu'], 3)} pu).")
    office = [d for d in plan.decisions if d.rule_id == "R-BILANT-OFFICE"]
    if office:
        lines += ["", "## Coada biroului de date (corecții fără deplasare)", ""] + [f"- `{d.work_item_id}`: {d.reason_ro}" for d in office]
    fusion = meta.get("fusion") or {}
    lines += ["", f"Fuziunea cu bilanțul pe post: {fusion.get('status', '-')}" + (f", {fusion.get('fused', 0)} contoare confirmate" if fusion.get("status") == "ok" else "") + "."]
    rules = Counter(d.rule_id for d in plan.decisions)
    lines += ["", "## Regulile folosite", "", "| Regula | Decizii |", "|---|---|"]
    lines += [f"| `{r}` | {n} |" for r, n in rules.most_common()]
    solver = meta.get("solver", {})
    lines += [
        "",
        "## Cum a lucrat agentul",
        "",
        f"- Timpi (secunde): Perceive {timings.get('perceive', 0):.2f}, Estimate {timings.get('estimate', 0):.2f}, Decide {timings.get('decide', 0):.2f}, Act {timings.get('act', 0):.2f}.",
        f"- Optimizator: {solver.get('name', '-')} ({solver.get('status', '-')}), {solver.get('tasks', 0)} lucrări candidate, {solver.get('crews', 0)} echipe, {solver.get('seconds', 0):.2f} s.",
        "- Ipotezele de cost: `config/economics.yaml` (cu sursele); pragurile: `config/planner.yaml`.",
        "- Fiecare decizie are în jurnal (`audit.jsonl`) ID-ul predicției, versiunea modelului, regula și pragurile.",
        "",
    ]
    return "\n".join(lines)
