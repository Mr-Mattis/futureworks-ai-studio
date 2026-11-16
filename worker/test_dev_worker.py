"""P02.01 isolated worker integration tests; no provider or service calls."""
import concurrent.futures
import copy
import json
import multiprocessing
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from dev_worker import DevelopmentWorker, AUTHORIZATION, REPO, planner
from atomic_claim import reserve_provider_operation, Claim

MANIFEST = REPO / "contracts/production-manifest/v1.0.0/example.valid.json"
PLAN = REPO / "agents/executive_producer/tests/fixtures/plan.valid.json"
BARRIER = None


def init_race(barrier):
    global BARRIER
    BARRIER = barrier


def submit_racer(path):
    BARRIER.wait(timeout=30)
    return DevelopmentWorker(path).submit(MANIFEST, planner.read_json(PLAN), "race-run")



def submit_recorded_racer(path):
    BARRIER.wait(timeout=30)
    record = planner.read_json(REPO / "agents/executive_producer/reconciliation/execution-54.json")
    return DevelopmentWorker(path).submit(MANIFEST, record["handoff"]["candidate"], "live-54-race")

def drain_racer(path):
    BARRIER.wait(timeout=30)
    worker = DevelopmentWorker(path)
    ticket = worker.take()
    if ticket:
        worker.finish(ticket)
        return "processed"
    return "idle"


def die_after_submit(path):
    DevelopmentWorker(path).submit(MANIFEST, planner.read_json(PLAN), "crash-submit")
    os._exit(17)


