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
    for src in "ABC":
        info = (meta.get("sources") or {}).get(src, {})
        lines.append(
            f"| {src} ({SOURCE_RO[src]}) | {STATUS_RO[plan.sources_status[src]]} | {ORIGIN_RO.get(info.get('origin', 'missing'), '-')} "
            f"| {info.get('valid', 0)} | {info.get('invalid', 0)} |"
        )
    lines += ["", "## Traseele", ""]
    dec = {d.work_item_id: d for d in plan.decisions}
    if not plan.routes:
        lines.append("Nicio echipă nu are lucrări mâine.")
    for r in plan.routes:
        lines.append(f"### {r.crew_id} (baza {r.depot_id}): {len(r.stops)} opriri, {num(r.total_km, 1)} km, {r.total_travel_min} min de drum")
        lines.append("")
        lines.append("| # | Sosire | Lucrare | Ce | Regula |")
        lines.append("|---|---|---|---|---|")
        for st in r.stops:
            wi = by_id.get(st.work_item_id)
            label = (wi.location.label or wi.asset_id) if wi else st.work_item_id
            what = wi.kind.value if wi else ""
            lines.append(f"| {st.seq} | {hhmm(st.eta)} | {label} | {what} | `{dec[st.work_item_id].rule_id}` |")
        lines.append("")
    review = [d for d in plan.decisions if d.decision.value == "human_review"]
    lines += ["## La om (\"nu sunt sigur\")", ""]
    if not review:
        lines.append("Niciun caz.")
    for d in review:
        lines.append(f"- `{d.work_item_id}`: {d.reason_ro}")
    lines += ["", "## Alerte", ""]
    if not plan.alerts:
        lines.append("Nicio alertă.")
    for a in plan.alerts:
        lines.append(f"- **{a.severity}** {a.title_ro}. {a.body_ro}")
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
