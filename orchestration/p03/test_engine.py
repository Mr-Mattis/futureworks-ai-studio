"""P03.01–P03.08 isolated integration, durability and fail-closed tests."""
from __future__ import annotations

import concurrent.futures
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from engine import AUTH, GATES, REPO, ROLES, Rejected, STAGE_DEPENDENCIES, Studio
from model import ReplayModel

MANIFEST = REPO / "contracts/production-manifest/v1.0.0/example.valid.json"
EP = REPO / "agents/executive_producer/reconciliation/execution-54.json"
PLAN = json.loads(EP.read_text())["handoff"]["candidate"]
PROJECT = "FWAI-EP-0001"
RUN = "P03-CONTROLLED-RUN-001"
BRIEF = "The PC That Became a Robot — clearly fictional AI_CONCEPT."
STAGES = ("research", "script", "visual", "avatar", "budget", "assembly", "qc")


def concurrent_claim(args):
    path, project, run, stage = args
    return Studio(path).claim(project, run, stage)


def concurrent_submit(args):
    path, project_run = args
    return Studio(path).submit(MANIFEST, PLAN, project_run, BRIEF)


class OrchestrationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / "p03-dev.sqlite3"
        self.studio = Studio(self.path)

    def submit(self, run=RUN, brief=BRIEF):
        return self.studio.submit(MANIFEST, PLAN, run, brief)

    def test_submit_seven_stages_and_three_pending_gates(self):
        a = self.submit()
        self.assertEqual(a["action"], "created")
        report = self.studio.dashboard(PROJECT, RUN)
        self.assertEqual(report["state"], "planning")
        self.assertEqual(len(report["stages"]), 7)
        self.assertEqual({g["name"] for g in report["approvals"]}, set(GATES))
        self.assertEqual({g["status"] for g in report["approvals"]}, {"pending"})
        self.assertEqual(report["authorization"], AUTH)
        self.assertEqual(report["costs_usd"], 0)
        self.assertFalse(report["dispatch_performed"])

    def test_replay_identity_and_conflicting_brief(self):
        self.submit()
        self.assertEqual(self.submit()["action"], "replay_skipped")
        with self.assertRaisesRegex(Rejected, "IDEMPOTENCY_CONFLICT"):
            self.submit(brief="The PC That Became a Robot - changed and untrusted concept.")
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM runs").fetchone()[0], 1)

    def test_same_revision_across_independent_runs(self):
        self.submit()
        self.assertEqual(self.submit(run="P03-CONTROLLED-RUN-002")["action"], "created")
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM revisions").fetchone()[0], 1)

    def test_missing_and_wrong_manifest_rejected(self):
        with self.assertRaises((Rejected, ValueError)):
            self.studio.submit(REPO / "not-an-existing-manifest.json", PLAN, RUN, BRIEF)
        with self.assertRaises((Rejected, ValueError)):
            self.studio.submit(MANIFEST, dict(PLAN, project_id="OTHER-PROJECT"), RUN, BRIEF)

    def test_rejects_empty_and_unrelated_brief(self):
        with self.assertRaises(Rejected):
            self.submit(brief="short")
        with self.assertRaises(Rejected):
            self.submit(brief="An unrelated theme with no canonical project reference.")

    def test_unready_stage_not_claimable(self):
        self.submit()
        self.assertIsNone(self.studio.claim(PROJECT, RUN, "qc"))
        self.assertEqual(self.studio.ready_stages(PROJECT, RUN), ["research"])

    def test_research_claim_has_one_owner_across_twelve_processes(self):
        self.submit()
        with concurrent.futures.ProcessPoolExecutor(max_workers=12) as pool:
            result = list(pool.map(concurrent_claim, [
                (self.path, PROJECT, RUN, "research")] * 12))
        self.assertEqual(sum(x is not None for x in result), 1)
        report = self.studio.dashboard(PROJECT, RUN)
        self.assertEqual(report["stages"][0]["attempt"], 1)

    def test_replay_will_not_recreate_work(self):
        self.submit()
        ticket = self.studio.claim(PROJECT, RUN, "research")
        self.assertEqual(self.submit()["action"], "replay_skipped")
        self.assertIsNone(self.studio.claim(PROJECT, RUN, "research"))
        self.studio.recover(ticket)
        self.assertIsNotNone(self.studio.claim(PROJECT, RUN, "research"))

    def test_complete_stale_token_rejected(self):
        self.submit()
        t = self.studio.claim(PROJECT, RUN, "research")
        with self.assertRaisesRegex(Rejected, "STALE_OWNERSHIP"):
            self.studio.complete(dict(t, token="wrong"), ReplayModel()("research_agent", self.studio.context(t)))
        self.studio.recover(t)
        with self.assertRaisesRegex(Rejected, "STALE_OWNERSHIP"):
            self.studio.complete(t, ReplayModel()("research_agent", self.studio.context(t)))

    def test_recover_fenced_and_bounded(self):
        self.submit()
        ticket = self.studio.claim(PROJECT, RUN, "research")
        self.assertEqual(self.studio.recover(ticket), "queued")
        with self.assertRaisesRegex(Rejected, "STALE_OWNERSHIP"):
            self.studio.recover(ticket)
        next_ticket = self.studio.claim(PROJECT, RUN, "research")
        with self.assertRaisesRegex(Rejected, "Recovery limit"):
            self.studio.recover(next_ticket)
        self.assertEqual(self.studio.dashboard(PROJECT, RUN)["stages"][0]["state"], "needs_review")

    def test_fail_local_retry_then_needs_review(self):
        self.submit()
        ticket = self.studio.claim(PROJECT, RUN, "research")
        self.assertEqual(self.studio.fail(ticket, "synthetic timeout"), "queued")
        ticket = self.studio.claim(PROJECT, RUN, "research")
        self.assertEqual(self.studio.fail(ticket, "second failure"), "needs_review")
        self.assertEqual(len(self.studio.dashboard(PROJECT, RUN)["issues"]), 2)
        self.assertEqual(self.studio.ready_stages(PROJECT, RUN), [])

    def test_ambiguous_failure_no_retry(self):
        self.submit()
        ticket = self.studio.claim(PROJECT, RUN, "research")
        self.assertEqual(self.studio.fail(ticket, "unknown provider outcome", ambiguous=True), "needs_review")
        self.assertEqual(self.studio.ready_stages(PROJECT, RUN), [])

    def test_all_seven_stages_automatically_complete_to_human_gate(self):
        self.submit()
        report = self.studio.drive(PROJECT, RUN, ReplayModel(), parallel=True)
        self.assertEqual(report["state"], "awaiting_approval")
        self.assertEqual([t["stage"] for t in report["stages"]], list(STAGES))
        self.assertTrue(all(t["state"] == "passed" for t in report["stages"]))
        self.assertEqual({g["status"] for g in report["approvals"]}, {"pending"})
        self.assertFalse(any(report["authorization"].values()))
        self.assertEqual(report["costs_usd"], 0)
        self.assertEqual(report["assets_ready"], 0)
        with sqlite3.connect(self.path) as db:
            stored = db.execute("SELECT stage,output_json FROM tasks WHERE project_id=? AND run_id=?",
                                (PROJECT, RUN)).fetchall()
            self.assertEqual(len(stored), 7)
            for _, value in stored:
                out = json.loads(value)
                self.assertEqual(out["execution"]["status"], "blocked")
                self.assertEqual(out["validation"]["status"], "passed")
                self.assertFalse(any(out["authorization"].values()))
        self.assertEqual(self.studio.ready_stages(PROJECT, RUN), [])

    def test_parallel_visual_avatar_is_independent(self):
        self.submit()
        self.studio._step(PROJECT, RUN, "research", ReplayModel())
        self.studio._step(PROJECT, RUN, "script", ReplayModel())
        self.assertEqual(set(self.studio.ready_stages(PROJECT, RUN)), {"visual", "avatar"})
        self.assertIsNone(self.studio.claim(PROJECT, RUN, "budget"))

    def test_bad_model_output_blocks_pipeline_and_records_issue(self):
        self.submit()
        def malicious(role, ctx):
            return {"project_id": ctx["project_id"], "spend_authorized": True}
        result = self.studio.drive(PROJECT, RUN, malicious)
        self.assertEqual(result["stages"][0]["state"], "queued")
        self.assertEqual(len(result["issues"]), 1)
        self.assertFalse(any(result["authorization"].values()))

    def test_p03_06_approval_fields_never_auto_granted(self):
        self.submit()
        result = self.studio.drive(PROJECT, RUN, ReplayModel())
        self.assertEqual(result["state"], "awaiting_approval")
        self.assertEqual(result["next_action"], "owner_review")
        with sqlite3.connect(self.path) as db:
            columns = [row[1] for row in db.execute("PRAGMA table_info(approval_gates)")]
            self.assertEqual(columns, ["project_id", "run_id", "name", "status"])
            self.assertEqual(db.execute("SELECT COUNT(*) FROM approval_gates WHERE status='pending'").fetchone()[0], 3)

    def test_p03_07_mock_reservation_and_poll_do_not_submit(self):
        self.submit()
        key = "MOCK-OP-000001"
        self.assertEqual(self.studio.reserve_mock(PROJECT, RUN, key), "reserved")
        self.assertEqual(self.studio.reserve_mock(PROJECT, RUN, key), "already_reserved")
        self.assertEqual(self.studio.poll_mock(key)["provider_submission_performed"], False)
        report = self.studio.dashboard(PROJECT, RUN)
        self.assertEqual(len(report["provider_jobs"]), 1)
        self.assertEqual(report["provider_jobs"][0]["state"], "not_submitted")
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM provider_queue").fetchone()[0], 1)

    def test_p03_07_async_mock_success_and_bounded_pending_queue(self):
        self.submit()
        self.studio.reserve_mock(PROJECT, RUN, "MOCK-SUCCESS-0001")
        self.assertEqual(self.studio.set_mock_receipt("MOCK-SUCCESS-0001", "success"),
                         "mock_polling")
        self.assertEqual(self.studio.poll_due_mock()[0]["state"], "mock_complete")
        self.assertEqual(self.studio.poll_due_mock(), [])
        self.studio.reserve_mock(PROJECT, RUN, "MOCK-PENDING-0001")
        self.studio.set_mock_receipt("MOCK-PENDING-0001", "pending")
        outcome = self.studio.poll_due_mock()
        self.assertEqual(outcome[0]["state"], "mock_polling")
        outcome = self.studio.poll_due_mock()
        self.assertEqual(outcome[0]["state"], "needs_review")
        self.assertEqual(outcome[0]["attempt"], 2)
        self.assertEqual(self.studio.poll_due_mock(), [])
        self.assertEqual(len(self.studio.dashboard(PROJECT, RUN)["issues"]), 1)

    def test_p03_07_unknown_mock_receipt_requires_review_without_retry(self):
        self.submit()
        self.studio.reserve_mock(PROJECT, RUN, "MOCK-UNKNOWN-0001")
        self.studio.set_mock_receipt("MOCK-UNKNOWN-0001", "unknown")
        result = self.studio.poll_due_mock()[0]
        self.assertEqual(result["attempt"], 1)
        self.assertEqual(result["state"], "needs_review")
        self.assertFalse(result["provider_submission_performed"])
        with self.assertRaisesRegex(Rejected, "finalized"):
            self.studio.set_mock_receipt("MOCK-UNKNOWN-0001", "success")

    def test_p03_07_poll_limit_and_invalid_simulation_rejected(self):
        self.submit()
        self.studio.reserve_mock(PROJECT, RUN, "MOCK-POLL-0001")
        with self.assertRaises(Rejected):
            self.studio.set_mock_receipt("MOCK-POLL-0001", "real_provider_success")
        with self.assertRaises(Rejected):
            self.studio.poll_due_mock(limit=0)

    def test_mock_collision_rejected(self):
        self.submit()
        self.submit("P03-CONTROLLED-RUN-002")
        self.studio.reserve_mock(PROJECT, RUN, "MOCK-OP-000001")
        with self.assertRaisesRegex(Rejected, "collision"):
            self.studio.reserve_mock(PROJECT, "P03-CONTROLLED-RUN-002", "MOCK-OP-000001")

    def test_provider_poll_unknown_fails_closed(self):
        with self.assertRaisesRegex(Rejected, "simulated"):
            self.studio.poll_mock("NONEXISTENT")

    def test_report_unknown_run_fails_closed(self):
        with self.assertRaises(Rejected):
            self.studio.dashboard(PROJECT, "UNKNOWN")

    def test_nothing_reaches_production_paths(self):
        self.submit()
        self.studio.drive(PROJECT, RUN, ReplayModel())
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM costs").fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM assets").fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM provider_queue").fetchone()[0], 0)

    def test_model_does_not_need_any_network_for_replay(self):
        self.submit()
        self.studio.drive(PROJECT, RUN, ReplayModel())
        self.assertEqual(self.studio.dashboard(PROJECT, RUN)["state"], "awaiting_approval")


if __name__ == "__main__":
    unittest.main(verbosity=2)
