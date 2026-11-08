"""Durable task metadata. Callers must freshly authorize before every access.

Claims are metadata leases, never authority to execute operational effects.
"""

import hashlib
import json
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .contracts import TaskView


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _owner(actor):
    data = actor.model_dump(mode="json")
    for key in ("permissions", "connection_ids"):
        data[key] = sorted(data.get(key, []))
    return hashlib.sha256(_json(data).encode()).hexdigest()


def _now():
    return datetime.now(UTC).isoformat()


class TaskStore:
    def __init__(self, path):
        if str(path) == ":memory:":
            raise ValueError("A durable explicit database path is required")
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch(mode=0o600, exist_ok=True)
        target.chmod(0o600)
        self.path = str(target)
        with self._db() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS agent_tasks (id TEXT PRIMARY KEY, owner TEXT NOT NULL, request_key TEXT, request_hash TEXT NOT NULL, body TEXT NOT NULL, lease TEXT, lease_until REAL, UNIQUE(owner, request_key))"
            )

            if "request_json" not in {row[1] for row in db.execute("PRAGMA table_info(agent_tasks)")}:
                db.execute("ALTER TABLE agent_tasks ADD COLUMN request_json TEXT")

    def request(self, actor, task_id):
        """Internal immutable request; callers must freshly authorize the actor first."""
        from .contracts import TaskRequest

        with self._db() as db:
            self._read(db, actor, task_id)
            row = db.execute("SELECT request_json FROM agent_tasks WHERE id=?", (task_id,)).fetchone()
        if not row or not row[0]:
            raise ValueError("This historical task cannot be resumed; start a fresh task")
        return TaskRequest.model_validate_json(row[0])

    def _db(self):
        return sqlite3.connect(self.path, timeout=5)

    def create(self, actor, request, plan_version):
        owner = _owner(actor)
        payload = request.model_dump(mode="json")
        digest = hashlib.sha256(_json(payload).encode()).hexdigest()
        stamp = _now()
        view = TaskView(
            task_id=str(uuid4()),
            goal=request.goal,
            scenario=request.scenario,
            status="queued",
            plan_version=plan_version,
            created_at=stamp,
            updated_at=stamp,
        )
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            if request.request_key is not None:
                row = db.execute(
                    "SELECT request_hash, body FROM agent_tasks WHERE owner=? AND request_key=?",
                    (owner, request.request_key),
                ).fetchone()
                if row:
                    if row[0] != digest:
                        raise ValueError("request_key conflicts with an existing request")
                    return TaskView.model_validate_json(row[1])
            db.execute(
                "INSERT INTO agent_tasks(id,owner,request_key,request_hash,body,request_json) VALUES(?,?,?,?,?,?)",
                (view.task_id, owner, request.request_key, digest, view.model_dump_json(), request.model_dump_json()),
            )
        return view

    def _read(self, db, actor, task_id):
        row = db.execute(
            "SELECT body,lease,lease_until FROM agent_tasks WHERE id=? AND owner=?", (task_id, _owner(actor))
        ).fetchone()
        if row is None:
            raise PermissionError("Task unavailable for current membership")
        return row

    def get(self, actor, task_id):
        with self._db() as db:
            return TaskView.model_validate_json(self._read(db, actor, task_id)[0])

    def list(self, actor, scenario):
        with self._db() as db:
            rows = db.execute("SELECT body FROM agent_tasks WHERE owner=? ORDER BY rowid", (_owner(actor),)).fetchall()
        return [v for (body,) in rows if (v := TaskView.model_validate_json(body)).scenario == scenario]

    def update(self, actor, task_id, **fields):
        token = fields.pop("claim_token", None)
        allowed = {"status", "reply", "result", "proposal", "error"}
        if fields.keys() - allowed:
            raise ValueError("Immutable or unknown task field")
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            body, lease, until = self._read(db, actor, task_id)
            if lease and (token != lease or until <= time.time()):
                raise ValueError("Current claim required")
            view = TaskView.model_validate_json(body)
            if view.status in {"completed", "cancelled", "failed"}:
                raise ValueError("Terminal task is immutable")
            transitions = {
                "queued": {"running", "cancelled", "failed"},
                "running": {
                    "running",
                    "needs_information",
                    "awaiting_confirmation",
                    "completed",
                    "failed",
                    "cancelled",
                    "needs_reconciliation",
                },
                "needs_information": {"running", "cancelled", "failed"},
                "awaiting_confirmation": {"running", "completed", "cancelled", "failed", "needs_reconciliation"},
                "needs_reconciliation": {"running", "completed", "failed", "cancelled"},
            }
            if fields.get("status", view.status) not in transitions.get(view.status, set()):
                raise ValueError("Invalid task transition")
            if token is not None and token != lease:
                raise ValueError("Stale claim")
            updated = TaskView.model_validate({**view.model_dump(), **fields, "updated_at": _now()})
            db.execute(
                "UPDATE agent_tasks SET body=?,lease=NULL,lease_until=NULL WHERE id=?",
                (updated.model_dump_json(), task_id),
            )
            return updated

    def claim(self, actor, task_id, *, seconds=30):
        """Return a fencing token; expired work can be reclaimed after restart."""
        if not 0 < seconds <= 180:
            raise ValueError("Claim duration must be between zero and 180 seconds")
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            body, lease, until = self._read(db, actor, task_id)
            view = TaskView.model_validate_json(body)
            if view.status not in {
                "queued",
                "running",
                "needs_information",
                "needs_reconciliation",
                "awaiting_confirmation",
            } or (lease and until > time.time()):
                return None
            token = str(uuid4())
            view.status = "running"
            view.updated_at = _now()
            db.execute(
                "UPDATE agent_tasks SET body=?,lease=?,lease_until=? WHERE id=?",
                (view.model_dump_json(), token, time.time() + seconds, task_id),
            )
            return token