def die_after_take(path, pipe):
    ticket = DevelopmentWorker(path).take()
    pipe.send(ticket)
    pipe.close()
    os._exit(18)


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "dev.sqlite3"
        self.worker = DevelopmentWorker(self.path)
        self.plan = planner.read_json(PLAN)

    def rows(self, table):
        with sqlite3.connect(self.path) as db:
            return db.execute("SELECT * FROM " + table).fetchall()

    def race(self, target):
        ctx = multiprocessing.get_context("spawn")
        barrier = ctx.Barrier(12)
        with concurrent.futures.ProcessPoolExecutor(
                max_workers=12, mp_context=ctx, initializer=init_race,
                initargs=(barrier,)) as pool:
            return list(pool.map(target, [self.path] * 12))

    def submit(self, run_id="run"):
        return self.worker.submit(MANIFEST, self.plan, run_id)

    def test_twelve_simultaneous_full_submissions_and_consumers(self):
        results = self.race(submit_racer)
        self.assertEqual(sum(r["action"] == "created" for r in results), 1)
        self.assertEqual(sum(r["action"] == "replay_skipped" for r in results), 11)
        self.assertEqual(len(self.rows("requests")), 1)
        self.assertEqual(len(self.rows("dev_jobs")), 1)
        self.assertEqual(self.race(drain_racer).count("processed"), 1)
        ops = self.rows("provider_reservations")
        self.assertEqual(len(ops), 25)  # 5 scenes x five required enabled media kinds
        self.assertTrue(all(r[3] == "not_submitted" for r in ops))
        self.assertEqual(self.worker.status("FWAI-EP-0001", "race-run")["state"], "blocked")

    def test_crash_after_submit_commit_has_durable_work_without_enqueue(self):
        ctx = multiprocessing.get_context("spawn")
        p = ctx.Process(target=die_after_submit, args=(self.path,))
        p.start()
        p.join(30)
        self.assertEqual(p.exitcode, 17)
        ticket = self.worker.take()
        self.assertEqual(ticket["run_id"], "crash-submit")
        result = self.worker.finish(ticket)
        self.assertEqual(result["authorization"], AUTHORIZATION)
        self.assertIsNone(self.worker.take())
        self.assertEqual(len(self.rows("requests")), 1)

    def test_crash_after_take_requires_explicit_fenced_recovery(self):
        self.submit()
        ctx = multiprocessing.get_context("spawn")
        receiver, sender = ctx.Pipe(duplex=False)
        p = ctx.Process(target=die_after_take, args=(self.path, sender))
        p.start()
        sender.close()
        self.assertTrue(receiver.poll(30))
        ticket = receiver.recv()
        receiver.close()
        p.join(30)
        self.assertEqual(p.exitcode, 18)
        self.assertIsNone(self.worker.take())  # no timed takeover
        self.worker.recover(ticket)
        with self.assertRaisesRegex(ValueError, "STALE_OWNERSHIP"):
            self.worker.recover(ticket)
        next_ticket = self.worker.take()
        with self.assertRaisesRegex(ValueError, "STALE_OWNERSHIP"):
            self.worker.finish(ticket)
        result = self.worker.finish(next_ticket)
        self.assertEqual(result["execution"]["attempt"], 2)
        self.assertEqual(len(self.rows("requests")), 1)
        self.assertEqual(len(self.rows("dev_jobs")), 1)
        self.assertEqual(self.submit()["action"], "replay_skipped")

    def test_manifest_revision_and_hash_conflicts_are_atomic(self):
        self.submit()
        from unittest.mock import patch
        original = planner.evaluate(MANIFEST, self.plan)
        for change in (dict(revision=2), dict(sha256="b" * 64)):
            candidate = copy.deepcopy(original)
            candidate["input_manifest"].update(change)
            with patch.object(planner, "evaluate", return_value=candidate):
                with self.assertRaises(ValueError):
                    self.submit()
        self.assertEqual(len(self.rows("requests")), 1)
        self.assertEqual(self.worker.status("FWAI-EP-0001", "run")["state"], "queued")

    def test_invalid_metadata_and_plan_do_not_create_jobs(self):
        for run_id in ("", None, False, "a"):
            with self.assertRaises(ValueError):
                self.submit(run_id)
        for mutation in (
                lambda p: p.update(project_id="wrong"),
                lambda p: p.update(authorization={"spend_authorized": True}),
                lambda p: p.update(estimated_scene_count=2),
                lambda p: p["work_packages"][0].update(dependencies=["qc"])):
            invalid = copy.deepcopy(self.plan)
            mutation(invalid)
            with self.assertRaises(ValueError):
                self.worker.submit(MANIFEST, invalid, "run")
        self.assertEqual(self.rows("requests"), [])
        self.assertEqual(self.rows("dev_jobs"), [])

    def test_missing_and_malformed_manifest_rejected(self):
        for path in (REPO / "missing.json",
                     REPO / "agents/executive_producer/tests/fixtures/duplicate-key.txt"):
            with self.assertRaises(ValueError):
                self.worker.submit(path, self.plan, "run")
        self.assertEqual(self.rows("requests"), [])

    def test_plan_conflict_rolls_back_and_preserves_original(self):
        self.submit()
        changed = copy.deepcopy(self.plan)
        changed["working_title"] += " changed"
        with self.assertRaisesRegex(ValueError, "PLAN_CONFLICT"):
            self.worker.submit(MANIFEST, changed, "run")
        stored = self.rows("dev_jobs")[0]
        self.assertEqual(json.loads(stored[3]), self.plan)
        self.assertEqual(len(self.rows("requests")), 1)

    def test_uncertain_provider_operation_blocks_all_replay_and_recovery(self):
        self.submit()
        ticket = self.worker.take()
        ref = planner.manifest_context(MANIFEST)[1]
        key = self.worker.operation_key("FWAI-EP-0001", "run", ref["revision"],
                                        ref["sha256"], "S01", "video", "runway")
        request = Claim("FWAI-EP-0001", "run", ref["revision"], ref["sha256"])
        reserve_provider_operation(self.path, request, key)
        self.worker.flag_ambiguous(key, "Injected timeout: reconcile before retry")
        self.assertEqual(self.submit()["state"], "needs_review")
        self.assertIsNone(self.worker.take())
        with self.assertRaises(ValueError):
            self.worker.recover(ticket)
        with self.assertRaises(ValueError):
            self.worker.finish(ticket)
        self.assertEqual(len(self.rows("provider_reservations")), 1)
        self.assertEqual(self.rows("provider_reservations")[0][3], "not_submitted")

    def test_ambiguity_injection_rejects_queued_or_completed_job(self):
        self.submit()
        ref = planner.manifest_context(MANIFEST)[1]
        key = self.worker.operation_key("FWAI-EP-0001", "run", ref["revision"],
                                        ref["sha256"], "S01", "video", "runway")
        reserve_provider_operation(
            self.path, Claim("FWAI-EP-0001", "run", ref["revision"], ref["sha256"]), key)
        with self.assertRaisesRegex(ValueError, "INVALID_RECONCILIATION_STATE"):
            self.worker.flag_ambiguous(key, "injected while queued")
        self.assertEqual(self.worker.status("FWAI-EP-0001", "run")["state"], "queued")
        self.worker.finish(self.worker.take())
        with self.assertRaisesRegex(ValueError, "INVALID_RECONCILIATION_STATE"):
            self.worker.flag_ambiguous(key, "injected after completed planning")
        self.assertEqual(self.worker.status("FWAI-EP-0001", "run")["state"], "blocked")
        self.assertEqual(self.rows("dev_operation_reviews"), [])

    def test_failed_completion_rolls_back_reservations(self):
        self.submit()
        ticket = self.worker.take()
        with self.worker.transaction() as db:
            raw = json.loads(db.execute("SELECT result_json FROM dev_jobs").fetchone()[0])
            raw["authorization"]["spend_authorized"] = True
            db.execute("UPDATE dev_jobs SET result_json=?", (json.dumps(raw),))
        with self.assertRaisesRegex(ValueError, "CORRUPT_HANDOFF"):
            self.worker.finish(ticket)
        self.assertEqual(self.rows("provider_reservations"), [])
        self.assertEqual(self.worker.status("FWAI-EP-0001", "run")["state"], "running")

    def test_distinct_run_ids_remain_distinct_and_reservations_unique(self):
        self.submit("run-a")
        self.submit("run-b")
        results = []
        while ticket := self.worker.take():
            results.append(self.worker.finish(ticket))
        self.assertEqual(len(results), 2)
        self.assertEqual(len(self.rows("provider_reservations")), 50)
        self.assertEqual(len({r[0] for r in self.rows("provider_reservations")}), 50)
        for result in results:
            self.assertEqual(result["authorization"], AUTHORIZATION)
            self.assertEqual(result["execution"]["status"], "blocked")
            self.assertTrue(result["blockers"])

    def test_cli_submit_drain_and_duplicate(self):
        base = [sys.executable, "-B", str(REPO / "worker/dev_worker.py"),
                "--database", str(self.path)]
        submit = base + ["submit", "--manifest", str(MANIFEST), "--plan", str(PLAN),
                         "--run-id", "cli"]
        first = subprocess.run(submit, capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(first.stdout)["action"], "created")
        subprocess.run(base + ["drain-one"], capture_output=True, text=True, check=True)
        replay = subprocess.run(submit, capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(replay.stdout)["action"], "replay_skipped")
        self.assertEqual(len(self.rows("provider_reservations")), 25)

    def test_isolation_has_no_production_credentials_or_network(self):
        self.assertFalse(Path("/data").exists())
        self.assertFalse(Path("/home/mattis983").exists())
        self.assertFalse(Path("/var/run/docker.sock").exists())
        self.assertEqual(os.listdir("/sys/class/net") if Path("/sys/class/net").exists() else [], [])
        self.assertFalse(any("API_KEY" in k or "SECRET" in k for k in os.environ))
        with socket.socket() as connection:
            connection.settimeout(0.1)
            self.assertNotEqual(connection.connect_ex(("127.0.0.1", 5678)), 0)


    def test_claim_and_work_intent_rollback_together(self):
        with self.worker.transaction() as db:
            db.execute("CREATE TRIGGER inject_crash BEFORE INSERT ON dev_jobs "
                       "BEGIN SELECT RAISE(ABORT, 'injected failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.submit()
        self.assertEqual(self.rows("requests"), [])
        self.assertEqual(self.rows("dev_jobs"), [])

    def test_revision_bytes_cannot_change_under_a_different_run_id(self):
        self.submit()
        import hashlib
        from unittest.mock import patch
        changed_bytes = MANIFEST.read_bytes() + b"\n"
        changed_file = Path(self.temp.name) / "same-revision.json"
        changed_file.write_bytes(changed_bytes)
        result = planner.evaluate(MANIFEST, self.plan)
        result["input_manifest"]["sha256"] = hashlib.sha256(changed_bytes).hexdigest()
        local_file = planner.local_file
        # Test-only address shim supplies a whitespace-only canonical fixture.
        # Canonical validation still runs on the actual changed bytes.
        def fixture_path(path):
            return changed_file if path == MANIFEST else local_file(path)
        with patch.object(planner, "evaluate", return_value=result), \
                patch.object(planner, "local_file", side_effect=fixture_path):
            with self.assertRaisesRegex(ValueError, "IMMUTABLE_REVISION_CONFLICT"):
                self.submit("different-run")
        self.assertEqual(len(self.rows("requests")), 1)
        self.assertEqual(len(self.rows("dev_manifest_revisions")), 1)

    def test_real_immutable_revision_conflict(self):
        manifest_dir = REPO / "contracts/revision-guard/v1.0.0"
        plan = copy.deepcopy(self.plan)
        plan["project_id"] = "FWAI-P0105-LIVE-TEST"
        self.worker.submit(manifest_dir / "example.revision-1.json", plan, "revision-run")
        with self.assertRaisesRegex(ValueError, "IDEMPOTENCY_CONFLICT"):
            self.worker.submit(manifest_dir / "example.revision-2.json", plan, "revision-run")
        self.assertEqual(len(self.rows("requests")), 1)
        self.assertEqual(len(self.rows("dev_jobs")), 1)

    def test_reservation_survives_recovery_without_duplicate(self):
        self.submit()
        ticket = self.worker.take()
        ref = planner.manifest_context(MANIFEST)[1]
        key = self.worker.operation_key("FWAI-EP-0001", "run", ref["revision"],
                                        ref["sha256"], "S01", "video", "runway")
        reserve_provider_operation(self.path,
            Claim("FWAI-EP-0001", "run", ref["revision"], ref["sha256"]), key)
        self.worker.recover(ticket)
        result = self.worker.finish(self.worker.take())
        self.assertEqual(result["execution"]["attempt"], 2)
        self.assertEqual(len(self.rows("provider_reservations")), 25)
        self.assertEqual(sum(r[0] == key for r in self.rows("provider_reservations")), 1)

    def test_actual_n8n_54_candidate_survives_concurrent_worker_handoff(self):
        record = planner.read_json(REPO / "agents/executive_producer/reconciliation/execution-54.json")
        handoff = record["handoff"]
        self.assertEqual(handoff["input_manifest"], planner.manifest_context(MANIFEST)[1])
        self.assertEqual(handoff["authorization"], AUTHORIZATION)
        self.assertEqual(handoff["status"], "candidate_requires_canonical_validation")
        self.assertFalse(handoff["dispatch_performed"])
        results = self.race(submit_recorded_racer)
        self.assertEqual(sum(r["action"] == "created" for r in results), 1)
        self.assertEqual(sum(r["action"] == "replay_skipped" for r in results), 11)
        self.assertEqual(self.race(drain_racer).count("processed"), 1)
        self.assertEqual(len(self.rows("dev_jobs")), 1)
        self.assertEqual(len(self.rows("provider_reservations")), 25)
        stored = json.loads(self.rows("dev_jobs")[0][4])
        self.assertEqual(stored["output"], handoff["candidate"])
        self.assertEqual(stored["execution"]["status"], "blocked")
        self.assertEqual(stored["authorization"], AUTHORIZATION)
        for blocker in handoff["candidate"]["blockers"]:
            self.assertIn(blocker, stored["blockers"])

    def test_production_storage_path_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Production storage"):
            DevelopmentWorker("/data/output/dev.sqlite3")


if __name__ == "__main__":
    unittest.main(verbosity=2)
