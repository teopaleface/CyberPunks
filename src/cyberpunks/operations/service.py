"""Cazuri comune și propuneri confirmate, cu domeniu verificat pe fiecare obiect."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

from pydantic import ValidationError

from cyberpunks.api.store import read_json
from cyberpunks.common.paths import OUTPUTS
from cyberpunks.operations import photos
from cyberpunks.operations.bindings import DEMO_ORGANIZATION, demo_binding
from cyberpunks.operations.database import Database
from cyberpunks.operations.models import DATA_MODELS, Actor, OperationError
from cyberpunks.operations.planner import Planner

PLANNER_ACTIONS = {"approve_plan", "review_work_item", "record_verdict"}
PERMISSIONS = {"approve_plan": "approve_plan", "review_work_item": "review_work_item", "create_case": "create_case"}


def now() -> datetime:
    return datetime.now(UTC)


def encode(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def signature(actor: Actor) -> str:
    obj = actor.model_dump()
    obj["permissions"] = sorted(obj["permissions"])
    obj["connection_ids"] = sorted(obj["connection_ids"])
    return hashlib.sha256(encode(obj).encode()).hexdigest()


def fail(status: int, code: str, message: str):
    raise OperationError(status, code, message)


class OperationsService:
    def __init__(self, outputs: Path | None = None, db_path: Path | None = None, *, demo: Path | None = None):
        self.outputs = Path(
            outputs or os.environ.get("DAYBREAK_OPERATIONS_OUTPUTS", OUTPUTS / "operations-runtime/data")
        ).resolve()
        self.db_path = Path(
            db_path or os.environ.get("DAYBREAK_OPERATIONS_DB", OUTPUTS / "operations/operations.sqlite3")
        ).resolve()
        self.db = Database(self.db_path)
        self.planner = Planner(
            self.outputs, self.db_path.parent / (self.db_path.stem + "-state"), **({"demo": demo} if demo else {})
        )

    @contextmanager
    def _lock(self):
        # All workers using this database serialize complete planner effects and SQLite commits.
        with self.db_path.with_suffix(".lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def _scope(self, actor: Actor, scenario: str):
        if actor.organization_id != DEMO_ORGANIZATION or scenario != "demo-vara":
            fail(404, "not_found", "Scenario not found in your organization.")
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", scenario):
            fail(422, "invalid_scenario", "Invalid scenario.")

    def _provision(self, scenario: str):
        with self.db.connect() as db:
            found = db.execute(
                "SELECT 1 FROM connections WHERE organization_id=? AND scenario=?", (DEMO_ORGANIZATION, scenario)
            ).fetchone()
        if found:
            return
        view = self.planner.view(scenario)
        binding = demo_binding(view.plan() or {}, view.work_items(), scenario)
        if binding:
            with self.db.transaction() as db:
                db.execute(
                    "INSERT OR IGNORE INTO connections VALUES (?,?,?,?)",
                    (binding["connection_id"], DEMO_ORGANIZATION, scenario, encode(binding)),
                )

    def demo_bindings(self, scenario: str = "demo-vara") -> dict:
        """Administrative local provisioning. Never accepts browser-selected memberships."""
        if scenario != "demo-vara":
            fail(404, "not_found", "Synthetic memberships exist only for demo-vara.")
        with self._lock():
            self._provision(scenario)
            with self.db.connect() as db:
                rows = db.execute(
                    "SELECT body FROM connections WHERE organization_id=? AND scenario=?", (DEMO_ORGANIZATION, scenario)
                ).fetchall()
            connections = [json.loads(r["body"]) for r in rows]
            return {
                "synthetic": True,
                "organization_id": DEMO_ORGANIZATION,
                "scenario": scenario,
                "connection_ids": [c["connection_id"] for c in connections],
                "crew_id": connections[0]["crew_id"] if connections else None,
                "connections": connections,
                "permissions": ["approve_plan", "review_work_item", "create_case", "recover_commands"],
            }

    def _connections(self, actor: Actor, scenario: str) -> list[dict]:
        with self.db.connect() as db:
            rows = db.execute(
                "SELECT body FROM connections WHERE organization_id=? AND scenario=?", (actor.organization_id, scenario)
            ).fetchall()
        cs = [json.loads(r["body"]) for r in rows]
        if actor.role == "customer":
            return [c for c in cs if c["connection_id"] in actor.connection_ids]
        if actor.role == "technician":
            # Current route, never the old provisioning crew, determines technical access.
            ids = {w["work_item_id"] for w in self._work_items(actor, scenario)}
            return [c for c in cs if c["work_item_id"] in ids]
        return cs

    def _connection(self, actor: Actor, scenario: str, connection_id: str) -> dict:
        found = next((c for c in self._connections(actor, scenario) if c["connection_id"] == connection_id), None)
        if found is None:
            fail(404, "not_found", "Connection not found in your scope.")
        return found

    def _work_items(self, actor: Actor, scenario: str) -> list[dict]:
        if actor.role == "customer":
            return []
        view = self.planner.view(scenario)
        plan, items = view.plan() or {}, view.work_items()
        decisions = {d["work_item_id"]: d for d in plan.get("decisions", [])}
        allowed = None
        if actor.role == "technician":
            allowed = (
                {
                    s["work_item_id"]
                    for r in plan.get("routes", [])
                    if r["crew_id"] == actor.crew_id
                    for s in r.get("stops", [])
                }
                if actor.crew_id
                else set()
            )
        return [
            {
                **w,
                "decision": decisions.get(w["work_item_id"]),
                "assessment": self._assessment(w, plan, scenario, view.mode),
            }
            for w in items
            if allowed is None or w["work_item_id"] in allowed
        ]

    def _work_item(self, actor: Actor, scenario: str, wid: str) -> dict:
        item = next((w for w in self._work_items(actor, scenario) if w["work_item_id"] == wid), None)
        if item is None:
            fail(404, "not_found", "Work item not found in your scope.")
        return item

    def authorize_photo_upload(self, actor: Actor, work_item_id: str, scenario: str = "demo-vara"):
        self._scope(actor, scenario)
        self._authorize_action(actor, "record_verdict")
        with self._lock():
            self._work_item(actor, scenario, work_item_id)
            self.planner.writable(scenario)

    def upload_photo(
        self, actor: Actor, work_item_id: str, content: bytes, mime_type: str, scenario: str = "demo-vara"
    ) -> dict:
        self.authorize_photo_upload(actor, work_item_id, scenario)
        content, width, height = photos.sanitize(content, mime_type)
        with self._lock(), self.db.transaction() as db:
            self._work_item(actor, scenario, work_item_id)
            current_time = now()
            photos.collect_expired(db, actor.organization_id, scenario, current_time)
            count = photos.pending_count(
                db,
                actor.organization_id,
                scenario,
                actor.user_id,
                signature(actor),
                [w["work_item_id"] for w in self._work_items(actor, scenario)],
                current_time,
            )
            if count >= photos.PENDING_QUOTA:
                fail(409, "photo_quota", "Remove unused draft photos before uploading more. The limit is 20.")
            pid = str(uuid.uuid4())
            metadata = {
                "photo_id": pid,
                "work_item_id": work_item_id,
                "mime_type": mime_type,
                "width": width,
                "height": height,
                "size_bytes": len(content),
                "created_at": now().isoformat(),
                "status": "draft",
                "url": f"/api/operations/photos/{pid}?scenario={quote(scenario, safe='')}",
            }
            db.execute(
                "INSERT INTO photos VALUES (?,?,?,?,?,?,?,?,?,NULL)",
                (
                    pid,
                    actor.organization_id,
                    scenario,
                    work_item_id,
                    actor.user_id,
                    signature(actor),
                    "draft",
                    encode(metadata),
                    content,
                ),
            )
            return metadata

    def _photo_row(self, db, actor: Actor, pid: str, scenario: str):
        self._scope(actor, scenario)
        row = db.execute(
            "SELECT * FROM photos WHERE photo_id=? AND organization_id=? AND scenario=?",
            (photos.photo_id(pid), actor.organization_id, scenario),
        ).fetchone()
        if not row or actor.role == "customer" or photos.is_expired(db, row["photo_id"], now()):
            fail(404, "not_found", "Photo not found in your scope.")
        self._work_item(actor, scenario, row["work_item_id"])
        if row["status"] == "draft" and (
            actor.role != "technician"
            or row["uploader_id"] != actor.user_id
            or row["actor_signature"] != signature(actor)
        ):
            fail(404, "not_found", "Photo not found in your scope.")
        return row

    def photo(self, actor: Actor, pid: str, scenario: str = "demo-vara") -> tuple[dict, bytes]:
        with self._lock(), self.db.connect() as db:
            row = self._photo_row(db, actor, pid, scenario)
            return json.loads(row["body"]), row["content"]

    def delete_photo(self, actor: Actor, pid: str, scenario: str = "demo-vara") -> dict:
        self._scope(actor, scenario)
        self._authorize_action(actor, "record_verdict")
        with self._lock(), self.db.transaction() as db:
            row = self._photo_row(db, actor, pid, scenario)
            if row["status"] != "draft" or row["uploader_id"] != actor.user_id:
                photos.error()
            refs = db.execute(
                "SELECT p.body,c.status FROM proposal_photos pp JOIN proposals p ON p.proposal_id=pp.proposal_id "
                "LEFT JOIN commands c ON c.command_id=p.command_id WHERE pp.photo_id=?",
                (row["photo_id"],),
            ).fetchall()
            if any(
                r["status"] == "reconciling"
                or (r["status"] is None and datetime.fromisoformat(json.loads(r["body"])["expires_at"]) > now())
                for r in refs
            ):
                fail(409, "photo_in_use", "This photo is bound to a prepared finding. Wait for expiry or confirm it.")
            db.execute("DELETE FROM proposal_photos WHERE photo_id=?", (row["photo_id"],))
            db.execute("DELETE FROM photos WHERE photo_id=?", (row["photo_id"],))
            return {"photo_id": row["photo_id"], "deleted": True}

    def _enrich_work_items(self, actor: Actor, scenario: str, items: list[dict]):
        by_id = {w["work_item_id"]: w for w in items}
        for item in items:
            item.update(findings=[], photos=[], manual_corrections=[], latest_manual_correction=None)
        with self.db.connect() as db:
            for table, field in (("findings", "findings"), ("manual_corrections", "manual_corrections")):
                for row in db.execute(
                    f"SELECT work_item_id,body FROM {table} WHERE organization_id=? AND scenario=? ORDER BY rowid",
                    (actor.organization_id, scenario),
                ):
                    if row["work_item_id"] in by_id:
                        by_id[row["work_item_id"]][field].append(json.loads(row["body"]))
        for item in items:
            item["photos"] = [p for f in item["findings"] for p in f["photos"]]
            if item["manual_corrections"]:
                item["latest_manual_correction"] = item["manual_corrections"][-1]

    def _review_snapshot(self, actor: Actor, scenario: str, item: dict) -> dict:
        with self.db.connect() as db:
            first = db.execute(
                "SELECT body FROM manual_corrections WHERE organization_id=? AND scenario=? AND work_item_id=? "
                "ORDER BY rowid LIMIT 1",
                (actor.organization_id, scenario, item["work_item_id"]),
            ).fetchone()
        before = item.get("decision")
        original, status = None, "unknown"
        if first:
            first = json.loads(first["body"])
            original, status = first["original_ai_decision"], first["original_ai_decision_status"]
        else:
            view = self.planner.view(scenario)
            overrides = read_json(view.plan_dir / "overrides.json") or {}
            audit_path = view.plan_dir / "audit.jsonl"
            try:
                records = [json.loads(line) for line in audit_path.read_text().splitlines() if line.strip()]
                previous_human = any(
                    r.get("work_item_id") == item["work_item_id"] and r.get("action", "").startswith("review_")
                    for r in records
                )
                proof = next((r for r in records if before and r.get("audit_id") == before.get("audit_id")), {})
                prediction = item.get("prediction") or {}
                if (
                    before
                    and item["work_item_id"] not in overrides
                    and not previous_human
                    and proof.get("actor") == "agent"
                    and proof.get("work_item_id") == item["work_item_id"]
                    and proof.get("action") == before.get("decision")
                    and proof.get("prediction_id") == prediction.get("prediction_id")
                    and proof.get("model_version") == prediction.get("model_version")
                ):
                    original, status = before, "verified"
            except (OSError, ValueError, TypeError):
                pass  # Missing historical evidence must never be labelled as an original AI decision.
        return {"decision_before": before, "original_ai_decision": original, "original_ai_decision_status": status}

    def _cases(self, actor: Actor, scenario: str) -> list[dict]:
        with self.db.connect() as db:
            rows = db.execute(
                "SELECT body FROM cases WHERE organization_id=? AND scenario=? ORDER BY case_id",
                (actor.organization_id, scenario),
            ).fetchall()
        cases = [json.loads(r["body"]) for r in rows]
        if actor.role == "dispatcher":
            return cases
        cs = {c["connection_id"] for c in self._connections(actor, scenario)}
        if actor.role == "customer":
            return [c for c in cases if c["connection_id"] in cs and c["requester_id"] == actor.user_id]
        ids = {w["work_item_id"] for w in self._work_items(actor, scenario)}
        return [c for c in cases if c["work_item_id"] in ids]

    def _case(self, actor: Actor, scenario: str, case_id: str) -> dict:
        case = next((c for c in self._cases(actor, scenario) if c["case_id"] == case_id), None)
        if case is None:
            fail(404, "not_found", "Case not found in your scope.")
        return case

    @staticmethod
    def _assessment(item: dict, plan: dict, scenario: str, mode: str) -> dict:
        pred, quality = item.get("prediction") or {}, item.get("data_quality") or {}
        reason = None
        if item.get("target_date") != plan.get("plan_date") or plan.get("scenario") != scenario:
            reason = "Prediction does not match the current scenario and plan date."
        elif not pred.get("prediction_id") or not pred.get("model_version") or not pred.get("model_id"):
            reason = "Prediction provenance is incomplete."
        elif pred.get("abstain"):
            reason = pred.get("abstain_reason") or "The model abstained."
        elif quality.get("missing_ratio", 1) > 0.3:
            reason = "Insufficient input data for a supported assessment."
        elif plan.get("sources_status", {}).get(item.get("source")) == "missing":
            reason = "The model source is unavailable."
        return {
            "status": "needs_data" if reason else "available",
            "reason": reason,
            "work_item_id": item.get("work_item_id"),
            "prediction_id": pred.get("prediction_id"),
            "model_id": pred.get("model_id"),
            "model_version": pred.get("model_version"),
            "asset_id": item.get("asset_id"),
            "target_date": item.get("target_date"),
            "scenario": scenario,
            "created_at": item.get("created_at"),
            "score": pred.get("score") if not reason else None,
            "confidence": pred.get("confidence") if not reason else None,
            "point_estimate": pred.get("point_estimate") if not reason else None,
            "point_interval": pred.get("point_interval") if not reason else None,
            "point_unit": pred.get("point_unit"),
            "synthetic": bool(quality.get("synthetic", True)),
            "source": "local_run" if mode == "live" else "demo_snapshot",
            "limitations": ["Historical scenario; not a current outage or confirmed repair."],
        }

    def _case_assessment(self, connection: dict, symptom_type: str, scenario: str) -> dict:
        view = self.planner.view(scenario)
        plan, items = view.plan() or {}, view.work_items()
        # A voltage symptom requires C at the exact provisioned post, never a neighbor or arbitrary meter.
        if symptom_type == "voltage":
            compatible = [
                w
                for w in items
                if w["source"] == "C"
                and w["asset_type"] == "transformer_post"
                and w["asset_id"] == connection["post_id"]
            ]
        elif symptom_type == "meter" and connection.get("meter_id"):
            compatible = [w for w in items if w["source"] == "A" and w["asset_id"] == connection["meter_id"]]
        else:
            compatible = []
        if not compatible:
            return {
                "status": "needs_data",
                "reason": "No compatible assessment for this symptom and authorized connection.",
                "score": None,
                "synthetic": True,
                "source": view.mode,
            }
        return self._assessment(compatible[0], plan, scenario, view.mode)

    def _public_case(self, actor: Actor, case: dict) -> dict:
        case = dict(case)
        original = case.get("assessment", {})
        with self.db.connect() as db:
            connection = db.execute(
                "SELECT body FROM connections WHERE connection_id=? AND organization_id=? AND scenario=?",
                (case["connection_id"], actor.organization_id, case["scenario"]),
            ).fetchone()
        if connection and original.get("prediction_id") and original.get("status") == "available":
            current = self._case_assessment(json.loads(connection["body"]), case["symptom_type"], case["scenario"])
            if (
                current.get("prediction_id") != original.get("prediction_id")
                or current.get("model_version") != original.get("model_version")
                or current.get("status") != "available"
            ):
                case["assessment"] = {
                    **original,
                    "status": "stale",
                    "score": None,
                    "point_estimate": None,
                    "point_interval": None,
                    "confidence": None,
                    "reason": "The saved assessment is no longer current. Human reassessment is required.",
                }
        if actor.role != "customer":
            return case
        allowed = (
            "case_id",
            "connection_id",
            "symptom",
            "symptom_type",
            "status",
            "version",
            "synthetic",
            "created_at",
            "updated_at",
            "next_step",
            "availability",
            "assessment",
            "human_requested",
        )
        public = {k: v for k, v in case.items() if k in allowed}
        outcome = case.get("verdict", {}).get("outcome")
        if outcome in {"confirmed", "not_found", "other_problem", "no_access"}:
            # Customers need the finding, without internal command/prediction identifiers.
            public["verdict"] = {"outcome": outcome, "repair_confirmed": False}
        return public

    def context(self, actor: Actor, scenario: str = "demo-vara") -> dict:
        self._scope(actor, scenario)
        with self._lock():
            self._provision(scenario)
            view = self.planner.view(scenario)
            plan, version = view.plan() or {}, self.planner.version(scenario)
            meta = read_json(view.plan_dir / "run.json") or {}
            connections = self._connections(actor, scenario)
            items = self._work_items(actor, scenario)
            self._enrich_work_items(actor, scenario, items)
            cases = self._cases(actor, scenario)
            routes = plan.get("routes", [])
            if actor.role != "dispatcher":
                routes = [r for r in routes if actor.role == "technician" and r["crew_id"] == actor.crew_id]
            from cyberpunks.planner import feedback

            approvals = feedback.approvals(scenario, out_root=view.root)
            approval = feedback.plan_approval(scenario, out_root=view.root)
            plan_info = {k: plan.get(k) for k in ("plan_id", "plan_date", "generated_at", "planner_version")}
            plan_info.update(
                source="local_run" if view.mode == "live" else "demo_snapshot",
                version=version,
                plan_version=version,
                writable=view.mode == "live" and bool(meta.get("sources")),
                historical_scenario=True,
                approved=bool(approval and not approval["stale"]),
            )
            if actor.role != "customer":
                plan_info.update(
                    routes=routes,
                    sources_status=plan.get("sources_status"),
                    summary=plan.get("summary") if actor.role == "dispatcher" else None,
                    approvals=[a for a in approvals if actor.role == "dispatcher" or a["crew_id"] == actor.crew_id],
                    inference_sources={
                        k: {"origin": v.get("origin"), "status": v.get("status"), "valid": v.get("valid")}
                        for k, v in meta.get("sources", {}).items()
                    },
                )
            with self.db.connect() as db:
                events = [
                    json.loads(r["body"])
                    for r in db.execute(
                        "SELECT body FROM events WHERE organization_id=? AND scenario=? ORDER BY rowid",
                        (actor.organization_id, scenario),
                    )
                ]
                pending = db.execute(
                    "SELECT c.*, p.actor_signature, p.body AS proposal_body FROM commands c JOIN proposals p "
                    "ON p.proposal_id=c.proposal_id WHERE c.organization_id=? AND c.scenario=? AND c.status=?",
                    (actor.organization_id, scenario, "reconciling"),
                ).fetchall()
                proposal_rows = db.execute(
                    "SELECT body FROM proposals WHERE user_id=? AND organization_id=? AND scenario=? "
                    "AND actor_signature=? AND command_id IS NULL ORDER BY rowid DESC LIMIT 50",
                    (actor.user_id, actor.organization_id, scenario, signature(actor)),
                ).fetchall()
            pending_proposals = []
            for row in proposal_rows:
                p = json.loads(row["body"])
                if datetime.fromisoformat(p["expires_at"]) <= now() or p["plan_version"] != version:
                    continue
                try:
                    self._authorize_action(actor, p["action"])
                    self._check_versions(actor, p)
                except OperationError:
                    continue
                pending_proposals.append(
                    {
                        k: p[k]
                        for k in (
                            "proposal_id",
                            "action",
                            "summary",
                            "scenario",
                            "created_at",
                            "expires_at",
                            "requires_confirmation",
                        )
                    }
                )
                if len(pending_proposals) == 10:
                    break
            pending_commands = []
            for row in pending:
                if row["user_id"] != actor.user_id and not self._can_recover(actor):
                    continue
                p = json.loads(row["proposal_body"])
                cmd = json.loads(row["body"])
                unchanged_owner = row["user_id"] == actor.user_id and row["actor_signature"] == signature(actor)
                recovery = self._recovery_options(p, cmd) if self._can_recover(actor) else None
                pending_commands.append(
                    {
                        "command_id": cmd["command_id"],
                        "proposal_id": cmd["proposal_id"],
                        "action": cmd["action"],
                        "status": cmd["status"],
                        "created_at": cmd["created_at"],
                        "can_recover": unchanged_owner
                        or bool(recovery and recovery["action"] in ("retrieve", "cancel")),
                        "recovery_action": recovery["action"]
                        if recovery
                        else ("retrieve" if unchanged_owner else "requires_dispatcher"),
                    }
                )
            case_ids = {c["case_id"] for c in cases}
            if actor.role != "dispatcher":
                work_ids = {w["work_item_id"] for w in items}
                events = [
                    e
                    for e in events
                    if e.get("case_id") in case_ids
                    or (actor.role == "technician" and e.get("work_item_id") in work_ids)
                    or (e["actor_id"] == actor.user_id and e["action"] == "request_human")
                ]
            if actor.role == "customer":
                events = [
                    {k: e[k] for k in ("event_id", "case_id", "created_at", "action", "status") if k in e}
                    for e in events
                ]
                connections = [
                    {
                        k: c[k]
                        for k in (
                            "connection_id",
                            "label",
                            "post_id",
                            "meter_id",
                            "synthetic",
                            "supported_symptom_types",
                        )
                        if k in c
                    }
                    for c in connections
                ]
            route_approved = (
                any(not a["stale"] and a["crew_id"] == actor.crew_id for a in approvals) or plan_info["approved"]
            )
            stops = [s for r in routes for s in r.get("stops", [])]
            return {
                "actor": actor.model_dump(),
                "scenario": scenario,
                "plan": plan_info,
                "connections": connections,
                "work_items": items,
                "cases": [self._public_case(actor, c) for c in cases],
                "events": events,
                "next_stop": stops[0] if actor.role == "technician" and route_approved and stops else None,
                "next_stop_status": "approved_plan" if route_approved else "awaiting_approval",
                "human_requests": [e["human_request"] for e in events if "human_request" in e],
                "reconciliation_pending": bool(pending),
                "pending_commands": pending_commands,
                "pending_proposals": pending_proposals,
                "synthetic": True,
                "data_notice": "Synthetic operational associations. Historical model scenario, not a live grid feed.",
            }

    def _authorize_action(self, actor: Actor, action: str):
        roles = {
            "create_case": {"customer", "dispatcher"},
            "record_verdict": {"technician"},
            "review_work_item": {"dispatcher"},
            "approve_plan": {"dispatcher"},
            "set_availability": {"customer"},
            "request_human": {"customer", "technician", "dispatcher"},
        }
        if action not in roles:
            fail(422, "invalid_action", "Unknown operation.")
        if actor.role not in roles[action]:
            fail(403, "forbidden", "Your role cannot perform this operation.")
        if actor.role == "dispatcher" and action in PERMISSIONS and PERMISSIONS[action] not in actor.permissions:
            fail(403, "forbidden", "An explicit operation permission is required.")

    @staticmethod
    def _parse_data(action: str, data: dict) -> dict:
        try:
            return DATA_MODELS[action].model_validate(data).model_dump(exclude_none=True, mode="json")
        except ValidationError:
            fail(422, "invalid_data", "Invalid operation fields. Check the action schema.")

    def _validate(self, actor: Actor, action: str, data: dict, scenario: str) -> dict:
        self._authorize_action(actor, action)
        d = self._parse_data(action, data)
        plan = self.planner.view(scenario).plan() or {}
        if d.get("plan_version") and d["plan_version"] != self.planner.version(scenario):
            fail(409, "stale_plan", "The plan changed. Reload before preparing this operation.")
        if d.get("case_id"):
            c = self._case(actor, scenario, d["case_id"])
            if d.get("case_version") and d["case_version"] != c["version"]:
                fail(409, "stale_case", "The case changed. Reload before preparing this operation.")
            d["case_version"] = c["version"]
        if action == "create_case":
            self._connection(actor, scenario, d["connection_id"])
            if d.get("case_id"):
                fail(422, "invalid_data", "A new report cannot select an existing case.")
        if action in {"review_work_item", "record_verdict"}:
            w = self._work_item(actor, scenario, d["work_item_id"])
            if d.get("case_id") and c["work_item_id"] != w["work_item_id"]:
                fail(422, "case_work_mismatch", "The work item does not belong to this case.")
            # Bind all affected shared cases, even when the caller selected only the work item.
            linked = [c for c in self._cases(actor, scenario) if c["work_item_id"] == w["work_item_id"]]
            if action == "record_verdict" and any(
                c.get("assessment", {}).get("prediction_id") != w.get("prediction", {}).get("prediction_id")
                for c in linked
            ):
                fail(
                    409, "stale_assessment", "The case refers to an older prediction. Request human reassessment first."
                )
            if action == "review_work_item" and (w.get("decision") or {}).get("decision") == "rejected_invalid":
                fail(409, "invalid_work_item", "Correct the quarantined work item at its source before review.")
            if action == "review_work_item":
                d.update(self._review_snapshot(actor, scenario, w))
            d["linked_case_versions"] = {c["case_id"]: c["version"] for c in linked}
        if action == "approve_plan":
            if d["plan_id"] != plan.get("plan_id"):
                fail(409, "stale_plan", "The selected plan is no longer current.")
            d["linked_case_versions"] = {c["case_id"]: c["version"] for c in self._cases(actor, scenario)}
            if d.get("crew_id") and not any(r["crew_id"] == d["crew_id"] for r in plan.get("routes", [])):
                fail(404, "not_found", "Crew route not found in the current plan.")
        if action == "set_availability":
            try:
                start, end = datetime.fromisoformat(d["start"]), datetime.fromisoformat(d["end"])
                if not start.tzinfo or not end.tzinfo or end <= start or end - start > timedelta(days=1):
                    raise ValueError
            except ValueError:
                fail(422, "invalid_window", "Provide a time zone and an increasing access window of at most 24 hours.")
        if action == "request_human":
            if d.get("connection_id"):
                self._connection(actor, scenario, d["connection_id"])
            if actor.role == "customer" and not d.get("case_id") and not d.get("connection_id"):
                fail(422, "connection_required", "Select your case or authorized connection.")
        if action in PLANNER_ACTIONS:
            self.planner.writable(scenario)
        return d

    def _prepare_retry(self, actor: Actor, action: str, request_data: dict, scenario: str) -> dict | None:
        idem = request_data.get("idempotency_key")
        if not idem:
            return None
        fingerprint = hashlib.sha256(encode({"key": idem}).encode()).hexdigest()
        with self.db.connect() as db:
            row = db.execute(
                "SELECT proposal_id FROM proposals WHERE user_id=? AND organization_id=? AND scenario=? AND fingerprint=?",
                (actor.user_id, actor.organization_id, scenario, fingerprint),
            ).fetchone()
        if not row:
            return None
        p, command_id = self._load_proposal(actor, row["proposal_id"])
        if p["action"] != action:
            fail(409, "idempotency_conflict", "This idempotency key already belongs to another proposal.")
        original = p.get("request_data")
        if original is None:
            # Older proposals have only the server-enriched payload. Never compare
            # generated provenance/photo metadata, or versions absent from the retry.
            original = {k: v for k, v in p["data"].items() if k in DATA_MODELS[action].model_fields}
            for field in ("plan_version", "case_version"):
                if field not in request_data:
                    original.pop(field, None)
            original = self._parse_data(action, original)
        if original != request_data:
            fail(409, "idempotency_conflict", "This idempotency key already belongs to another proposal.")
        # A key identifies a request, never a grant of the historical object's rights.
        for field, check in (
            ("work_item_id", self._work_item),
            ("case_id", self._case),
            ("connection_id", self._connection),
        ):
            if p["data"].get(field):
                check(actor, scenario, p["data"][field])
        if not command_id:
            if datetime.fromisoformat(p["expires_at"]) <= now():
                return None  # Preserve renewal of expired, unconfirmed requests only.
            self._check_versions(actor, p)
        return self._public_proposal(p)

    def prepare(self, actor: Actor, action: str, data: dict, scenario: str = "demo-vara") -> dict:
        self._scope(actor, scenario)
        self._authorize_action(actor, action)
        with self._lock():
            self._provision(scenario)
            request_data = self._parse_data(action, data)
            retry = self._prepare_retry(actor, action, request_data, scenario)
            if retry:
                return retry
            d = self._validate(actor, action, data, scenario)
            with self.db.transaction() as db:
                version = self.planner.version(scenario)
                if action == "record_verdict":
                    d["photos"] = photos.validate_refs(
                        db,
                        actor.organization_id,
                        actor.user_id,
                        scenario,
                        d["work_item_id"],
                        d["photo_ids"],
                        signature(actor),
                        at=now(),
                    )
                payload = {"action": action, "data": d, "plan_version": version}
                idem = d.get("idempotency_key")
                fingerprint = hashlib.sha256(encode({"key": idem} if idem else payload).encode()).hexdigest()
                prior = db.execute(
                    "SELECT body FROM proposals WHERE user_id=? AND organization_id=? AND scenario=? AND fingerprint=?",
                    (actor.user_id, actor.organization_id, scenario, fingerprint),
                ).fetchone()
                if prior:
                    p = json.loads(prior["body"])
                    if datetime.fromisoformat(p["expires_at"]) > now() and p["actor_signature"] == signature(actor):
                        return self._public_proposal(p)
                    db.execute("DELETE FROM proposals WHERE proposal_id=? AND command_id IS NULL", (p["proposal_id"],))
                    # Keep consumed keys immutable, even after expiry.
                    if db.execute("SELECT 1 FROM proposals WHERE proposal_id=?", (p["proposal_id"],)).fetchone():
                        fail(409, "proposal_consumed", "This proposal was already confirmed. Retrieve its command.")
                p = {
                    "proposal_id": str(uuid.uuid4()),
                    "action": action,
                    "data": d,
                    "request_data": request_data,
                    "scenario": scenario,
                    "plan_version": version,
                    "actor_signature": signature(actor),
                    "created_at": now().isoformat(),
                    "expires_at": (now() + timedelta(minutes=10)).isoformat(),
                    "requires_confirmation": True,
                    "summary": self._summary(action, d),
                }
                db.execute(
                    "INSERT INTO proposals VALUES (?,?,?,?,?,?,?,NULL)",
                    (
                        p["proposal_id"],
                        actor.user_id,
                        actor.organization_id,
                        scenario,
                        signature(actor),
                        fingerprint,
                        encode(p),
                    ),
                )
                if action == "record_verdict":
                    db.executemany(
                        "INSERT INTO proposal_photos VALUES (?,?)", [(p["proposal_id"], pid) for pid in d["photo_ids"]]
                    )
            return self._public_proposal(p)

    @staticmethod
    def _summary(action: str, d: dict) -> str:
        if action == "create_case":
            return f"Create a case for {d['connection_id']}: {d['symptom']}"
        if action == "record_verdict":
            return f"Record {d['outcome']} for {d['work_item_id']}. This does not confirm a repair."
        if action == "review_work_item":
            return f"{d['decision'].capitalize()} {d['work_item_id']} and recalculate the plan."
        if action == "approve_plan":
            return f"Approve plan {d['plan_id']}" + (f" for crew {d['crew_id']}." if d.get("crew_id") else ".")
        if action == "set_availability":
            return f"Request access from {d['start']} to {d['end']}. Scheduling remains unconfirmed."
        return "Add a human review request to the shared queue. No external message or call will be sent."

    @staticmethod
    def _public_proposal(p: dict) -> dict:
        return {k: v for k, v in p.items() if k not in {"actor_signature", "request_data"}}

    def _load_proposal(self, actor: Actor, pid: str) -> tuple[dict, str | None]:
        with self.db.connect() as db:
            row = db.execute(
                "SELECT * FROM proposals WHERE proposal_id=? AND user_id=? AND organization_id=?",
                (pid, actor.user_id, actor.organization_id),
            ).fetchone()
        if not row:
            fail(404, "not_found", "Proposal not found in your scope.")
        p = json.loads(row["body"])
        self._scope(actor, p["scenario"])
        if row["actor_signature"] != signature(actor):
            fail(403, "membership_changed", "Membership changed. Prepare a new proposal.")
        self._authorize_action(actor, p["action"])
        return p, row["command_id"]

    def proposal(self, actor: Actor, proposal_id: str) -> dict:
        """Citește propunerea confirmabilă a emitentului, fără executare sau regenerare."""
        with self._lock():
            p, command_id = self._load_proposal(actor, proposal_id)
            if command_id:
                fail(409, "proposal_consumed", "This proposal was already confirmed. Retrieve its command.")
            if datetime.fromisoformat(p["expires_at"]) <= now():
                fail(409, "proposal_expired", "The proposal expired. Prepare a new proposal.")
            self._check_versions(actor, p)
            return self._public_proposal(p)

    def _check_versions(self, actor: Actor, p: dict):
        scenario, d = p["scenario"], p["data"]
        if self.planner.version(scenario) != p["plan_version"]:
            fail(409, "stale_plan", "The plan changed. Prepare a new proposal.")
        self._check_case_versions(actor, p)
        # Also recheck current route and connection access at confirmation.
        if d.get("work_item_id"):
            self._work_item(actor, scenario, d["work_item_id"])
        if d.get("connection_id"):
            self._connection(actor, scenario, d["connection_id"])
        if p["action"] == "record_verdict":
            with self.db.connect() as db:
                self._validate_proposal_photos(db, actor, p)

    def _validate_proposal_photos(self, db, actor: Actor, p: dict, *, original_id: str | None = None):
        d = p["data"]
        return photos.validate_refs(
            db,
            actor.organization_id,
            original_id or actor.user_id,
            p["scenario"],
            d["work_item_id"],
            d.get("photo_ids", []),
            p["actor_signature"],
            at=now(),
            frozen=d.get("photos", []),
        )

    def _check_case_versions(self, actor: Actor, p: dict):
        scenario, d = p["scenario"], p["data"]
        versions = dict(d.get("linked_case_versions", {}))
        if d.get("case_id"):
            versions[d["case_id"]] = d["case_version"]
        for cid, expected in versions.items():
            if self._case(actor, scenario, cid)["version"] != expected:
                fail(409, "stale_case", "The case changed. Prepare a new proposal.")
        if "linked_case_versions" in d:
            linked = self._cases(actor, scenario)
            if p["action"] != "approve_plan":
                linked = [c for c in linked if c["work_item_id"] == d["work_item_id"]]
            if {c["case_id"] for c in linked} != set(d["linked_case_versions"]):
                fail(409, "stale_case", "The linked cases changed. Prepare a new proposal.")

    def confirm(self, actor: Actor, proposal_id: str) -> dict:
        with self._lock():
            p, cid = self._load_proposal(actor, proposal_id)
            if cid:
                return self._resume(actor, p, cid)
            if datetime.fromisoformat(p["expires_at"]) <= now():
                fail(409, "proposal_expired", "The proposal expired. Prepare a new proposal.")
            with self.db.transaction() as db:
                self._check_versions(actor, p)
                if p["action"] == "record_verdict":
                    self._validate_proposal_photos(db, actor, p)
                if db.execute(
                    "SELECT 1 FROM commands WHERE organization_id=? AND scenario=? AND status=?",
                    (actor.organization_id, p["scenario"], "reconciling"),
                ).fetchone():
                    fail(
                        409,
                        "reconciliation_pending",
                        "Recover the pending command before confirming another operation.",
                    )
                cid = str(uuid.uuid4())
                cmd = {
                    "command_id": cid,
                    "proposal_id": proposal_id,
                    "status": "reconciling",
                    "action": p["action"],
                    "created_at": now().isoformat(),
                    "confirmed_by": {"user_id": actor.user_id, "role": actor.role},
                    "result": None,
                }
                db.execute(
                    "INSERT INTO commands VALUES (?,?,?,?,?,?,?)",
                    (cid, proposal_id, actor.user_id, actor.organization_id, p["scenario"], "reconciling", encode(cmd)),
                )
                db.execute("UPDATE proposals SET command_id=? WHERE proposal_id=?", (cid, proposal_id))
            return self._resume(actor, p, cid)

    @staticmethod
    def _can_recover(actor: Actor) -> bool:
        return actor.role == "dispatcher" and "recover_commands" in actor.permissions

    def _recovery_options(self, p: dict, cmd: dict) -> dict:
        state = self.planner.effect_status(cmd["command_id"], p) if p["action"] in PLANNER_ACTIONS else "not_started"
        action = (
            "retrieve"
            if state in ("applied", "partially_applied")
            else ("cancel" if state in ("not_started", "prepared") else "manual_review")
        )
        return {
            "effect_status": state,
            "action": action,
            "allowed_decisions": ["cancel"] if action == "cancel" else [],
            "requires_confirmation": action == "cancel",
        }

    def _command_row(self, actor: Actor, command_id: str):
        with self.db.connect() as db:
            row = db.execute(
                "SELECT c.*, p.body AS proposal_body FROM commands c JOIN proposals p "
                "ON p.proposal_id=c.proposal_id WHERE c.command_id=? AND c.organization_id=?",
                (command_id, actor.organization_id),
            ).fetchone()
        if not row or (row["user_id"] != actor.user_id and not self._can_recover(actor)):
            fail(404, "not_found", "Command not found in your scope.")
        self._scope(actor, row["scenario"])
        return row

    def _recovery_audit(self, actor: Actor, row, cmd: dict, decision: str, reason: str | None = None) -> dict:
        audit = {
            "recovery_id": str(uuid.uuid4()),
            "command_id": cmd["command_id"],
            "confirmed_by": cmd.get("confirmed_by", {"user_id": row["user_id"], "role": None}),
            "reconciled_by": {
                "user_id": actor.user_id,
                "role": actor.role,
                "permission": "recover_commands",
                "membership_signature": signature(actor),
            },
            "decision": decision,
            "reason": reason,
            "created_at": now().isoformat(),
            "status": "started",
        }
        with self.db.transaction() as db:
            db.execute(
                "INSERT INTO command_recoveries VALUES (?,?,?,?,?)",
                (audit["recovery_id"], cmd["command_id"], actor.organization_id, row["scenario"], encode(audit)),
            )
        return audit

    def command(self, actor: Actor, command_id: str) -> dict:
        with self._lock():
            row = self._command_row(actor, command_id)
            p, cmd = json.loads(row["proposal_body"]), json.loads(row["body"])
            if self._can_recover(actor):
                if cmd["status"] != "reconciling":
                    return cmd
                recovery = self._recovery_options(p, cmd)
                if recovery["action"] != "retrieve":
                    return {**cmd, "recovery": recovery}
                # Current dispatcher authority adopts only the immutable, already-published effect.
                audit = self._recovery_audit(actor, row, cmd, "reconcile_published_effect")
                return self._resume(actor, p, command_id, recovery_audit=audit)
            p, _ = self._load_proposal(actor, row["proposal_id"])
            return self._resume(actor, p, command_id)

    def recover(self, actor: Actor, command_id: str, decision: str, reason: str) -> dict:
        with self._lock():
            row = self._command_row(actor, command_id)
            if not self._can_recover(actor):
                fail(403, "forbidden", "Explicit dispatcher recovery permission is required.")
            p, cmd = json.loads(row["proposal_body"]), json.loads(row["body"])
            if decision != "cancel" or not isinstance(reason, str) or not 3 <= len(reason.strip()) <= 2000:
                fail(422, "invalid_recovery", "Provide an explicit cancellation and reason.")
            if cmd["status"] != "reconciling":
                return cmd
            if self._recovery_options(p, cmd)["action"] != "cancel":
                fail(
                    409,
                    "effect_already_published",
                    "A published or uncertain effect cannot be cancelled. Recover or review it.",
                )
            audit = self._recovery_audit(actor, row, cmd, "cancel_unpublished", reason.strip())
            cmd.update(
                status="cancelled",
                result={"cancelled": True, "effect_published": False},
                completed_at=now().isoformat(),
                recovery=audit,
            )
            cmd.pop("error", None)
            audit.update(status="completed", completed_at=cmd["completed_at"])
            with self.db.transaction() as db:
                self._event(db, actor, p, command_id, None, "cancelled", audit=audit)
                db.execute(
                    "UPDATE commands SET status=?,body=? WHERE command_id=?", ("cancelled", encode(cmd), command_id)
                )
                db.execute(
                    "UPDATE command_recoveries SET body=? WHERE recovery_id=?", (encode(audit), audit["recovery_id"])
                )
            return cmd

    def _resume(self, actor: Actor, p: dict, cid: str, *, recovery_audit: dict | None = None) -> dict:
        with self.db.connect() as db:
            row = db.execute("SELECT body FROM commands WHERE command_id=?", (cid,)).fetchone()
        cmd = json.loads(row["body"])
        if cmd["status"] != "reconciling":
            return cmd
        try:
            if recovery_audit:
                self._check_case_versions(actor, p)
            original_id = recovery_audit["confirmed_by"]["user_id"] if recovery_audit else actor.user_id
            if p["action"] == "record_verdict":
                with self.db.transaction() as db:
                    self._validate_proposal_photos(db, actor, p, original_id=original_id)
            effect = (
                self.planner.execute(cmd, p, original_id, recover_only=bool(recovery_audit))
                if p["action"] in PLANNER_ACTIONS
                else {}
            )
            with self.db.transaction() as db:
                result = self._apply(db, actor, p, cid, effect, audit=recovery_audit)
                cmd.update(status="succeeded", result=result, completed_at=now().isoformat())
                cmd.pop("error", None)
                if recovery_audit:
                    recovery_audit.update(status="completed", completed_at=cmd["completed_at"])
                    cmd["recovery"] = recovery_audit
                    db.execute(
                        "UPDATE command_recoveries SET body=? WHERE recovery_id=?",
                        (encode(recovery_audit), recovery_audit["recovery_id"]),
                    )
                db.execute("UPDATE commands SET status=?,body=? WHERE command_id=?", ("succeeded", encode(cmd), cid))
            return cmd
        except Exception as exc:  # noqa: BLE001 - persist recoverable partial effect without exposing private exception
            # Result is recoverable by command id. Never report a partial file publication as success.
            code = exc.code if isinstance(exc, OperationError) else "effect_unavailable"
            cmd.update(
                status="reconciling",
                error={
                    "code": code,
                    "message": "Operation pending verification. Retrieve this command before retrying.",
                },
            )
            with self.db.transaction() as db:
                if recovery_audit:
                    recovery_audit.update(status="reconciling", error_code=code)
                    cmd["recovery"] = recovery_audit
                    db.execute(
                        "UPDATE command_recoveries SET body=? WHERE recovery_id=?",
                        (encode(recovery_audit), recovery_audit["recovery_id"]),
                    )
                db.execute("UPDATE commands SET body=? WHERE command_id=?", (encode(cmd), cid))
            return cmd

    def _event(
        self,
        db,
        actor: Actor,
        p: dict,
        cid: str,
        case: dict | None,
        status: str,
        *,
        audit: dict | None = None,
        details: dict | None = None,
    ):
        event = {
            "event_id": str(uuid.uuid4()),
            "command_id": cid,
            "case_id": case["case_id"] if case else None,
            "created_at": now().isoformat(),
            "actor_id": actor.user_id,
            "role": actor.role,
            "action": p["action"],
            "status": status,
            "plan_version": p["plan_version"],
            "synthetic": True,
        }
        if audit:
            event.update(
                actor_id=audit["confirmed_by"]["user_id"],
                role=audit["confirmed_by"]["role"],
                reconciled_by=audit["reconciled_by"],
                recovery_id=audit["recovery_id"],
            )
        if p["action"] == "request_human" and status != "cancelled":
            event["human_request"] = {
                "request_id": cid,
                "reason": p["data"]["reason"],
                "priority": p["data"]["priority"],
                "status": "queued",
                "connection_id": p["data"].get("connection_id"),
                "external_contact": False,
            }
        if case:
            event["case_version"] = case["version"]
            event["prediction_id"] = case.get("assessment", {}).get("prediction_id")
            event["model_version"] = case.get("assessment", {}).get("model_version")
        if p["data"].get("work_item_id"):
            event["work_item_id"] = p["data"]["work_item_id"]
        for key in ("finding", "manual_correction"):
            if details and key in details:
                event[key] = details[key]
        db.execute(
            "INSERT INTO events VALUES (?,?,?,?,?,?)",
            (event["event_id"], cid, event["case_id"], actor.organization_id, p["scenario"], encode(event)),
        )
        return event["event_id"]

    def _save_case(self, db, case: dict):
        db.execute(
            "INSERT INTO cases VALUES (?,?,?,?,?,?,?) ON CONFLICT(case_id) DO UPDATE SET version=excluded.version,body=excluded.body",
            (
                case["case_id"],
                case["organization_id"],
                case["scenario"],
                case["connection_id"],
                case["requester_id"],
                case["version"],
                encode(case),
            ),
        )

    def _apply(self, db, actor: Actor, p: dict, cid: str, effect: dict, *, audit: dict | None = None) -> dict:
        action, d, scenario = p["action"], p["data"], p["scenario"]
        result = {"effect": effect, "synthetic": True, "repaired": False}
        original_actor = audit["confirmed_by"] if audit else {"user_id": actor.user_id, "role": actor.role}
        common = {
            "work_item_id": d.get("work_item_id"),
            "actor_id": original_actor["user_id"],
            "actor_role": original_actor["role"],
            "created_at": now().isoformat(),
            "command_id": cid,
        }
        if audit:
            common.update(reconciled_by=audit["reconciled_by"], recovery_id=audit["recovery_id"])
        if action == "record_verdict":
            attached = self._validate_proposal_photos(db, actor, p, original_id=original_actor["user_id"])
            attached = [{**metadata, "status": "attached"} for metadata in attached]
            finding = {
                **common,
                "finding_id": cid,
                "outcome": d["outcome"],
                "note": d.get("note"),
                "photos": attached,
                "repair_confirmed": False,
            }
            db.execute(
                "INSERT INTO findings VALUES (?,?,?,?,?)",
                (cid, actor.organization_id, scenario, d["work_item_id"], encode(finding)),
            )
            for metadata in attached:
                db.execute(
                    "UPDATE photos SET status='attached',body=?,command_id=? WHERE photo_id=?",
                    (encode(metadata), cid, metadata["photo_id"]),
                )
            result["finding"] = finding
        elif action == "review_work_item":
            correction = {
                **common,
                "original_ai_decision": d.get("original_ai_decision"),
                "original_ai_decision_status": d.get("original_ai_decision_status", "unknown"),
                "decision_before": d.get("decision_before"),
                "decision_after": effect.get("decision_after"),
                "requested_decision": d["decision"],
                "reason": d.get("note"),
                "is_correction": d.get("is_correction", False),
            }
            db.execute(
                "INSERT INTO manual_corrections VALUES (?,?,?,?,?)",
                (cid, actor.organization_id, scenario, d["work_item_id"], encode(correction)),
            )
            result["manual_correction"] = correction
        changed = []
        if action == "create_case":
            existing = [
                c
                for c in self._cases(actor, scenario)
                if c["connection_id"] == d["connection_id"]
                and c["symptom_type"] == d["symptom_type"]
                and c["symptom"].casefold().strip() == d["symptom"].casefold().strip()
                and c["status"] not in ("closed", "resolved")
            ]
            if existing:
                return {**result, "case": self._public_case(actor, existing[0]), "deduplicated": True}
            connection = self._connection(actor, scenario, d["connection_id"])
            assessment = self._case_assessment(connection, d["symptom_type"], scenario)
            case = {
                "case_id": str(uuid.uuid4()),
                "organization_id": actor.organization_id,
                "scenario": scenario,
                "connection_id": connection["connection_id"],
                "post_id": connection["post_id"],
                "requester_id": actor.user_id,
                "work_item_id": assessment.get("work_item_id"),
                "symptom": d["symptom"],
                "symptom_type": d["symptom_type"],
                "version": 1,
                "status": "awaiting_decision" if assessment["status"] == "available" else "awaiting_data",
                "assessment": assessment,
                "synthetic": True,
                "created_at": now().isoformat(),
                "updated_at": now().isoformat(),
                "next_step": "Dispatcher review; no visit or repair is confirmed.",
            }
            changed.append(case)
        elif action in ("set_availability", "request_human"):
            if d.get("case_id"):
                case = self._case(actor, scenario, d["case_id"])
                case.update(version=case["version"] + 1, updated_at=now().isoformat())
                if action == "set_availability":
                    case["availability"] = {"start": d["start"], "end": d["end"], "status": "requested"}
                else:
                    case.update(human_requested=True, next_step="Awaiting human review in the shared queue.")
                changed.append(case)
            if action == "request_human":
                result["human_request"] = {
                    "request_id": cid,
                    "status": "queued",
                    "priority": d["priority"],
                    "reason": d["reason"],
                    "connection_id": d.get("connection_id"),
                    "external_contact": False,
                }
        elif action in PLANNER_ACTIONS:
            all_cases = self._cases(actor, scenario)
            if action == "approve_plan":
                plan = self.planner.view(scenario).plan() or {}
                assigned = {
                    s["work_item_id"]
                    for r in plan.get("routes", [])
                    if not d.get("crew_id") or r["crew_id"] == d["crew_id"]
                    for s in r.get("stops", [])
                }
                changed = [c for c in all_cases if c["work_item_id"] in assigned]
                for c in changed:
                    c.update(
                        status="intervention_approved",
                        next_step="Approved intervention; no arrival time or repair confirmed.",
                    )
            else:
                changed = [c for c in all_cases if c["work_item_id"] == d["work_item_id"]]
                for c in changed:
                    if action == "record_verdict":
                        c["status"] = "access_blocked" if d["outcome"] == "no_access" else "verification_after_visit"
                        c["verdict"] = {
                            "outcome": d["outcome"],
                            "command_id": cid,
                            "prediction_id": effect.get("label", {}).get("prediction_id"),
                            "repair_confirmed": False,
                            "finding_id": cid,
                            "note": d.get("note"),
                            "photos": result["finding"]["photos"],
                        }
                        c["next_step"] = (
                            "Dispatcher must arrange access."
                            if d["outcome"] == "no_access"
                            else "Human follow-up required; repair not confirmed."
                        )
                    else:
                        c.update(
                            status="awaiting_plan_approval" if d["decision"] == "approve" else "awaiting_decision",
                            next_step="Dispatcher must review and approve the recalculated plan.",
                        )
            for c in changed:
                c.update(version=c["version"] + 1, updated_at=now().isoformat())
        event_ids = []
        for case in changed:
            self._save_case(db, case)
            event_ids.append(self._event(db, actor, p, cid, case, case["status"], audit=audit, details=result))
        if not changed:
            event_ids.append(
                self._event(
                    db,
                    actor,
                    p,
                    cid,
                    None,
                    result.get("human_request", {}).get("status", "succeeded"),
                    audit=audit,
                    details=result,
                )
            )
        if changed:
            result["cases"] = [self._public_case(actor, c) for c in changed]
            result["case"] = result["cases"][0]
        result["event_ids"] = event_ids
        result["plan_version"] = self.planner.version(scenario)
        return result


@lru_cache(maxsize=1)
def get_service() -> OperationsService:
    return OperationsService()
