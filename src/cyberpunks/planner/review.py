"""Omul în buclă: aprobă, respinge sau amână o lucrare; decizia intră în jurnal (actor: human), apoi planul se recalculează.

Deciziile omului stau în outputs/plans/<scenariu>/overrides.json și se reaplică la fiecare replanificare,
până la o rulare nouă a agentului (care pornește de la zero, cu planul vechi arhivat în history/).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

from cyberpunks.common.contracts import AuditRecord
from cyberpunks.common.paths import OUTPUTS
from cyberpunks.planner.actions import write_json, write_jsonl
from cyberpunks.planner.agent import replan
from cyberpunks.planner.settings import TZ

ACTIONS = {"approve": "review_approve", "reject": "review_reject", "defer": "review_defer"}


def apply_review(
    scenario: str, work_item_id: str, decision: str, note: str | None, reviewer: str, *, out_root: Path = OUTPUTS
) -> AuditRecord:
    """Scrie decizia omului în jurnal și replanifică. KeyError dacă lucrarea nu există în planul curent."""
    if decision not in ACTIONS:
        raise ValueError(f"decizie necunoscută: {decision!r} (approve, reject, defer)")
    plan_dir = out_root / "plans" / scenario
    plan_path = plan_dir / "plan.json"
    if not plan_path.exists():
        raise KeyError(f"nu există un plan pentru scenariul {scenario!r}; rulează întâi agentul")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    current = next((d for d in plan["decisions"] if d["work_item_id"] == work_item_id), None)
    if current is None:
        raise KeyError(f"lucrarea {work_item_id} nu e în planul curent")
    if current["decision"] == "rejected_invalid":
        raise ValueError("lucrarea e în carantină (intrare greșită); nu se poate aproba până nu e corectată la sursă")
    items = [json.loads(line) for line in (plan_dir / "work_items.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    wi = next((w for w in items if w["work_item_id"] == work_item_id), {})
    now = datetime.now(TZ).replace(microsecond=0)
    record = AuditRecord(
        audit_id=str(uuid.uuid4()),
        ts=now,
        actor="human",
        action=ACTIONS[decision],
        work_item_id=work_item_id,
        prediction_id=(wi.get("prediction") or {}).get("prediction_id"),
        model_version=(wi.get("prediction") or {}).get("model_version"),
        rule_id=current.get("rule_id"),
        threshold=current.get("threshold") or {},
        note=f"{reviewer}: {note}" if note else reviewer,
    )
    write_jsonl(plan_dir / "audit.jsonl", [record.model_dump(mode="json")], append=True)
    ov_path = plan_dir / "overrides.json"
    overrides = json.loads(ov_path.read_text(encoding="utf-8")) if ov_path.exists() else {}
    overrides[work_item_id] = {"decision": decision, "reviewer": reviewer, "note": note, "ts": now.isoformat(), "audit_id": record.audit_id}
    write_json(ov_path, overrides)
    replan(scenario, out_root=out_root)
    return record

