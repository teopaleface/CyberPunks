"""Coada de intrare și registrul de ieșire au tranzacții independente de rețea."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
from pathlib import Path

from cyberpunks.channels.models import ChannelError


def event_key(destination: str, message_id: str) -> str:
    return "wa:" + hashlib.sha256((destination + ":" + message_id).encode()).hexdigest()


def actor_key(actor) -> str:
    return hashlib.sha256(actor.model_dump_json().encode()).hexdigest()


class DeliveryStore:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(mode=0o600, exist_ok=True)
        path.chmod(0o600)
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS inbound_queue (
                    event_id TEXT PRIMARY KEY, destination TEXT NOT NULL, sender TEXT NOT NULL,
                    message TEXT NOT NULL, actor_signature TEXT NOT NULL,
                    state TEXT NOT NULL, created REAL NOT NULL, retry_at REAL NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0, error_code TEXT
                );
                CREATE TABLE IF NOT EXISTS outbound_reports (event_id TEXT PRIMARY KEY, report_id TEXT NOT NULL, plan_version TEXT NOT NULL, page_count INTEGER NOT NULL, case_versions TEXT NOT NULL DEFAULT '{}', format TEXT NOT NULL DEFAULT 'png', manifest TEXT);
                CREATE TABLE IF NOT EXISTS outbound_media (part_id TEXT PRIMARY KEY, payload BLOB NOT NULL);
                CREATE TABLE IF NOT EXISTS outbound (
                    part_id TEXT PRIMARY KEY, event_id TEXT NOT NULL, destination TEXT NOT NULL,
                    recipient_hash TEXT NOT NULL, kind TEXT NOT NULL, payload_hash TEXT NOT NULL,
                    state TEXT NOT NULL, updated REAL NOT NULL, media_id TEXT,
                    provider_message_id TEXT UNIQUE, error_code TEXT
                );
            """)

            columns = {row[1] for row in db.execute("PRAGMA table_info(outbound_reports)")}
            if "case_versions" not in columns:
                db.execute("ALTER TABLE outbound_reports ADD COLUMN case_versions TEXT NOT NULL DEFAULT '{}'")
            if "format" not in columns:
                db.execute("ALTER TABLE outbound_reports ADD COLUMN format TEXT NOT NULL DEFAULT 'png'")
            if "manifest" not in columns:
                db.execute("ALTER TABLE outbound_reports ADD COLUMN manifest TEXT")

    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        return db

    def enqueue(self, destination: str, sender: str, message: dict, actor) -> bool:
        eid = event_key(destination, message["id"])
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            exists = db.execute("SELECT 1 FROM inbound_queue WHERE event_id=?", (eid,)).fetchone()
            if exists:
                return False
            count = db.execute(
                "SELECT count(*) FROM inbound_queue WHERE state IN ('queued','processing','retryable')"
            ).fetchone()[0]
            if count >= 100:
                raise ChannelError("whatsapp_queue_full", "The inbound queue is full. Retry later.", 503)
            try:
                db.execute(
                    "INSERT INTO inbound_queue(event_id,destination,sender,message,actor_signature,state,created,retry_at) "
                    "VALUES(?,?,?,?,?,'queued',?,0)",
                    (eid, destination, sender, json.dumps(message), actor_key(actor), time.time()),
                )
            except sqlite3.IntegrityError:
                return False
        return True

    def next(self) -> dict | None:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM inbound_queue WHERE state IN ('queued','retryable') AND retry_at<=? ORDER BY created,event_id LIMIT 1",
                (time.time(),),
            ).fetchone()
            if row is None:
                return None
            db.execute(
                "UPDATE inbound_queue SET state='processing',attempts=attempts+1 WHERE event_id=?", (row["event_id"],)
            )
        result = dict(row)
        result["message"] = json.loads(result["message"])
        return result

    @staticmethod
    def _record_delivery(db, event_id: str) -> str:
        # The caller holds BEGIN IMMEDIATE. Never use a transport return value that a callback
        # may already have superseded; decide only from this locked outbox snapshot.
        parts = {
            row["kind"]: row["state"]
            for row in db.execute("SELECT kind,state FROM outbound WHERE event_id=?", (event_id,))
        }
        states = set(parts.values())
        if states & {"unknown", "sending"}:
            state, code = "needs_reconciliation", "meta_outcome_unknown"
        elif parts.get("text") in {"failed", "rejected", "cancelled"}:
            state, code = "failed", "meta_rejected"
        elif "prepared" in states:
            state, code = "queued", None
        elif states & {"accepted", "delivered", "read"}:
            # A failed/cancelled optional audio part does not discard accepted text.
            state, code = "accepted", None
        else:
            state, code = "failed", "meta_rejected"
        db.execute("UPDATE inbound_queue SET state=?,error_code=?,retry_at=0 WHERE event_id=?", (state, code, event_id))
        return state

    def record_delivery(self, event_id: str) -> str:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            return self._record_delivery(db, event_id)

    def recover(self):
        # Called only while holding the exclusive worker lock. A previous worker is no longer alive.
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE outbound SET state='unknown',error_code='worker_interrupted' WHERE state='sending'")
            db.execute("UPDATE inbound_queue SET state='queued' WHERE state='processing'")
            # Also recover an old waiting decision whose signed status has already resolved.
            for row in db.execute("SELECT event_id FROM inbound_queue WHERE state='needs_reconciliation'").fetchall():
                self._record_delivery(db, row["event_id"])

    def queue_state(self, eid: str, state: str, code: str | None = None, *, delay=0):
        with self.connect() as db:
            db.execute(
                "UPDATE inbound_queue SET state=?,error_code=?,retry_at=? WHERE event_id=?",
                (state, code, time.time() + delay, eid),
            )

    def prepare(self, eid: str, destination: str, sender: str, kind: str, payload: bytes) -> dict:
        part = hashlib.sha256((eid + ":" + kind).encode()).hexdigest()
        recipient = hashlib.sha256(sender.encode()).hexdigest()
        digest = hashlib.sha256(payload).hexdigest()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "INSERT OR IGNORE INTO outbound(part_id,event_id,destination,recipient_hash,kind,payload_hash,state,updated) "
                "VALUES(?,?,?,?,?,?,'prepared',?)",
                (part, eid, destination, recipient, kind, digest, time.time()),
            )
            row = db.execute("SELECT * FROM outbound WHERE part_id=?", (part,)).fetchone()
            if row["recipient_hash"] != recipient or row["destination"] != destination or row["payload_hash"] != digest:
                raise ChannelError(
                    "outbound_conflict", "The durable reply no longer matches this inbound message.", 409
                )
            if kind.startswith(("image:", "document:")):
                db.execute("INSERT OR IGNORE INTO outbound_media VALUES (?,?)", (part, payload))
        return dict(row)

    def prepare_report(
        self,
        eid: str,
        destination: str,
        sender: str,
        report_id: str,
        version: str,
        pages: list[dict],
        case_versions: dict | None = None,
    ):
        """Freeze the complete report and every page in one transaction before delivery."""
        recipient = hashlib.sha256(sender.encode()).hexdigest()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute("SELECT * FROM outbound_reports WHERE event_id=?", (eid,)).fetchone()
            if previous:
                if (
                    previous["report_id"] != report_id
                    or previous["plan_version"] != version
                    or previous["format"] != "png"
                ):
                    raise ChannelError("outbound_conflict", "The report source changed.", 409)
                return
            for page in pages:
                kind = "image:" + report_id + "_" + str(page["page"]).zfill(3)
                part = hashlib.sha256((eid + ":" + kind).encode()).hexdigest()
                digest = hashlib.sha256(page["png"]).hexdigest()
                if digest != page["sha256"]:
                    raise ChannelError("outbound_conflict", "Report integrity check failed.", 409)
                db.execute(
                    "INSERT INTO outbound(part_id,event_id,destination,recipient_hash,kind,payload_hash,state,updated) VALUES(?,?,?,?,?,?,'prepared',?)",
                    (part, eid, destination, recipient, kind, digest, time.time()),
                )
                db.execute("INSERT INTO outbound_media VALUES(?,?)", (part, page["png"]))
            db.execute(
                "INSERT INTO outbound_reports(event_id,report_id,plan_version,page_count,case_versions) VALUES(?,?,?,?,?)",
                (eid, report_id, version, len(pages), json.dumps(case_versions or {})),
            )

    def prepare_report_pdf(
        self,
        eid: str,
        destination: str,
        sender: str,
        report_id: str,
        version: str,
        pdf: bytes,
        *,
        sha256: str,
        page_count: int,
        source_pages: int | None = None,
        case_versions: dict | None = None,
    ) -> dict:
        """Freeze the exact PDF bytes, their hash and the report manifest in one transaction.

        The outbound row, media blob and manifest commit together or not at all, so a restart can
        never find a manifest without its bytes, or deliverable bytes without a manifest.
        """
        pdf = bytes(pdf)
        digest = hashlib.sha256(pdf).hexdigest()
        if digest != sha256 or not pdf.startswith(b"%PDF-") or b"%%EOF" not in pdf[-1100:]:
            raise ChannelError("outbound_conflict", "Report integrity check failed.", 409)
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,120}", report_id) or not isinstance(page_count, int) or page_count < 1:
            raise ChannelError("outbound_invalid", "A stable report identifier is required.", 422)
        recipient = hashlib.sha256(sender.encode()).hexdigest()
        kind = "document:" + report_id + "_pdf"
        manifest = {
            "format": "pdf",
            "mime": "application/pdf",
            "filename": f"daybreak-raport-{report_id[:60]}-{digest[:8]}.pdf",
            "sha256": digest,
            "bytes": len(pdf),
            "page_count": page_count,
            "source_pages": source_pages if source_pages is not None else page_count,
            "report_id": report_id,
            "plan_version": version,
            "part_kind": kind,
        }
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute("SELECT * FROM outbound_reports WHERE event_id=?", (eid,)).fetchone()
            if previous:
                if (
                    previous["report_id"] != report_id
                    or previous["plan_version"] != version
                    or previous["format"] != "pdf"
                    or not previous["manifest"]
                ):
                    raise ChannelError("outbound_conflict", "The report source changed.", 409)
                return json.loads(previous["manifest"])
            part = hashlib.sha256((eid + ":" + kind).encode()).hexdigest()
            db.execute(
                "INSERT INTO outbound(part_id,event_id,destination,recipient_hash,kind,payload_hash,state,updated) VALUES(?,?,?,?,?,?,'prepared',?)",
                (part, eid, destination, recipient, kind, digest, time.time()),
            )
            db.execute("INSERT INTO outbound_media VALUES(?,?)", (part, pdf))
            db.execute(
                "INSERT INTO outbound_reports(event_id,report_id,plan_version,page_count,case_versions,format,manifest) "
                "VALUES(?,?,?,?,?,'pdf',?)",
                (eid, report_id, version, page_count, json.dumps(case_versions or {}), json.dumps(manifest)),
            )
        return manifest

    def report_manifest(self, eid: str) -> dict | None:
        with self.connect() as db:
            row = db.execute("SELECT manifest FROM outbound_reports WHERE event_id=?", (eid,)).fetchone()
        return json.loads(row[0]) if row and row[0] else None

    def prepared_documents(self, eid: str) -> list[dict]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT o.*,m.payload FROM outbound o JOIN outbound_media m USING(part_id) "
                "WHERE event_id=? AND kind LIKE 'document:%' ORDER BY kind",
                (eid,),
            ).fetchall()
        return [dict(row) for row in rows]

    def report_cases(self, eid: str) -> dict:
        with self.connect() as db:
            row = db.execute("SELECT case_versions FROM outbound_reports WHERE event_id=?", (eid,)).fetchone()
        return json.loads(row[0]) if row else {}

    def report_version(self, eid: str) -> str | None:
        with self.connect() as db:
            row = db.execute("SELECT plan_version FROM outbound_reports WHERE event_id=?", (eid,)).fetchone()
        return row[0] if row else None

    def prepared_images(self, eid: str) -> list[dict]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT o.*,m.payload FROM outbound o JOIN outbound_media m USING(part_id) "
                "WHERE event_id=? AND kind LIKE 'image:%' ORDER BY kind",
                (eid,),
            ).fetchall()
        return [dict(row) for row in rows]

    def outbound_state(self, part: str, state: str, *, media_id=None, message_id=None, code=None) -> str:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT state FROM outbound WHERE part_id=?", (part,)).fetchone()
            if row and row["state"] in {"failed", "cancelled"}:
                state = row["state"]
            if (
                row
                and row["state"] in {"accepted", "delivered", "read"}
                and state in {"prepared", "sending", "unknown", "rejected"}
            ):
                state = row["state"]
            if row and row["state"] in {"delivered", "read"} and state == "accepted":
                state = row["state"]
            db.execute(
                "UPDATE outbound SET state=?,updated=?,media_id=coalesce(?,media_id),provider_message_id=coalesce(?,provider_message_id),error_code=? WHERE part_id=?",
                (state, time.time(), media_id, message_id, code, part),
            )
        return state

    def has_unresolved_send(self, event_id: str) -> bool:
        with self.connect() as db:
            return (
                db.execute(
                    "SELECT 1 FROM outbound WHERE event_id=? AND state IN ('sending','unknown') LIMIT 1", (event_id,)
                ).fetchone()
                is not None
            )

    def skip_prepared_audio(self, event_id: str, code: str):
        # Only an audio part that has never started sending may be cancelled for text fallback.
        # Sending/unknown/accepted/failed parts keep their existing reconciliation semantics.
        with self.connect() as db:
            db.execute(
                "UPDATE outbound SET state='cancelled',updated=?,error_code=? WHERE event_id=? AND kind='audio' AND state='prepared'",
                (time.time(), code, event_id),
            )

    def begin_send(self, part: str) -> bool:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            updated = db.execute(
                "UPDATE outbound SET state='sending',updated=? WHERE part_id=? AND state='prepared'",
                (time.time(), part),
            )
            return updated.rowcount == 1

    def reconcile(self, destination: str, status: dict):
        # Correlation comes only from the HMAC-verified status event and must match the bound recipient.
        recipient = str(status.get("recipient_id", ""))
        message_id = status.get("id")
        opaque = status.get("biz_opaque_callback_data")
        state = status.get("status")
        if state not in {"sent", "delivered", "read", "failed", "played"} or not isinstance(message_id, str):
            return
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM outbound WHERE provider_message_id=? OR part_id=?",
                (message_id, opaque if isinstance(opaque, str) else ""),
            ).fetchone()
            if (
                not row
                or row["destination"] != destination
                or row["recipient_hash"] != hashlib.sha256(recipient.encode()).hexdigest()
            ):
                return
            mapped = {
                "sent": "accepted",
                "delivered": "delivered",
                "read": "read",
                "played": "read",
                "failed": "failed",
            }[state]
            rank = {
                "prepared": 0,
                "sending": 0,
                "unknown": 0,
                "rejected": 0,
                "accepted": 1,
                "delivered": 2,
                "read": 3,
                "failed": 4,
            }
            if row["state"] == "cancelled" or rank.get(row["state"], 0) > rank[mapped]:
                return
            db.execute(
                "UPDATE outbound SET state=?,provider_message_id=?,updated=? WHERE part_id=?",
                (mapped, message_id, time.time(), row["part_id"]),
            )
            queue = db.execute("SELECT state FROM inbound_queue WHERE event_id=?", (row["event_id"],)).fetchone()
            if queue and queue[0] == "needs_reconciliation":
                self._record_delivery(db, row["event_id"])

    def counts(self) -> dict:
        with self.connect() as db:
            result = {
                table: {r[0]: r[1] for r in db.execute(f"SELECT state,count(*) FROM {table} GROUP BY state")}
                for table in ("inbound_queue", "outbound")
            }
            result["error_codes"] = {
                table: {
                    r[0]: r[1]
                    for r in db.execute(
                        f"SELECT error_code,count(*) FROM {table} WHERE error_code IS NOT NULL GROUP BY error_code"
                    )
                }
                for table in ("inbound_queue", "outbound")
            }
            return result
