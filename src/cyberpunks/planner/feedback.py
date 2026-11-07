"""Omul în buclă, după plan: aprobarea listei unei echipe și verdictul de după vizită (eticheta pentru reantrenare).

- Aprobarea: un dispecer aprobă traseul unei echipe; fiecare oprire primește în jurnal un AuditRecord cu `actor: human`,
  `action: route_approve`. Aprobările stau în outputs/plans/<s>/approvals.json, legate de plan_id (după o replanificare
  care schimbă traseul, aprobarea veche apare ca "stale").
- Verdictul: echipa spune ce a găsit (confirmed, not_found, other_problem, no_access). Intră în jurnal (`field_verdict`)
  și în outputs/plans/<s>/labels.jsonl, câte o linie pe verdict, cu predicția și versiunea modelului: firele A și bilanț
  le pot folosi ca etichete noi la reantrenare (confirmed = 1, not_found = 0, restul fără etichetă).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from cyberpunks.common.contracts import AuditRecord
from cyberpunks.common.paths import OUTPUTS
from cyberpunks.planner.actions import write_json, write_jsonl
from cyberpunks.planner.settings import TZ

Outcome = Literal["confirmed", "not_found", "other_problem", "no_access"]
LABEL_OF = {"confirmed": 1, "not_found": 0, "other_problem": None, "no_access": None}
OUTCOME_RO = {
    "confirmed": "problema confirmată pe teren",
    "not_found": "nicio problemă găsită",
    "other_problem": "altă problemă decât cea estimată",
    "no_access": "fără acces la contor sau la post",
}


def _plan_dir(scenario: str, out_root: Path) -> Path:
    return out_root / "plans" / scenario


def _load_plan(plan_dir: Path) -> dict[str, Any]:
    path = plan_dir / "plan.json"
    if not path.exists():
        raise KeyError("nu există un plan pentru acest scenariu; rulează întâi agentul")
    return json.loads(path.read_text(encoding="utf-8"))


def _items(plan_dir: Path) -> dict[str, dict[str, Any]]:
    path = plan_dir / "work_items.jsonl"
    if not path.exists():
        return {}
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    return {r["work_item_id"]: r for r in rows}


def approve_route(scenario: str, crew_id: str, reviewer: str, note: str | None = None, *, out_root: Path = OUTPUTS) -> dict[str, Any]:
    plan_dir = _plan_dir(scenario, out_root)
    plan = _load_plan(plan_dir)
    route = next((r for r in plan.get("routes", []) if r["crew_id"] == crew_id), None)
    if route is None:
        raise KeyError(f"echipa {crew_id} nu are traseu în planul curent")
    decisions = {d["work_item_id"]: d for d in plan.get("decisions", [])}
    items = _items(plan_dir)
    now = datetime.now(TZ).replace(microsecond=0)
    records = []
    for stop in route["stops"]:
        wid = stop["work_item_id"]
        pred = (items.get(wid) or {}).get("prediction") or {}
        records.append(
            AuditRecord(
                audit_id=str(uuid.uuid4()), ts=now, actor="human", action="route_approve", work_item_id=wid,
                prediction_id=pred.get("prediction_id"), model_version=pred.get("model_version"),
                rule_id=(decisions.get(wid) or {}).get("rule_id"), threshold=(decisions.get(wid) or {}).get("threshold") or {},
                note=f"{reviewer}: aprob traseul {crew_id}, oprirea {stop['seq']}" + (f" ({note})" if note else ""),
            )
        )
    write_jsonl(plan_dir / "audit.jsonl", [r.model_dump(mode="json") for r in records], append=True)
    path = plan_dir / "approvals.json"
    approvals = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    approvals[crew_id] = {
        "crew_id": crew_id, "reviewer": reviewer, "note": note, "ts": now.isoformat(), "plan_id": plan["plan_id"],
        "work_item_ids": [s["work_item_id"] for s in route["stops"]], "audit_ids": [r.audit_id for r in records],
    }
    write_json(path, approvals)
    return approvals[crew_id]


def approvals(scenario: str, *, out_root: Path = OUTPUTS) -> list[dict[str, Any]]:
    plan_dir = _plan_dir(scenario, out_root)
    path = plan_dir / "approvals.json"
    if not path.exists():
        return []
    current = (json.loads((plan_dir / "plan.json").read_text(encoding="utf-8")) if (plan_dir / "plan.json").exists() else {})
    routes = {r["crew_id"]: [s["work_item_id"] for s in r["stops"]] for r in current.get("routes", [])}
    out = []
    for a in json.loads(path.read_text(encoding="utf-8")).values():
        stale = a.get("plan_id") != current.get("plan_id") and routes.get(a["crew_id"]) != a.get("work_item_ids")
        out.append({**a, "stale": bool(stale)})
    return out


def record_verdict(
    scenario: str, work_item_id: str, outcome: Outcome, reviewer: str, note: str | None = None, *, out_root: Path = OUTPUTS
) -> tuple[AuditRecord, dict[str, Any]]:
    if outcome not in LABEL_OF:
        raise ValueError(f"verdict necunoscut: {outcome!r} ({', '.join(LABEL_OF)})")
    plan_dir = _plan_dir(scenario, out_root)
    plan = _load_plan(plan_dir)
    decision = next((d for d in plan.get("decisions", []) if d["work_item_id"] == work_item_id), None)
    wi = _items(plan_dir).get(work_item_id)
    if decision is None or wi is None:
        raise KeyError(f"lucrarea {work_item_id} nu e în planul curent")
    now = datetime.now(TZ).replace(microsecond=0)
    pred = wi["prediction"]
    record = AuditRecord(
        audit_id=str(uuid.uuid4()), ts=now, actor="human", action="field_verdict", work_item_id=work_item_id,
        prediction_id=pred.get("prediction_id"), model_version=pred.get("model_version"), rule_id=decision.get("rule_id"),
        threshold={"score": float(pred.get("score", 0.0))},
        note=f"{reviewer}: {OUTCOME_RO[outcome]}" + (f" ({note})" if note else ""),
    )
    label = {
        "ts": now.isoformat(), "plan_id": plan["plan_id"], "work_item_id": work_item_id, "source": wi["source"], "asset_id": wi["asset_id"],
        "asset_type": wi["asset_type"], "prediction_id": pred.get("prediction_id"), "model_id": pred.get("model_id"),
        "model_version": pred.get("model_version"), "predicted_label": pred.get("label"), "score": pred.get("score"),
        "outcome": outcome, "label": LABEL_OF[outcome], "reviewer": reviewer, "note": note, "audit_id": record.audit_id,
        "synthetic": bool((wi.get("data_quality") or {}).get("synthetic", True)),
    }
    write_jsonl(plan_dir / "audit.jsonl", [record.model_dump(mode="json")], append=True)
    write_jsonl(plan_dir / "labels.jsonl", [label], append=True)
    return record, label


def labels(scenario: str, *, out_root: Path = OUTPUTS) -> list[dict[str, Any]]:
    path = _plan_dir(scenario, out_root) / "labels.jsonl"
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
