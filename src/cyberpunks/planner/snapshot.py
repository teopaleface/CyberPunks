"""Instantaneul pentru demo: copiază rezultatele unui scenariu din outputs/ în outputs/demo/ (care intră în git).

    uv run python -m cyberpunks.planner.snapshot --scenario demo-vara     # sau: make demo-snapshot

Interfața și juriul pot vedea planul fără să ruleze modelele: API-ul citește outputs/demo/ când nu există o rulare
locală, iar interfața îl folosește ca rezervă. Structura e aceeași ca în outputs/ (vezi cyberpunks.api.store).
Se copiază: planul cu jurnalul, alertele, notificările, raportul și ordinele de lucru; lucrările primite; seriile
pentru grafice (doar ale lucrărilor din plan); rapoartele modelelor (reports/<X>/metrics.json) și evaluarea agentului.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

from cyberpunks.common.paths import OUTPUTS, REPORTS
from cyberpunks.planner.settings import TZ

PLAN_FILES = ["plan.json", "audit.jsonl", "work_items.jsonl", "quarantine.jsonl", "alerts.json", "notifications.json",
              "report.md", "run.json", "remedies.json", "approvals.json", "labels.jsonl", "actions.json", "titles.json", "posts.json", "plan_approval.json"]
REPORT_FILES = {
    "A": ["metrics.json"], "B": ["metrics.json"], "C": ["metrics.json"], "bilant": ["metrics.json"],
    "planner": ["agent_eval.json", "agent_eval.md", "agent_eval.png", "solver_benchmark.json", "README.md"],
}


def snapshot(scenario: str, src: Path = OUTPUTS, dest: Path | None = None, reports: Path = REPORTS) -> list[Path]:
    dest = dest or src / "demo"
    plan_src = src / "plans" / scenario
    if not (plan_src / "plan.json").exists():
        raise SystemExit(f"nu există {plan_src / 'plan.json'}: rulează întâi `uv run cyberpunks run --scenario {scenario}`")
    written: list[Path] = []
    plan_dst = dest / "plans" / scenario
    if plan_dst.exists():
        shutil.rmtree(plan_dst)
    plan_dst.mkdir(parents=True)
    for name in PLAN_FILES:
        if (plan_src / name).exists():
            shutil.copyfile(plan_src / name, plan_dst / name)
            written.append(plan_dst / name)
    if (plan_src / "work_orders").exists():
        shutil.copytree(plan_src / "work_orders", plan_dst / "work_orders")
        written += sorted((plan_dst / "work_orders").glob("*.pdf"))
    ids = {json.loads(x)["work_item_id"] for x in (plan_src / "work_items.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()}
    series_src, series_dst = src / "series" / scenario, dest / "series" / scenario
    if series_dst.exists():
        shutil.rmtree(series_dst)
    if series_src.exists():
        series_dst.mkdir(parents=True)
        for f in series_src.glob("*.json"):
            if f.stem in ids:
                shutil.copyfile(f, series_dst / f.name)
                written.append(series_dst / f.name)
    for folder, names in REPORT_FILES.items():
        for name in names:
            f = reports / folder / name
            if f.exists():
                (dest / "reports" / folder).mkdir(parents=True, exist_ok=True)
                shutil.copyfile(f, dest / "reports" / folder / name)
                written.append(dest / "reports" / folder / name)
    plan = json.loads((plan_src / "plan.json").read_text(encoding="utf-8"))
    run = json.loads((plan_src / "run.json").read_text(encoding="utf-8")) if (plan_src / "run.json").exists() else {}
    origins = ", ".join(f"{k}: {v.get('origin')}" for k, v in (run.get("sources") or {}).items() if not v.get("optional"))
    (dest / "README.md").write_text(
        "# Instantaneul demo\n\n"
        f"Scenariul `{scenario}`, planul `{plan['plan_id']}` pentru {plan['plan_date']}, copiat la {datetime.now(TZ):%Y-%m-%d %H:%M} "
        f"cu `uv run python -m cyberpunks.planner.snapshot --scenario {scenario}`.\n\n"
        f"Sursele lucrărilor: {origins or '-'}. Activele (contoare, posturi), echipele și bazele sunt SINTETICE, plasate pe hartă reală; "
        "vremea și zilele sunt reale. Nimic nu a fost trimis în afară (notificările sunt `demo_only`).\n\n"
        "Structura e aceeași ca în `outputs/`: `plans/<s>/` (plan, jurnal, alerte, notificări, raport, ordine de lucru PDF), "
        "`series/<s>/` (graficele lucrărilor), `reports/` (metricile modelelor și evaluarea agentului). "
        "API-ul le servește când nu există o rulare locală (`GET /api/health` → `mode: demo`).\n",
        encoding="utf-8",
    )
    written.append(dest / "README.md")
    return written


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Copiază rezultatele unui scenariu în outputs/demo/.")
    ap.add_argument("--scenario", default="demo-vara")
    args = ap.parse_args(argv)
    files = snapshot(args.scenario)
    size = sum(f.stat().st_size for f in files if f.exists())
    print(f"Copiat {len(files)} fișiere ({size / 1e6:.1f} MB) în {OUTPUTS / 'demo'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
