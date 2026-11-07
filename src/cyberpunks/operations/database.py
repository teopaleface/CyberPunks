"""SQLite comun tuturor rolurilor; nicio stare operațională în cookie sau memorie de proces."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS connections (
 connection_id TEXT PRIMARY KEY, organization_id TEXT NOT NULL, scenario TEXT NOT NULL, body TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cases (
 case_id TEXT PRIMARY KEY, organization_id TEXT NOT NULL, scenario TEXT NOT NULL,
 connection_id TEXT NOT NULL, requester_id TEXT NOT NULL, version INTEGER NOT NULL, body TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS proposals (
 proposal_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, organization_id TEXT NOT NULL, scenario TEXT NOT NULL,
 actor_signature TEXT NOT NULL, fingerprint TEXT NOT NULL, body TEXT NOT NULL, command_id TEXT,
 UNIQUE(user_id, organization_id, scenario, fingerprint)
);
CREATE TABLE IF NOT EXISTS commands (
 command_id TEXT PRIMARY KEY, proposal_id TEXT NOT NULL UNIQUE, user_id TEXT NOT NULL,
 organization_id TEXT NOT NULL, scenario TEXT NOT NULL, status TEXT NOT NULL, body TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
 event_id TEXT PRIMARY KEY, command_id TEXT NOT NULL, case_id TEXT, organization_id TEXT NOT NULL,
 scenario TEXT NOT NULL, body TEXT NOT NULL, UNIQUE(command_id, case_id)
);
CREATE TABLE IF NOT EXISTS command_recoveries (
 recovery_id TEXT PRIMARY KEY, command_id TEXT NOT NULL, organization_id TEXT NOT NULL,
 scenario TEXT NOT NULL, body TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript(SCHEMA)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA journal_mode=WAL")
        try:
            yield db
        finally:
            db.close()

    @contextmanager
    def transaction(self):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise
