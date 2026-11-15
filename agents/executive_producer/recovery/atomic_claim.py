"""P02.01.07 reference-only atomic request claims (not wired to production).

No paid/provider calls, network access, credentials, or n8n operations.
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Claim:
    project_id: str
    run_id: str
    revision: int
    sha256: str

    def validate(self) -> None:
        if not isinstance(self.project_id, str) or not self.project_id.strip():
            raise ValueError("Invalid project ID")
        if not isinstance(self.run_id, str) or not self.run_id.strip():
            raise ValueError("Invalid run ID")
        if type(self.revision) is not int or self.revision < 1:
            raise ValueError("Invalid manifest revision")
        if not isinstance(self.sha256, str) or re.fullmatch(r"[a-fA-F0-9]{64}", self.sha256) is None:
            raise ValueError("Invalid manifest SHA-256")


def _connect(path: Path | str) -> sqlite3.Connection:
    connection = sqlite3.connect(str(path), timeout=30, isolation_level=None)
    connection.execute("PRAGMA busy_timeout=30000")
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def initialize(path: Path | str) -> None:
    connection = _connect(path)
    try:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS requests (
            project_id TEXT NOT NULL,
            run_id TEXT NOT NULL,
            revision INTEGER NOT NULL CHECK(revision > 0),
            sha256 TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('interrupted','claimed','recovered','completed')),
            attempt INTEGER NOT NULL CHECK(attempt > 0),
            PRIMARY KEY(project_id, run_id)
        );
        CREATE TABLE IF NOT EXISTS provider_reservations (
            operation_key TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            run_id TEXT NOT NULL,
            state TEXT NOT NULL DEFAULT 'not_submitted' CHECK(state = 'not_submitted'),
            FOREIGN KEY(project_id,run_id) REFERENCES requests(project_id,run_id)
        );
        """)
    finally:
        connection.close()


def claim(path: Path | str, request: Claim, *, interrupted: bool = False) -> dict:
    """Atomically claim or replay a logical job. Caller must initialize storage first."""
    request.validate()
    connection = _connect(path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT revision,sha256,status,attempt FROM requests WHERE project_id=? AND run_id=?",
            (request.project_id, request.run_id),
        ).fetchone()
        if row is None:
            state = "interrupted" if interrupted else "claimed"
            connection.execute(
                "INSERT INTO requests(project_id,run_id,revision,sha256,status,attempt) "
                "VALUES(?,?,?,?,?,1)",
                (request.project_id, request.run_id, request.revision, request.sha256.lower(), state),
            )
            result = {"action": "created", "status": state, "attempt": 1}
        else:
            revision, sha256, state, attempt = row
            if revision != request.revision or sha256 != request.sha256.lower():
                raise ValueError("IDEMPOTENCY_CONFLICT")
            if interrupted and state == "interrupted":
                connection.execute(
                    "UPDATE requests SET status='recovered',attempt=attempt+1 "
                    "WHERE project_id=? AND run_id=? AND status='interrupted'",
                    (request.project_id, request.run_id),
                )
                result = {"action": "resumed", "status": "recovered", "attempt": attempt + 1}
            else:
                result = {"action": "replay_skipped", "status": state, "attempt": attempt}
        connection.commit()
        return result
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def reserve_provider_operation(path: Path | str, request: Claim, key: str) -> str:
    """Durably reserve a key; NEVER invokes a provider or implies approval."""
    request.validate()
    if not isinstance(key, str) or not key.strip():
        raise ValueError("Missing operation key")
    connection = _connect(path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        existing_request = connection.execute(
            "SELECT revision,sha256 FROM requests WHERE project_id=? AND run_id=?",
            (request.project_id, request.run_id),
        ).fetchone()
        if existing_request != (request.revision, request.sha256.lower()):
            raise ValueError("INVALID_PARENT_MANIFEST")
        prior = connection.execute(
            "SELECT project_id,run_id FROM provider_reservations WHERE operation_key=?",
            (key,),
        ).fetchone()
        if prior is None:
            connection.execute(
                "INSERT INTO provider_reservations(operation_key,project_id,run_id) VALUES(?,?,?)",
                (key, request.project_id, request.run_id),
            )
            outcome = "reserved"
        elif prior == (request.project_id, request.run_id):
            outcome = "already_reserved"
        else:
            raise ValueError("OPERATION_KEY_CONFLICT")
        connection.commit()
        return outcome
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()
