"""Private durable voice work, independent of calls and the WhatsApp outbox.

Integration contract:
* Construct VoiceJobs(runtime / 'voice-jobs.sqlite3') in the ASGI lifespan.
  Call recover_expired() on startup and periodically; it never steals a live lease.
* submit(verified_actor, 'report' | 'dispatch', trusted_payload, event_key) is
  synchronous and returns a job dict. payload MUST contain conversation_id; the
  caller/destination and verifiedActor snapshot come only from trusted root code.
  An event key is immutable: identical actor/kind/payload retries return the same
  job, including after completion; conflicting reuse raises ValueError.
* Respond immediately after submit. For PDF: 'Pregătesc raportul și îl trimit pe
  WhatsApp.' A lifespan-owned task periodically awaits drain_one(handler), separate
  from the voice response/call task, so barge-in cannot cancel background work.
* async handler(job) -> JSON dict receives job_id, event_key, verifiedActor,
  payload and conversation_id. Reconstruct Actor from verifiedActor, reauthorize
  against CURRENT identity/membership before work AND immediately before effects.
  The snapshot is evidence, never fresh authorization. The report handler calls
  actual send_voice_report with the original event_key and its existing durable
  Meta outbox; the dispatch handler runs the actual LLM. Neither is wired here.
* A returned dict is persisted as result. status 'failed' or
  'needs_reconciliation' selects that terminal state; 'unknown'/'sending' also
  select needs_reconciliation. Other results finish done. Raise VoiceJobFailed
  only for a KNOWN failure without an uncertain effect (e.g. rejected reauth).
  Unhandled exceptions, cancellation and expired leases require reconciliation;
  they are NEVER automatically retried. Reconcile against the underlying durable
  effect ledger before deciding whether any new attempt is safe. This store does
  not promise exactly-once external effects and has no automatic retry API.
* get(job_id, actor=...) and latest(actor, conversation_id) are private reads.
  Omit actor only in trusted root code. Never expose these dicts as public status.

SQLite transactions end before any await/network work. Each claim has a unique
lease token; heartbeat and completion require that token AND an unexpired lease.
A stale worker cannot overwrite recovery. Handlers must cooperate with asyncio
cancellation and offload blocking work; no queue can fence an external side effect
without the downstream system's own idempotency/authorization checks.
"""

from __future__ import annotations

import asyncio
import json
import math
import sqlite3
import time
from collections.abc import Awaitable, Callable
from contextlib import closing
from pathlib import Path
from uuid import uuid4


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _actor(actor):
    value = actor.model_dump(mode="json") if hasattr(actor, "model_dump") else actor
    if not isinstance(value, dict) or not value:
        raise ValueError("A verified actor snapshot is required")
    return _json(value)


