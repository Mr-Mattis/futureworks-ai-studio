"""P03 isolated master production orchestrator.

Implements P03.01–P03.08 in a development-only SQLite boundary. All agents
return *blocked planning proposals*. No paid tool, publishing, credentials,
production worker, or filesystem output path is imported.
"""
from __future__ import annotations

import concurrent.futures
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import time
import uuid

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / "agents/executive_producer"), str(REPO / "agents/p02_roles")]
import planner
import role_validation as roles

ROLES = dict(planner.STAGES)
STAGE_DEPENDENCIES = {
    "research": [], "script": ["research"], "visual": ["script"],
    "avatar": ["script"], "budget": ["visual", "avatar"],
    "assembly": ["visual", "avatar", "budget"], "qc": ["assembly"],
}
GATES = ("human_approval", "budget_approval", "publication_approval")
AUTH = dict(production_approved=False, spend_authorized=False, publish_authorized=False)
STATUS = ("queued", "running", "passed", "needs_review", "failed")
MAX_RETRIES = 2


def encoded(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)


def now():
    return datetime.now(timezone.utc).isoformat()


def uid(obj):
    return hashlib.sha256(encoded(obj).encode()).hexdigest()


class Rejected(ValueError):
    pass


class Studio:
    def __init__(self, database: str | Path):
        self.path = Path(database).resolve()
        if self.path.is_relative_to(Path("/data")) or self.path.is_relative_to(REPO):
            raise Rejected("P03 database must be outside production and source checkout")
        if self.path.exists() and self.path.is_symlink():
            raise Rejected("Symlink database prohibited")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.transaction() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS runs(
              project_id TEXT NOT NULL, run_id TEXT NOT NULL, revision INTEGER NOT NULL,
              manifest_sha TEXT NOT NULL, manifest_bytes BLOB NOT NULL,
              brief_hash TEXT NOT NULL, brief TEXT NOT NULL,
              plan_json TEXT NOT NULL, state TEXT NOT NULL,
              created_at TEXT NOT NULL, PRIMARY KEY(project_id,run_id)
            );
            CREATE TABLE IF NOT EXISTS revisions(
              project_id TEXT NOT NULL, revision INTEGER NOT NULL,
              manifest_sha TEXT NOT NULL, PRIMARY KEY(project_id,revision)
            );
            CREATE TABLE IF NOT EXISTS tasks(
              project_id TEXT NOT NULL, run_id TEXT NOT NULL,
              stage TEXT NOT NULL, role TEXT NOT NULL,
              dependencies_json TEXT NOT NULL,
              state TEXT NOT NULL, attempt INTEGER NOT NULL DEFAULT 0,
              token TEXT, output_json TEXT, error TEXT,
              PRIMARY KEY(project_id,run_id,stage),
              FOREIGN KEY(project_id,run_id) REFERENCES runs(project_id,run_id)
            );
            CREATE TABLE IF NOT EXISTS approval_gates(
              project_id TEXT NOT NULL, run_id TEXT NOT NULL,
              name TEXT NOT NULL, status TEXT NOT NULL CHECK(status='pending'),
              PRIMARY KEY(project_id,run_id,name),
              FOREIGN KEY(project_id,run_id) REFERENCES runs(project_id,run_id)
            );
            CREATE TABLE IF NOT EXISTS provider_queue(
              operation_key TEXT PRIMARY KEY, project_id TEXT NOT NULL,
              run_id TEXT NOT NULL, provider TEXT NOT NULL,
              state TEXT NOT NULL CHECK(state IN ('not_submitted','needs_review')),
              attempt INTEGER NOT NULL DEFAULT 0,
              receipt TEXT, next_poll_at TEXT,
              FOREIGN KEY(project_id,run_id) REFERENCES runs(project_id,run_id)
            );
            CREATE TABLE IF NOT EXISTS issues(
              issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
              project_id TEXT NOT NULL, run_id TEXT NOT NULL,
              stage TEXT NOT NULL, message TEXT NOT NULL, recorded_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS costs(
              project_id TEXT NOT NULL, run_id TEXT NOT NULL, amount_cents INTEGER
              NOT NULL CHECK(amount_cents=0), state TEXT NOT NULL CHECK(state='unspent')
            );
            CREATE TABLE IF NOT EXISTS assets(
              project_id TEXT NOT NULL, run_id TEXT NOT NULL, asset_id TEXT NOT NULL,
              state TEXT NOT NULL CHECK(state='not_generated')
            );
            """)

    def transaction(self):
        return _Transaction(self.path)

    @staticmethod
    def _key(project_id, run_id):
        if not isinstance(project_id, str) or not isinstance(run_id, str):
            raise Rejected("Missing run identity")
        if not (3 <= len(project_id) <= 80 and 3 <= len(run_id) <= 128):
            raise Rejected("Invalid run identity")
        if not all(ch.isalnum() or ch in "-_." for ch in project_id + run_id):
            raise Rejected("Invalid run identity")
        return project_id, run_id

    def submit(self, manifest_path, plan, run_id, brief):
        """P03.01–03: canonical project + immutable reference + 7-stage intent."""
        if not isinstance(brief, str) or not (10 <= len(brief.strip()) <= 4000):
            raise Rejected("Creative brief required (10–4000 characters)")
        manifest, ref = planner.manifest_context(manifest_path)
        self._key(ref["project_id"], run_id)
        checked_plan = planner.validate_plan(plan, manifest)
        if not isinstance(checked_plan, dict):
            raise Rejected("Invalid Executive Producer plan")
        raw = planner.local_file(manifest_path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != ref["sha256"]:
            raise Rejected("Manifest changed after canonical validation")
        if manifest["title"] not in brief and manifest["project_id"] not in brief:
            raise Rejected("Brief does not identify immutable test manifest")
        bh = uid(brief)
        by_stage = {p["stage"]: p for p in checked_plan["work_packages"]}
        with self.transaction() as db:
            prior_ref = db.execute(
                "SELECT manifest_sha FROM revisions WHERE project_id=? AND revision=?",
                (ref["project_id"], ref["revision"])).fetchone()
            if prior_ref and prior_ref["manifest_sha"] != ref["sha256"]:
                raise Rejected("IMMUTABLE_REVISION_CONFLICT")
            db.execute("INSERT OR IGNORE INTO revisions VALUES(?,?,?)",
                       (ref["project_id"], ref["revision"], ref["sha256"]))
            prior = db.execute("SELECT * FROM runs WHERE project_id=? AND run_id=?",
                               (ref["project_id"], run_id)).fetchone()
            if prior:
                if (prior["manifest_sha"], prior["brief_hash"], prior["plan_json"]) != (
                    ref["sha256"], bh, encoded(checked_plan)):
                    raise Rejected("IDEMPOTENCY_CONFLICT")
                return {"action": "replay_skipped", "state": prior["state"],
                        "project_id": ref["project_id"], "run_id": run_id}
            db.execute("INSERT INTO runs VALUES(?,?,?,?,?,?,?,?,?,?)",
                       (ref["project_id"], run_id, ref["revision"], ref["sha256"],
                        raw, bh, brief, encoded(checked_plan), "planning", now()))
            for stage, role in ROLES.items():
                deps = STAGE_DEPENDENCIES[stage]
                expected = by_stage[stage]
                actual_deps = {by_stage[d]["package_id"] for d in deps}
                if not actual_deps.issubset(set(expected["dependencies"])):
                    raise Rejected("Stage dependency mismatch")
                db.execute("INSERT INTO tasks(project_id,run_id,stage,role,dependencies_json,state)"
                           " VALUES(?,?,?,?,?,'queued')",
                           (ref["project_id"], run_id, stage, role, encoded(deps)))
            for gate in GATES:
                db.execute("INSERT INTO approval_gates VALUES(?,?,?,'pending')",
                           (ref["project_id"], run_id, gate))
            # No assets, costs or provider operations are created by planning.
            return {"action": "created", "state": "planning",
                    "project_id": ref["project_id"], "run_id": run_id}

    def ready_stages(self, project_id, run_id):
        self._key(project_id, run_id)
        with self.transaction() as db:
            tasks = db.execute("SELECT stage,state,dependencies_json FROM tasks "
                               "WHERE project_id=? AND run_id=?", (project_id, run_id)).fetchall()
            states = {row["stage"]: row["state"] for row in tasks}
            return [row["stage"] for row in tasks
                    if row["state"] == "queued"
                    and all(states.get(dep) == "passed"
                            for dep in json.loads(row["dependencies_json"]))]

    def claim(self, project_id, run_id, stage):
        """Cross-process fenced job lease; strictly one durable claimant."""
        if stage not in ROLES:
            raise Rejected("Unknown stage")
        with self.transaction() as db:
            row = db.execute(
                "SELECT state,attempt,dependencies_json FROM tasks "
                "WHERE project_id=? AND run_id=? AND stage=?",
                (project_id, run_id, stage)).fetchone()
            if row is None or row["state"] != "queued":
                return None
            for dep in json.loads(row["dependencies_json"]):
                previous = db.execute("SELECT state FROM tasks WHERE "
                                      "project_id=? AND run_id=? AND stage=?",
                                      (project_id, run_id, dep)).fetchone()
                if not previous or previous["state"] != "passed":
                    return None
            token = uuid.uuid4().hex
            db.execute("UPDATE tasks SET state='running',token=?,attempt=attempt+1 "
                       "WHERE project_id=? AND run_id=? AND stage=?",
                       (token, project_id, run_id, stage))
            return {"project_id": project_id, "run_id": run_id, "stage": stage,
                    "token": token, "attempt": row["attempt"] + 1}

    def context(self, ticket):
        with self.transaction() as db:
            row = db.execute("SELECT * FROM runs WHERE project_id=? AND run_id=?",
                             (ticket["project_id"], ticket["run_id"])).fetchone()
            if row is None:
                raise Rejected("Missing durable run")
            manifest = json.loads(row["manifest_bytes"])
            ref = dict(schema_version=manifest["schema_version"],
                       project_id=row["project_id"], revision=row["revision"],
                       sha256=row["manifest_sha"])
            stage = ticket["stage"]
            role = ROLES[stage]
            scenes = [s["scene_id"] for s in manifest["scenes"]]
            inp = {
                "project_id": row["project_id"], "content_type": manifest["content_type"],
                "brief": row["brief"], "scene_ids": scenes, "scenes": manifest["scenes"],
                "target_duration_seconds": manifest["target_duration_seconds"],
                "sources": [], "claims_to_check": [], "provider_rates": {},
                "budget_cap_usd": 0, "approved_asset_ids": [],
                "avatar_profile": None, "ffprobe_report": None,
                "video_metrics": None, "media_inspection": None,
                "paid_generation_authorized": False,
            }
            results = {}
            for t in db.execute("SELECT stage,output_json FROM tasks WHERE "
                                "project_id=? AND run_id=? AND state='passed'",
                                (row["project_id"], row["run_id"])):
                results[t["stage"]] = json.loads(t["output_json"])["output"]
            inp["dependencies"] = {d: results[d] for d in STAGE_DEPENDENCIES[stage]}
            return {
                "scope": "episode", "project_id": row["project_id"],
                "input_manifest": ref, "run_id": ticket["run_id"],
                "attempt": ticket["attempt"], "role_input": inp,
                "manifest": manifest, "manifest_bytes": row["manifest_bytes"],
                "role": role, "prior": results,
            }

    def complete(self, ticket, candidate):
        role = ROLES[ticket["stage"]]
        ctx = self.context(ticket)
        # Validate both role policy and immutable byte-pinned P01.02 handoff.
        output = roles.checked_output(role, candidate, ctx)
        # Frozen source immutable; verify raw bytes before final result.
        manifest_file = REPO / "contracts/production-manifest/v1.0.0/example.valid.json"
        if hashlib.sha256(manifest_file.read_bytes()).hexdigest() != ctx["input_manifest"]["sha256"]:
            raise Rejected("Only the approved development manifest is supported")
        result = roles.envelope(role, output, ctx, manifest_path=manifest_file)
        with self.transaction() as db:
            row = db.execute("SELECT state,token FROM tasks WHERE "
                             "project_id=? AND run_id=? AND stage=?",
                             (ticket["project_id"], ticket["run_id"], ticket["stage"])).fetchone()
            if row is None or row["state"] != "running" or row["token"] != ticket["token"]:
                raise Rejected("STALE_OWNERSHIP")
            db.execute("UPDATE tasks SET state='passed',output_json=?,token=NULL,error=NULL "
                       "WHERE project_id=? AND run_id=? AND stage=?",
                       (encoded(result), ticket["project_id"], ticket["run_id"],
                        ticket["stage"]))
            if db.execute("SELECT COUNT(*) FROM tasks WHERE project_id=? AND run_id=? "
                          "AND state='passed'",
                          (ticket["project_id"], ticket["run_id"])).fetchone()[0] == 7:
                db.execute("UPDATE runs SET state='awaiting_approval' "
                           "WHERE project_id=? AND run_id=?",
                           (ticket["project_id"], ticket["run_id"]))
            return result

    def fail(self, ticket, message, *, ambiguous=False):
        """Bounded local retries; uncertain external outcomes always fail closed."""
        with self.transaction() as db:
            row = db.execute("SELECT state,token,attempt FROM tasks WHERE project_id=? "
                             "AND run_id=? AND stage=?",
                             (ticket["project_id"], ticket["run_id"], ticket["stage"])).fetchone()
            if row is None or row["state"] != "running" or row["token"] != ticket["token"]:
                raise Rejected("STALE_OWNERSHIP")
            status = ("needs_review" if ambiguous or row["attempt"] >= MAX_RETRIES
                      else "queued")
            db.execute("UPDATE tasks SET state=?,token=NULL,error=? WHERE "
                       "project_id=? AND run_id=? AND stage=?",
                       (status, str(message)[:500], ticket["project_id"],
                        ticket["run_id"], ticket["stage"]))
            db.execute("INSERT INTO issues(project_id,run_id,stage,message,recorded_at)"
                       " VALUES(?,?,?,?,?)",
                       (ticket["project_id"], ticket["run_id"], ticket["stage"],
                        str(message)[:500], now()))
            if status == "needs_review":
                db.execute("UPDATE runs SET state='needs_review' WHERE "
                           "project_id=? AND run_id=?",
                           (ticket["project_id"], ticket["run_id"]))
            return status

    def recover(self, ticket):
        """Explicit operator recovery of no-provider local model work only."""
        with self.transaction() as db:
            row = db.execute("SELECT state,token,attempt FROM tasks WHERE project_id=? "
                             "AND run_id=? AND stage=?",
                             (ticket["project_id"], ticket["run_id"], ticket["stage"])).fetchone()
            if not row or row["state"] != "running" or row["token"] != ticket["token"]:
                raise Rejected("STALE_OWNERSHIP")
            if row["attempt"] >= MAX_RETRIES:
                db.execute("UPDATE tasks SET state='needs_review',token=NULL WHERE "
                           "project_id=? AND run_id=? AND stage=?",
                           (ticket["project_id"], ticket["run_id"], ticket["stage"]))
                db.execute("UPDATE runs SET state='needs_review' WHERE "
                           "project_id=? AND run_id=?",
                           (ticket["project_id"], ticket["run_id"]))
                outcome = "needs_review"
            else:
                db.execute("UPDATE tasks SET state='queued',token=NULL WHERE project_id=? "
                           "AND run_id=? AND stage=?",
                           (ticket["project_id"], ticket["run_id"], ticket["stage"]))
                outcome = "queued"
        if outcome == "needs_review":
            raise Rejected("Recovery limit reached; operator review required")
        return outcome

    def reserve_mock(self, project_id, run_id, key):
        """P03.07 zero-charge dry-run outbox; no real provider adapter."""
        self._key(project_id, run_id)
        if not isinstance(key, str) or len(key) < 8:
            raise Rejected("Invalid operation identity")
        with self.transaction() as db:
            if not db.execute("SELECT 1 FROM runs WHERE project_id=? AND run_id=?",
                              (project_id, run_id)).fetchone():
                raise Rejected("Unknown run")
            prior = db.execute("SELECT * FROM provider_queue WHERE operation_key=?",
                               (key,)).fetchone()
            if prior and (prior["project_id"], prior["run_id"]) != (project_id, run_id):
                raise Rejected("Provider operation key collision")
            db.execute("INSERT OR IGNORE INTO provider_queue(operation_key,project_id,"
                       "run_id,provider,state) VALUES(?,?,?,'mock','not_submitted')",
                       (key, project_id, run_id))
            return "already_reserved" if prior else "reserved"

    def poll_mock(self, operation_key):
        """Do not talk to any provider. Missing mock receipt needs human review."""
        with self.transaction() as db:
            row = db.execute("SELECT provider,state FROM provider_queue "
                             "WHERE operation_key=?", (operation_key,)).fetchone()
            if not row or row["provider"] != "mock":
                raise Rejected("Only simulated operations can be polled")
            return {"state": row["state"], "provider_submission_performed": False,
                    "next_action": "human_review_required"}

    def dashboard(self, project_id, run_id):
        self._key(project_id, run_id)
        with self.transaction() as db:
            run = db.execute("SELECT * FROM runs WHERE project_id=? AND run_id=?",
                             (project_id, run_id)).fetchone()
            if run is None:
                raise Rejected("Unknown run")
            tasks = db.execute("SELECT stage,role,state,attempt,error FROM tasks "
                               "WHERE project_id=? AND run_id=? ORDER BY rowid",
                               (project_id, run_id)).fetchall()
            gates = db.execute("SELECT name,status FROM approval_gates WHERE "
                               "project_id=? AND run_id=? ORDER BY name",
                               (project_id, run_id)).fetchall()
            providers = db.execute("SELECT operation_key,state,attempt FROM provider_queue "
                                   "WHERE project_id=? AND run_id=?",
                                   (project_id, run_id)).fetchall()
            issues = db.execute("SELECT stage,message FROM issues WHERE "
                                "project_id=? AND run_id=? ORDER BY issue_id",
                                (project_id, run_id)).fetchall()
            return {
                "project_id": project_id, "run_id": run_id, "revision": run["revision"],
                "manifest_sha256": run["manifest_sha"],
                "state": run["state"], "stages": [dict(t) for t in tasks],
                "approvals": [dict(g) for g in gates],
                "provider_jobs": [dict(p) for p in providers],
                "costs_usd": 0, "assets_ready": 0,
                "issues": [dict(x) for x in issues],
                "authorization": dict(AUTH),
                "dispatch_performed": False,
                "next_action": ("owner_review" if run["state"] == "awaiting_approval"
                                else "continue_isolated_planning"),
            }

    def drive(self, project_id, run_id, model, *, parallel=True):
        """P03.03–05: dependencies + parallel independent stages; stop at gate."""
        while (ready := self.ready_stages(project_id, run_id)):
            if parallel and len(ready) > 1:
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                    results = list(pool.map(lambda stage: self._step(
                        project_id, run_id, stage, model), ready))
            else:
                results = [self._step(project_id, run_id, stage, model)
                           for stage in ready]
            if not all(results):
                break
        return self.dashboard(project_id, run_id)

    def _step(self, project_id, run_id, stage, model):
        ticket = self.claim(project_id, run_id, stage)
        if ticket is None:
            return False
        try:
            context = self.context(ticket)
            candidate = model(ROLES[stage], copy.deepcopy(context))
            self.complete(ticket, candidate)
            return True
        except Exception as exc:
            self.fail(ticket, exc, ambiguous=False)
            return False


class _Transaction:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.db = sqlite3.connect(str(self.path), timeout=30, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA busy_timeout=30000")
        self.db.execute("BEGIN IMMEDIATE")
        return self.db

    def __exit__(self, typ, value, traceback):
        try:
            if typ:
                self.db.rollback()
            else:
                self.db.commit()
        finally:
            self.db.close()
        return False
