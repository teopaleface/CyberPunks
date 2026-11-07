"""Contextul zilei: câte o frază pe sursă care spune de ce planul arată așa (de exemplu puține lucrări de tensiune în noiembrie).

Doar cifre din lucrări, din deciziile agentului și din rezumatele publicate de fire (`<sursă>_summary.json` lângă lucrări),
fără LLM. Apare ca alertă informativă („Contextul zilei”), în raportul zilei și în run.json.
"""

from __future__ import annotations

import json
import math
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
    """Rezumatul publicat de un fir lângă lucrările lui; orice lipsă sau formă greșită înseamnă „fără rezumat”, nu o eroare."""
    if not path_str:
        return {}
    p = Path(path_str).parent / name
    try:
        data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _num(value: Any) -> float | None:
    """Un număr finit sau None (textele, valorile booleene, NaN și infinitul nu trec)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) else None


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
        posts = _num(summary.get("posts"))
        weather = summary.get("weather") if isinstance(summary.get("weather"), dict) else {}
        gti, temp = _num(weather.get("gti_max")), _num(weather.get("temp_noon"))
        crews = sum(1 for p in c if p.decision == DecisionType.assigned)
        notify = sum(1 for p in c if p.decision == DecisionType.notify)
        watch = sum(1 for p in c if p.decision == DecisionType.deferred)
        head = f"Tensiune: {len(c)} posturi cu risc" + (f" din {round(posts)}" if posts else "")
        sun = ""
        if gti is not None:
            sun = f" (soare pe panou până la {num(gti)} W/m² la prânz" + (f", {num(temp)} °C" if temp is not None else "") + ")"
        # Motivele urmăririi vin din regulile chiar aplicate, nu din lună: fiecare număr e un număr de decizii.
        rules = Counter(p.rule_id for p in c if p.decision == DecisionType.deferred)
        below = rules.get("R-C-WATCH", 0)
        unsure = sum(n for r, n in rules.items() if r.startswith(("R-WIDE-INTERVAL", "R-LOW-CONFIDENCE")))
        why = [f"{below} sub prag sau sub limită chiar și în scenariul pesimist" if below else "",
               f"{unsure} cu incertitudine prea mare" if unsure else "",
               f"{watch - below - unsure} din alte motive" if watch - below - unsure > 0 else ""]
        why_ro = f" ({', '.join(x for x in why if x)})" if watch else ""
        tally = f"{watch} posturi rămân la urmărire{why_ro}, {notify} primesc mesaje către prosumatori, {crews} primesc echipă."
        if d.month not in PV_SEASON:
            horizon = [h for h in (_num(p.wi.extra.get("season_horizon_days")) for p in c) if h is not None]
            left = f"; mai sunt ~{round(min(horizon))} zile cu soare puternic în sezonul acesta" if horizon else ""
            lines.append(f"{head}{sun}. În {month} sezonul fotovoltaic e la final{left}: {tally}")
        else:
            lines.append(f"{head}{sun}: {tally}")
    for key, info in sources.items():
        if key == "A_bilant" and info.get("origin") == "missing" and "eroare" in (info.get("note") or ""):
            lines.append("Bilanțul pe post n-a rulat pentru ziua asta (eroare a modelului); planul de contoare merge fără confirmarea bilanțului.")
    return lines