class VoiceJobFailed(Exception):
    """Known failure; caller guarantees no uncertain external outcome."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class VoiceJobs:
    def __init__(self, path: str | Path, *, lease_seconds: float = 180, clock=time.time):
        if not math.isfinite(lease_seconds) or lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive and finite")
        self.path = Path(path)
        self.lease_seconds, self.clock = lease_seconds, clock
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(mode=0o600, exist_ok=True)
        self.path.chmod(0o600)
        with closing(self._connect()) as db, db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS voice_jobs (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL UNIQUE, event_key TEXT NOT NULL UNIQUE,
                    actor TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('report','dispatch')),
                    payload TEXT NOT NULL, conversation_id TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN
                        ('queued','running','done','failed','needs_reconciliation')),
                    created REAL NOT NULL, updated REAL NOT NULL,
                    lease_token TEXT, lease_until REAL, attempts INTEGER NOT NULL DEFAULT 0,
                    result TEXT, error TEXT
                );
                CREATE INDEX IF NOT EXISTS voice_jobs_latest
                    ON voice_jobs(actor, conversation_id, sequence DESC);
            """)

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def _decode(row):
        if row is None:
            return None
        job = dict(row)
        job["verifiedActor"] = json.loads(job.pop("actor"))
        for key in ("payload", "result", "error"):
            job[key] = json.loads(job[key]) if job[key] is not None else None
        return job

    def submit(self, actor, kind: str, payload: dict, event_key: str) -> dict:
        if kind not in {"report", "dispatch"}:
            raise ValueError("Unsupported voice job kind")
        if not isinstance(event_key, str) or not event_key.strip():
            raise ValueError("A trusted event_key is required")
        if not isinstance(payload, dict):
            raise TypeError("A trusted payload is required")
        conversation = payload.get("conversation_id")
        if not isinstance(conversation, str) or not conversation.strip():
            raise ValueError("conversation_id is required in payload")
        snapshot, encoded = _actor(actor), _json(payload)
        now = self.clock()
        with closing(self._connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM voice_jobs WHERE event_key=?", (event_key,)).fetchone()
            if row:
                if (row["actor"], row["kind"], row["payload"]) != (snapshot, kind, encoded):
                    raise ValueError("event_key conflicts with actor, kind or payload")
                return self._decode(row)
            job_id = uuid4().hex
            db.execute(
                "INSERT INTO voice_jobs(job_id,event_key,actor,kind,payload,conversation_id,status,created,updated) "
                "VALUES(?,?,?,?,?,?,'queued',?,?)",
                (job_id, event_key, snapshot, kind, encoded, conversation, now, now),
            )
            return self._decode(db.execute("SELECT * FROM voice_jobs WHERE job_id=?", (job_id,)).fetchone())

    def get(self, job_id: str, *, actor=None) -> dict | None:
        with closing(self._connect()) as db:
            row = db.execute("SELECT * FROM voice_jobs WHERE job_id=?", (job_id,)).fetchone()
            if row is None or (actor is not None and row["actor"] != _actor(actor)):
                return None
            return self._decode(row)

    def latest(self, actor, conversation_id: str) -> dict | None:
        with closing(self._connect()) as db:
            return self._decode(
                db.execute(
                    "SELECT * FROM voice_jobs WHERE actor=? AND conversation_id=? ORDER BY sequence DESC LIMIT 1",
                    (_actor(actor), conversation_id),
                ).fetchone()
            )

    def recover_expired(self) -> int:
        now = self.clock()
        with closing(self._connect()) as db, db:
            return db.execute(
                "UPDATE voice_jobs SET status='needs_reconciliation', updated=?, lease_token=NULL, "
                "lease_until=NULL, error=? WHERE status='running' AND lease_until<=?",
                (now, _json({"code": "lease_expired"}), now),
            ).rowcount

    def _claim(self):
        self.recover_expired()
        with closing(self._connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM voice_jobs WHERE status='queued' ORDER BY sequence LIMIT 1").fetchone()
            if row is None:
                return None
            now = self.clock()
            db.execute(
                "UPDATE voice_jobs SET status='running', lease_token=?, lease_until=?, updated=?, "
                "attempts=attempts+1 WHERE job_id=?",
                (uuid4().hex, now + self.lease_seconds, now, row["job_id"]),
            )
            return self._decode(db.execute("SELECT * FROM voice_jobs WHERE job_id=?", (row["job_id"],)).fetchone())

    def _renew(self, job):
        now = self.clock()
        with closing(self._connect()) as db, db:
            return (
                db.execute(
                    "UPDATE voice_jobs SET lease_until=?, updated=? WHERE job_id=? AND lease_token=? "
                    "AND status='running' AND lease_until>?",
                    (now + self.lease_seconds, now, job["job_id"], job["lease_token"], now),
                ).rowcount
                == 1
            )

    def _finish(self, job, status, result=None, error=None):
        now = self.clock()
        encoded_result = None if result is None else _json(result)
        encoded_error = None if error is None else _json(error)
        with closing(self._connect()) as db, db:
            return (
                db.execute(
                    "UPDATE voice_jobs SET status=?, result=?, error=?, updated=?, lease_token=NULL, "
                    "lease_until=NULL WHERE job_id=? AND lease_token=? AND status='running' AND lease_until>?",
                    (status, encoded_result, encoded_error, now, job["job_id"], job["lease_token"], now),
                ).rowcount
                == 1
            )

    async def drain_one(self, handler: Callable[[dict], Awaitable[dict]]) -> dict | None:
        """Claim at most one job; return persisted state, or None when no work exists."""
        job = await asyncio.to_thread(self._claim)
        if job is None:
            return None

        async def heartbeat():
            while True:
                await asyncio.sleep(self.lease_seconds / 3)
                if not await asyncio.to_thread(self._renew, job):
                    raise RuntimeError("lease_lost")

        async def invoke():
            # Do not let a handler mutate the fencing token or stored snapshot.
            return await handler(json.loads(_json(job)))

        work = asyncio.create_task(invoke())
        beat = asyncio.create_task(heartbeat())
        try:
            completed, _ = await asyncio.wait((work, beat), return_when=asyncio.FIRST_COMPLETED)
            if beat in completed:
                await beat
            result = await work
            if not isinstance(result, dict):
                raise TypeError("handler must return a JSON dict")
            state = result.get("status")
            status = state if state in ("failed", "needs_reconciliation") else "done"
            if state in ("unknown", "sending"):
                status = "needs_reconciliation"
            self._finish(job, status, result=result)
        except asyncio.CancelledError:
            self._finish(job, "needs_reconciliation", error={"code": "cancelled"})
            raise
        except VoiceJobFailed as exc:
            self._finish(job, "failed", error={"code": exc.code})
        except Exception as exc:  # noqa: BLE001 - every uncertain handler failure must be durably quarantined
            # Persist type only: exception messages may contain private tokens.
            self._finish(job, "needs_reconciliation", error={"code": type(exc).__name__})
        finally:
            work.cancel()
            beat.cancel()
            await asyncio.gather(work, beat, return_exceptions=True)
        self.recover_expired()
        return self.get(job["job_id"])
