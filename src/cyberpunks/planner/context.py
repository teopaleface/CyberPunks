"""Contextul zilei: câte o frază pe sursă care spune de ce planul arată așa (de exemplu puține lucrări de tensiune în noiembrie).

Doar cifre din lucrări, din deciziile agentului și din rezumatele publicate de fire (`<sursă>_summary.json` lângă lucrări),
fără LLM. Apare ca alertă informativă („Contextul zilei”), în raportul zilei și în run.json.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from cyberpunks.common.contracts import DecisionType, Source
from cyberpunks.planner.decide import Context, Proposal
from cyberpunks.planner.texts import num, pct

MONTHS_RO = ["ianuarie", "februarie", "martie", "aprilie", "mai", "iunie", "iulie", "august", "septembrie", "octombrie", "noiembrie", "decembrie"]
PV_SEASON = range(3, 10)  # martie-septembrie: sezonul cu prânzuri însorite (aceeași ipoteză ca firul C)


def _summary(path_str: str | None, name: str) -> dict[str, Any]:
    if not path_str:
        return {}
    p = Path(path_str).parent / name
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except (OSError, ValueError):
        return {}


def day_context(ctx: Context, final: dict[str, Proposal], sources: dict[str, dict[str, Any]]) -> list[str]:
    """Frazele contextului, câte una pe sursă care are lucrări sau o explicație utilă."""
    lines: list[str] = []
    by_src: dict[str, list[Proposal]] = {}
    for p in final.values():
        by_src.setdefault(p.wi.source.value, []).append(p)
    d: date = ctx.plan_date
    month = MONTHS_RO[d.month - 1]

    a = by_src.get(Source.A.value, [])
    if a:
        kinds = Counter(p.decision for p in a)
        lines.append(
            f"Contoare și posturi: {len(a)} lucrări; {kinds.get(DecisionType.assigned, 0)} în trasee, "
            f"{kinds.get(DecisionType.remote_action, 0)} verificări de la distanță sau corecții în birou, "
            f"{kinds.get(DecisionType.human_review, 0)} la dispecer."
        )

    b = by_src.get(Source.B.value, [])
    if b:
        top = max(p.wi.prediction.score for p in b)
        sent = sum(1 for p in b if p.decision == DecisionType.assigned)
        alert_min = float(ctx.settings.rule("storm", "alert_min_score", default=0.4))
        if sent == 0 and top < alert_min:
            lines.append(f"Furtună: vreme liniștită în cele {len(b)} zone; cel mai mare risc de avarii e {pct(top)}, sub pragul de alertă ({pct(alert_min)}). Nicio echipă trimisă din timp.")
        else:
            lines.append(f"Furtună: {len(b)} zone analizate, cel mai mare risc {pct(top)}; {sent} echipe trimise din timp.")

    c = by_src.get(Source.C.value, [])
    if c:
        summary = _summary((sources.get("C") or {}).get("path"), "C_summary.json")
        posts = summary.get("posts")
        weather = summary.get("weather") or {}
        crews = sum(1 for p in c if p.decision == DecisionType.assigned)
        notify = sum(1 for p in c if p.decision == DecisionType.notify)
        watch = sum(1 for p in c if p.decision == DecisionType.deferred)
        head = f"Tensiune: {len(c)} posturi cu risc" + (f" din {posts}" if posts else "")
        sun = ""
        if weather.get("gti_max") is not None:
            sun = f" (soare pe panou până la {num(float(weather['gti_max']))} W/m² la prânz" + (
                f", {num(float(weather['temp_noon']))} °C" if weather.get("temp_noon") is not None else "") + ")"
        if d.month not in PV_SEASON:
            horizon = [p.wi.extra.get("season_horizon_days") for p in c if isinstance(p.wi.extra.get("season_horizon_days"), (int, float))]
            left = f"; mai sunt ~{round(min(horizon))} zile de soare puternic până la primăvară" if horizon else ""
            lines.append(
                f"{head}{sun}. În {month} sezonul fotovoltaic e la final{left}: o echipă pentru priză sau faze nu se mai plătește, "
                f"deci agentul trimite {notify} mesaje către prosumatori, pune {watch} posturi la urmărire și {crews} echipe."
            )
        else:
            lines.append(f"{head}{sun}: {crews} echipe, {notify} mesaje către prosumatori, {watch} posturi la urmărire.")
    for key, info in sources.items():
        if key == "A_bilant" and info.get("origin") == "missing" and "eroare" in (info.get("note") or ""):
            lines.append("Bilanțul pe post n-a rulat pentru ziua asta (eroare a modelului); planul de contoare merge fără confirmarea bilanțului.")
    return lines
