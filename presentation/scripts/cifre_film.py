"""Scrie în film cifra principală, citită din reports/ (niciodată de mână).

Cifra: cât câștigă agentul față de cea mai bună strategie simplă, ca valoare netă (reports/planner/agent_eval.json).
Rulare (din rădăcina repo-ului): uv run python presentation/scripts/cifre_film.py
Tipărește cifra și fișierul din care vine; dacă raportul lipsește, oprește exportul (cod 1).
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
EVAL = ROOT / "reports" / "planner" / "agent_eval.json"
SCENE = ROOT / "presentation" / "video" / "compositions" / "k9-final.html"


def main() -> int:
    if not EVAL.exists():
        print(f"Lipsește {EVAL.relative_to(ROOT)}: filmul nu primește cifra.", file=sys.stderr)
        return 1
    d = json.loads(EVAL.read_text())
    strat = d["main"]["strategies"]
    agent = strat["agent"]["net_value_lei_total"]
    best_name, best = max(((k, v["net_value_lei_total"]) for k, v in strat.items() if k != "agent"), key=lambda kv: kv[1])
    pct = round(100 * (agent - best) / best)
    html = SCENE.read_text()
    html = re.sub(r'(<div id="k9-num" data-value=")[^"]*(")', rf"\g<1>{pct}\g<2>", html)
    html = re.sub(r'(<div id="k9-num"[^>]*>)[^<]*(</div>)', rf"\g<1>+{pct}%\g<2>", html)
    days = d["main"]["days"]
    html = re.sub(r'(<div id="k9-src">)[^<]*(</div>)', rf"\g<1>simulare pe {days} de zile, într-o lume sintetică cu adevărul cunoscut\g<2>", html)
    SCENE.write_text(html)
    print(f"+{pct}% (agent {agent:.0f} lei față de '{best_name}' {best:.0f} lei, {days} zile) din {EVAL.relative_to(ROOT)}")
    print(f"comanda care refăce cifra: {d.get('reproduce_cmd')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
