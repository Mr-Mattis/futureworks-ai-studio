"""Isolated P02.01 development worker. No provider, rendering or publishing client.

Use only synthetic manifests and a dedicated local SQLite database. The legacy
worker and its image/compose do not import this module. Completion means a
validated planning handoff, never completed production or provider submission.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import uuid

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "agents/executive_producer"))
sys.path.insert(0, str(REPO / "agents/executive_producer/recovery"))
import planner
from atomic_claim import Claim, claim_in_transaction, initialize

AUTHORIZATION = dict(production_approved=False, spend_authorized=False, publish_authorized=False)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(encoded(value).encode()).hexdigest()


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    def reject(value):
        raise ValueError("Non-finite JSON number")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)


class DevelopmentWorker:
    def __init__(self, database):
        self.database = Path(database).resolve()
        # Explicit opt-in path; never defaults to legacy /data or home storage.
        if self.database.is_relative_to(Path("/data")):
            raise ValueError("Production storage is forbidden")
        initialize(self.database)
        with self.transaction() as db:
            schema = """
                CREATE TABLE IF NOT EXISTS dev_manifest_revisions (
                    project_id TEXT NOT NULL, revision INTEGER NOT NULL,
                    sha256 TEXT NOT NULL, manifest_bytes BLOB NOT NULL,
                    PRIMARY KEY(project_id,revision)
                );
                CREATE TABLE IF NOT EXISTS dev_jobs (
                    project_id TEXT NOT NULL, run_id TEXT NOT NULL,
                    manifest_bytes BLOB NOT NULL, plan_json TEXT NOT NULL,
                    result_json TEXT NOT NULL, payload_hash TEXT NOT NULL,
                    state TEXT NOT NULL CHECK(state IN
                        ('queued','running','blocked','needs_review')),
                    token TEXT,
                    PRIMARY KEY(project_id,run_id),
                    FOREIGN KEY(project_id,run_id) REFERENCES requests(project_id,run_id)
                );
                CREATE TABLE IF NOT EXISTS dev_operation_reviews (
                    operation_key TEXT PRIMARY KEY,
                    reason TEXT NOT NULL,
                    FOREIGN KEY(operation_key) REFERENCES provider_reservations(operation_key)
                );
            """
            for statement in schema.split(";"):
                if statement.strip():
                    db.execute(statement)

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA busy_timeout=30000")
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def validate_handoff(result, raw):
        canonical = planner.load_module(
            "dev_result_validation", planner.RESULT_DIR / "validate_agent_result.py")
        with tempfile.NamedTemporaryFile(suffix=".json") as frozen:
            frozen.write(raw)
            frozen.flush()
            errors = canonical.validate(result, frozen.name, planner.MANIFEST_DIR)
            if errors:
                raise ValueError("INVALID_CANONICAL_HANDOFF: " + "; ".join(errors))

    def submit(self, manifest_path, plan, run_id):
        # Canonical validation and a byte-for-byte frozen revision precede mutation.
        result = planner.evaluate(manifest_path, plan)
        raw = planner.local_file(manifest_path).read_bytes()
        ref = result["input_manifest"]
        if hashlib.sha256(raw).hexdigest() != ref["sha256"]:
            raise ValueError("MANIFEST_CHANGED_DURING_VALIDATION")
        manifest = strict_json(raw)
        if (manifest["project_id"], manifest["revision"]) != (ref["project_id"], ref["revision"]):
            raise ValueError("MANIFEST_IDENTITY_CONFLICT")
        request = Claim(ref["project_id"], run_id, ref["revision"], ref["sha256"])
        request.validate()
        plan_json = encoded(result["output"])
        payload_hash = digest([ref, result["output"]])
        # Persist the identity AND work intent in one transaction. No enqueue gap.
        result["execution"].update(run_id=run_id, attempt=1)
        self.validate_handoff(result, raw)
        with self.transaction() as db:
            revision = db.execute(
                "SELECT sha256 FROM dev_manifest_revisions WHERE project_id=? AND revision=?",
                (request.project_id, request.revision),
            ).fetchone()
            if revision is not None and revision["sha256"] != request.sha256:
                raise ValueError("IMMUTABLE_REVISION_CONFLICT")
            if revision is None:
                db.execute("INSERT INTO dev_manifest_revisions VALUES(?,?,?,?)",
                           (request.project_id, request.revision, request.sha256, raw))
            outcome = claim_in_transaction(db, request)
            prior = db.execute(
                "SELECT payload_hash,state FROM dev_jobs WHERE project_id=? AND run_id=?",
                (request.project_id, run_id),
            ).fetchone()
            if prior is not None:
                if prior["payload_hash"] != payload_hash:
                    raise ValueError("PLAN_CONFLICT")
            elif outcome["action"] != "created":
                # A proof-only claim cannot silently become an executable dev job.
                raise ValueError("CLAIM_WITHOUT_DURABLE_WORK")
            else:
                db.execute(
                    "INSERT INTO dev_jobs VALUES(?,?,?,?,?,?,'queued',NULL)",
                    (request.project_id, run_id, raw, plan_json, encoded(result), payload_hash),
                )
            return dict(action=outcome["action"], project_id=request.project_id,
                        run_id=run_id, state=prior["state"] if prior else "queued",
                        authorization=dict(AUTHORIZATION))

    def take(self):
        """Acquire one durable intent; no clock-based takeover of running work."""
        with self.transaction() as db:
            row = db.execute(
                "SELECT project_id,run_id FROM dev_jobs WHERE state='queued' "
                "ORDER BY project_id,run_id LIMIT 1"
            ).fetchone()
            if row is None:
                return None
            token = uuid.uuid4().hex
            db.execute(
                "UPDATE dev_jobs SET state='running',token=? WHERE project_id=? AND run_id=?",
                (token, row["project_id"], row["run_id"]),
            )
            return dict(row) | dict(token=token)

    @staticmethod
    def owned(db, ticket):
        row = db.execute(
            "SELECT * FROM dev_jobs WHERE project_id=? AND run_id=?",
            (ticket["project_id"], ticket["run_id"]),
        ).fetchone()
        if row is None or row["state"] != "running" or row["token"] != ticket["token"]:
            raise ValueError("STALE_OWNERSHIP")
        return row

    @staticmethod
    def operation_key(project_id, run_id, revision, sha256, scene_id, kind, provider):
        return digest([project_id, run_id, revision, sha256, scene_id, kind, provider])

    def finish(self, ticket):
        """Produce only a blocked planning handoff and unsubmitted reservations."""
        with self.transaction() as db:
            row = self.owned(db, ticket)
            request = db.execute(
                "SELECT * FROM requests WHERE project_id=? AND run_id=?",
                (ticket["project_id"], ticket["run_id"]),
            ).fetchone()
            if hashlib.sha256(row["manifest_bytes"]).hexdigest() != request["sha256"]:
                raise ValueError("CORRUPT_MANIFEST")
            manifest = strict_json(row["manifest_bytes"])
            plan = strict_json(row["plan_json"])
            reference = dict(schema_version=manifest["schema_version"],
                             project_id=manifest["project_id"], revision=manifest["revision"],
                             sha256=request["sha256"])
            if digest([reference, plan]) != row["payload_hash"]:
                raise ValueError("CORRUPT_WORK_INTENT")
            planner.verify_contracts()
            validator = planner.load_module(
                "dev_manifest_validation", planner.MANIFEST_DIR / "validate_manifest.py")
            if validator.validate(planner.read_json(
                    planner.MANIFEST_DIR / "production_manifest.schema.json"), manifest):
                raise ValueError("INVALID_STORED_MANIFEST")
            planner.validate_plan(plan, manifest)
            # Stable scene/provider/kind identity, not an arbitrary caller-supplied key.
            for scene in manifest["scenes"]:
                for kind, required in scene["media_requirements"].items():
                    config = manifest["generation_plan"][kind]
                    if not required or not config["enabled"]:
                        continue
                    key = self.operation_key(ticket["project_id"], ticket["run_id"],
                                             request["revision"], request["sha256"],
                                             scene["scene_id"], kind, config["provider"])
                    prior = db.execute(
                        "SELECT project_id,run_id FROM provider_reservations WHERE operation_key=?",
                        (key,),
                    ).fetchone()
                    if prior is not None and tuple(prior) != (ticket["project_id"], ticket["run_id"]):
                        raise ValueError("OPERATION_KEY_CONFLICT")
                    db.execute(
                        "INSERT OR IGNORE INTO provider_reservations"
                        "(operation_key,project_id,run_id) VALUES(?,?,?)",
                        (key, ticket["project_id"], ticket["run_id"]),
                    )
            if db.execute(
                "SELECT 1 FROM dev_operation_reviews r JOIN provider_reservations p "
                "USING(operation_key) WHERE p.project_id=? AND p.run_id=?",
                (ticket["project_id"], ticket["run_id"]),
            ).fetchone():
                raise ValueError("RECONCILIATION_REQUIRED")
            result = strict_json(row["result_json"])
            # Revalidate the frozen canonical envelope against the exact stored bytes.
            if (result["input_manifest"] != reference or result["output"] != plan
                    or result["execution"]["run_id"] != ticket["run_id"]
                    or result["execution"]["status"] != "blocked"
                    or result["authorization"] != AUTHORIZATION):
                raise ValueError("CORRUPT_HANDOFF")
            result["execution"]["attempt"] = request["attempt"]
            self.validate_handoff(result, row["manifest_bytes"])
            db.execute(
                "UPDATE dev_jobs SET result_json=? WHERE project_id=? AND run_id=?",
                (encoded(result), ticket["project_id"], ticket["run_id"]),
            )
            db.execute(
                "UPDATE dev_jobs SET state='blocked',token=NULL WHERE project_id=? AND run_id=?",
                (ticket["project_id"], ticket["run_id"]),
            )
            db.execute(
                "UPDATE requests SET status='completed' WHERE project_id=? AND run_id=?",
                (ticket["project_id"], ticket["run_id"]),
            )
            return result

    def recover(self, ticket):
        """Explicit zero-side-effect recovery, fenced by the previous owner token.

        Valid only for this no-provider development adapter. Never use this as
        permission to retry a real provider operation or to recover legacy jobs.
        """
        with self.transaction() as db:
            self.owned(db, ticket)
            if db.execute(
                "SELECT 1 FROM dev_operation_reviews r JOIN provider_reservations p "
                "USING(operation_key) WHERE p.project_id=? AND p.run_id=?",
                (ticket["project_id"], ticket["run_id"]),
            ).fetchone():
                raise ValueError("RECONCILIATION_REQUIRED")
            db.execute(
                "UPDATE dev_jobs SET state='queued',token=NULL WHERE project_id=? AND run_id=?",
                (ticket["project_id"], ticket["run_id"]),
            )
            db.execute(
                "UPDATE requests SET status='recovered',attempt=attempt+1 "
                "WHERE project_id=? AND run_id=?",
                (ticket["project_id"], ticket["run_id"]),
            )

    def flag_ambiguous(self, operation_key, reason):
        """Record a synthetic unknown outcome; there is deliberately no retry API."""
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("Reconciliation reason required")
        with self.transaction() as db:
            row = db.execute(
                "SELECT project_id,run_id FROM provider_reservations WHERE operation_key=?",
                (operation_key,),
            ).fetchone()
            if row is None:
                raise ValueError("UNKNOWN_OPERATION")
            parent = db.execute(
                "SELECT state FROM dev_jobs WHERE project_id=? AND run_id=?",
                tuple(row),
            ).fetchone()
            if parent is None or parent["state"] not in ("running", "needs_review"):
                raise ValueError("INVALID_RECONCILIATION_STATE")
            db.execute("INSERT OR IGNORE INTO dev_operation_reviews VALUES(?,?)",
                       (operation_key, reason))
            db.execute(
                "UPDATE dev_jobs SET state='needs_review',token=NULL "
                "WHERE project_id=? AND run_id=?", tuple(row),
            )
        # Reservations remain not_submitted: this adapter has never submitted.
        # A separate review flag represents injected uncertainty and blocks recovery.

    def status(self, project_id, run_id):
        with self.transaction() as db:
            row = db.execute(
                "SELECT state FROM dev_jobs WHERE project_id=? AND run_id=?",
                (project_id, run_id),
            ).fetchone()
            if row is None:
                raise ValueError("UNKNOWN_JOB")
            return dict(row) | dict(authorization=dict(AUTHORIZATION))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    submit = sub.add_parser("submit")
    submit.add_argument("--manifest", type=Path, required=True)
    submit.add_argument("--plan", type=Path, required=True)
    submit.add_argument("--run-id", required=True)
    sub.add_parser("drain-one")
    args = parser.parse_args()
    worker = DevelopmentWorker(args.database)
    try:
        if args.command == "submit":
            value = worker.submit(args.manifest, planner.read_json(args.plan), args.run_id)
        else:
            ticket = worker.take()
            value = worker.finish(ticket) if ticket else dict(state="idle")
        print(encoded(value))
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(encoded(dict(state="rejected", error=str(exc))))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
