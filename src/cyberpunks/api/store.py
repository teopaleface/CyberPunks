"""De unde citește API-ul datele unui scenariu.

Ordinea, pentru fiecare scenariu:
1. "live":     outputs/plans/<scenariu>/plan.json (ultima rulare a agentului pe mașina asta);
2. "demo":     outputs/demo/plans/<scenariu>/plan.json (instantaneul din git, aceeași structură ca outputs/);
3. "none":     niciun plan încă: un plan gol, cu o alertă care cere „Rulează agentul” (nu exemplele de test).
"fixtures" (contracts/fixtures/, exemple ilustrative) doar la cerere explicită: CYBERPUNKS_API_SOURCE=fixtures.

outputs/ și outputs/demo/ au aceeași structură:
    plans/<s>/{plan.json, audit.jsonl, work_items.jsonl, quarantine.jsonl, alerts.json, notifications.json, report.md}
    plans/<s>/work_orders/<crew_id>.pdf
    work_items/<s>/{A,B,C}.jsonl
    series/<s>/<work_item_id>.json
    reports/{A,B,C}/metrics.json, reports/planner/agent_eval.json   (doar în outputs/demo/)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from cyberpunks.api.fixture_series import make_series
from cyberpunks.common.paths import CONTRACTS, OUTPUTS, REPORTS, ROOT

Mode = Literal["live", "demo", "fixtures", "none"]
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
        if self.mode == "none":
            return empty_plan(self.scenario)
        return read_json(self.plan_dir / "plan.json")

    def work_items(self) -> list[dict[str, Any]]:
        if self.mode == "none":
            return []
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
        if isinstance(ref, str) and ref and self.mode != "fixtures":
            ref_path = Path(ref)
            if ref_path.is_absolute() or ".." in ref_path.parts:
                return None  # o cale venită din date nu iese din outputs/
            allowed = OUTPUTS.resolve()
            for base in (ROOT, self.root.parent if self.root.name == "demo" else self.root):
                candidate = (base / ref_path).resolve()
                if not candidate.is_relative_to(allowed) and not candidate.is_relative_to(self.root.resolve()):
                    continue
                found = read_json(candidate)
                if found is not None:
                    return found
        if self.mode == "fixtures":
            return make_series(item)
        return None


def empty_plan(scenario: str) -> dict[str, Any]:
    """Scenariul n-a rulat încă pe mașina asta și nu e în instantaneu: un plan gol, valid după contract, care spune asta.
    Nu se arată niciodată exemplele de test în locul unui plan real."""
    from datetime import datetime

    from cyberpunks.common.contracts import CONTRACT_VERSION
    from cyberpunks.planner import planner_version
    from cyberpunks.planner.settings import TZ, Settings

    now = datetime.now(TZ).replace(microsecond=0)
    try:
        sc = Settings.load().scenarios.get(scenario)
        day = (sc.resolve_date() if sc else None) or now.date()
    except Exception:  # noqa: BLE001 - un config stricat nu are voie să oprească răspunsul gol
        day = now.date()
    zeros = {"items_in": 0, "items_valid": 0, "items_invalid": 0, "assigned": 0, "deferred": 0, "human_review": 0,
             "remote_actions": 0, "notifications": 0, "crews_used": 0, "expected_value_lei": 0.0, "total_km": 0.0}
    return {
        "contract_version": CONTRACT_VERSION,
        "plan_id": f"FARA-PLAN-{scenario}",
        "plan_date": day.isoformat(),
        "generated_at": now.isoformat(),
        "planner_version": planner_version(),
        "scenario": scenario,
        "summary": zeros,
        "routes": [],
        "decisions": [],
        "alerts": [{
            "alert_id": f"fara-plan-{scenario}",
            "severity": "info",
            "title_ro": f"Încă nu există un plan pentru „{scenario}” ({day.strftime('%d.%m.%Y')})",
            "body_ro": "Apasă „Rulează agentul”: modelele A, B și C rulează pe datele zilei (prognoza reală pentru mâine), "
                       "iar o sursă care nu poate da rezultate apare ca lipsă, cu motivul. Nu se folosesc exemplele de test.",
            "work_item_ids": [],
            "channel": "dispecerat",
            "created_at": now.isoformat(),
        }],
        "notifications": [],
        "sources_status": {"A": "missing", "B": "missing", "C": "missing"},
    }


class Store:
    def __init__(self, outputs: Path = OUTPUTS, demo: Path = DEMO, reports: Path = REPORTS) -> None:
        self.outputs = outputs
        self.demo = demo
        self.reports = reports

    def view(self, scenario: str) -> ScenarioView:
        """CYBERPUNKS_API_SOURCE alege sursa: auto (rulare locală, apoi instantaneu, apoi plan gol), demo, live sau fixtures.
        Exemplele de test (fixtures) apar doar la cerere explicită, niciodată în locul unui plan real."""
        source = os.environ.get("CYBERPUNKS_API_SOURCE", "auto").strip().lower()
        if source == "demo" and (self.demo / "plans" / scenario / "plan.json").exists():
            return ScenarioView(scenario, "demo", self.demo)
        if source == "fixtures":
            return ScenarioView(scenario, "fixtures", self.outputs)
        if (self.outputs / "plans" / scenario / "plan.json").exists():
            return ScenarioView(scenario, "live", self.outputs)
        if (self.demo / "plans" / scenario / "plan.json").exists():
            return ScenarioView(scenario, "demo", self.demo)
        return ScenarioView(scenario, "none", self.outputs)

    def metrics(self) -> dict[str, Any]:
        """Rapoartele modelelor: întâi reports/<X>/metrics.json, apoi copia din outputs/demo/reports/."""
        out: dict[str, Any] = {}
        for src in "ABC":
            out[src] = read_json(self.reports / src / "metrics.json") or read_json(self.demo / "reports" / src / "metrics.json")
        out["planner"] = read_json(self.reports / "planner" / "agent_eval.json") or read_json(
            self.demo / "reports" / "planner" / "agent_eval.json"
        )
        return out
