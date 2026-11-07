"""De unde citește API-ul datele unui scenariu.

Ordinea, pentru fiecare scenariu:
1. "live":     outputs/plans/<scenariu>/plan.json (ultima rulare a agentului pe mașina asta);
2. "demo":     outputs/demo/plans/<scenariu>/plan.json (instantaneul din git, aceeași structură ca outputs/);
3. "fixtures": contracts/fixtures/ (exemple ilustrative, până există ieșiri reale).

outputs/ și outputs/demo/ au aceeași structură:
    plans/<s>/{plan.json, audit.jsonl, work_items.jsonl, quarantine.jsonl, alerts.json, notifications.json, report.md}
    plans/<s>/work_orders/<crew_id>.pdf
    work_items/<s>/{A,B,C}.jsonl
    series/<s>/<work_item_id>.json
    reports/{A,B,C}/metrics.json, reports/planner/agent_eval.json   (doar în outputs/demo/)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from cyberpunks.api.fixture_series import make_series
from cyberpunks.common.paths import CONTRACTS, OUTPUTS, REPORTS, ROOT

Mode = Literal["live", "demo", "fixtures"]
FIXTURES = CONTRACTS / "fixtures"
DEMO = OUTPUTS / "demo"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # linia stricată apare în carantina planificatorului, nu aici
    return out


def read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


@dataclass
class ScenarioView:
    scenario: str
    mode: Mode
    root: Path  # outputs/ sau outputs/demo/ (nefolosit în modul fixtures)

    @property
    def plan_dir(self) -> Path:
        return self.root / "plans" / self.scenario

    # ---------------- plan, lucrări, jurnal ----------------

    def plan(self) -> dict[str, Any] | None:
        if self.mode == "fixtures":
            return read_json(FIXTURES / "plan_example.json")
        return read_json(self.plan_dir / "plan.json")

    def work_items(self) -> list[dict[str, Any]]:
        if self.mode == "fixtures":
            items: list[dict[str, Any]] = []
            for src in "ABC":
                items += read_jsonl(FIXTURES / f"work_items_{src}.jsonl")
            return items
        used = self.plan_dir / "work_items.jsonl"
        if used.exists():
            return read_jsonl(used)
        items = []
        for src in "ABC":
            items += read_jsonl(self.root / "work_items" / self.scenario / f"{src}.jsonl")
        return items

    def audit(self) -> list[dict[str, Any]]:
        if self.mode == "fixtures":
            return read_jsonl(FIXTURES / "audit_example.jsonl")
        return read_jsonl(self.plan_dir / "audit.jsonl")

    def quarantine(self) -> list[dict[str, Any]]:
        if self.mode == "fixtures":
            return [
                {"source": "A", "line": i, "work_item_id": raw.get("work_item_id"), "errors": ["exemplu de intrare greșită din fixture"], "raw": raw}
                for i, raw in enumerate(read_jsonl(FIXTURES / "work_items_invalid.jsonl"), 1)
            ]
        return read_jsonl(self.plan_dir / "quarantine.jsonl")

    def report_md(self) -> str | None:
        p = self.plan_dir / "report.md"
        return p.read_text(encoding="utf-8") if self.mode != "fixtures" and p.exists() else None

    def work_order_pdf(self, crew_id: str) -> Path | None:
        if self.mode == "fixtures":
            return None
        p = self.plan_dir / "work_orders" / f"{crew_id}.pdf"
        return p if p.exists() else None

    # ---------------- serii ----------------

    def series(self, work_item_id: str) -> dict[str, Any] | None:
        if self.mode != "fixtures":
            found = read_json(self.root / "series" / self.scenario / f"{work_item_id}.json")
            if found is not None:
                return found
        item = next((w for w in self.work_items() if w.get("work_item_id") == work_item_id), None)
        if item is None:
            return None
        ref = (item.get("extra") or {}).get("series_ref")
        if ref and self.mode != "fixtures":
            for base in (ROOT, self.root.parent if self.root.name == "demo" else self.root):
                found = read_json(base / ref)
                if found is not None:
                    return found
        if self.mode == "fixtures":
            return make_series(item)
        return None


class Store:
    def __init__(self, outputs: Path = OUTPUTS, demo: Path = DEMO, reports: Path = REPORTS) -> None:
        self.outputs = outputs
        self.demo = demo
        self.reports = reports

    def view(self, scenario: str) -> ScenarioView:
        if (self.outputs / "plans" / scenario / "plan.json").exists():
            return ScenarioView(scenario, "live", self.outputs)
        if (self.demo / "plans" / scenario / "plan.json").exists():
            return ScenarioView(scenario, "demo", self.demo)
        return ScenarioView(scenario, "fixtures", self.outputs)

    def metrics(self) -> dict[str, Any]:
        """Rapoartele modelelor: întâi reports/<X>/metrics.json, apoi copia din outputs/demo/reports/."""
        out: dict[str, Any] = {}
        for src in "ABC":
            out[src] = read_json(self.reports / src / "metrics.json") or read_json(self.demo / "reports" / src / "metrics.json")
        out["planner"] = read_json(self.reports / "planner" / "agent_eval.json") or read_json(
            self.demo / "reports" / "planner" / "agent_eval.json"
        )
        return out
