"""Deterministic SQLite integration tests for P02.01.07; stdlib only."""
import concurrent.futures
import sqlite3
import tempfile
import unittest
from pathlib import Path

from atomic_claim import Claim, claim, initialize, reserve_provider_operation

SHA = "a" * 64


def concurrent_request(args):
    path, request = args
    return claim(path, request)


class AtomicClaimTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "claims.sqlite3"
        initialize(self.path)
        self.request = Claim("TEST-PROJECT", "TEST-RUN", 1, SHA)

    def test_create_and_replay(self):
        self.assertEqual(claim(self.path, self.request)["action"], "created")
        self.assertEqual(claim(self.path, self.request)["action"], "replay_skipped")

    def test_many_simultaneous_processes_get_one_claim(self):
        with concurrent.futures.ProcessPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(concurrent_request, [(self.path, self.request)] * 12))
        self.assertEqual(sum(r["action"] == "created" for r in results), 1)
        self.assertEqual(sum(r["action"] == "replay_skipped" for r in results), 11)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM requests").fetchone()[0], 1)

    def test_interruption_recovery_and_replay(self):
        self.assertEqual(claim(self.path, self.request, interrupted=True)["status"], "interrupted")
        self.assertEqual(claim(self.path, self.request, interrupted=True),
                         {"action": "resumed", "status": "recovered", "attempt": 2})
        self.assertEqual(claim(self.path, self.request, interrupted=True),
                         {"action": "replay_skipped", "status": "recovered", "attempt": 2})

    def test_hash_conflict_does_not_overwrite(self):
        claim(self.path, self.request)
        with self.assertRaisesRegex(ValueError, "IDEMPOTENCY_CONFLICT"):
            claim(self.path, Claim("TEST-PROJECT", "TEST-RUN", 1, "b" * 64))
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT sha256 FROM requests").fetchone()[0], SHA)

    def test_revision_conflict(self):
        claim(self.path, self.request)
        with self.assertRaisesRegex(ValueError, "IDEMPOTENCY_CONFLICT"):
            claim(self.path, Claim("TEST-PROJECT", "TEST-RUN", 2, SHA))

    def test_invalid_metadata(self):
        for candidate in (
            Claim("", "TEST-RUN", 1, SHA),
            Claim("TEST-PROJECT", "", 1, SHA),
            Claim("TEST-PROJECT", "TEST-RUN", 0, SHA),
            Claim("TEST-PROJECT", "TEST-RUN", True, SHA),
            Claim("TEST-PROJECT", "TEST-RUN", 1, "not-a-sha256"),
        ):
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                claim(self.path, candidate)

    def test_provider_operation_is_only_reserved_once(self):
        claim(self.path, self.request)
        self.assertEqual(reserve_provider_operation(self.path, self.request, "provider-op-1"), "reserved")
        self.assertEqual(reserve_provider_operation(self.path, self.request, "provider-op-1"), "already_reserved")
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM provider_reservations").fetchone()[0], 1)

    def test_parallel_provider_reservations_stay_unique(self):
        claim(self.path, self.request)
        with concurrent.futures.ProcessPoolExecutor(max_workers=12) as pool:
            futures = [
                pool.submit(
                    reserve_provider_operation,
                    self.path,
                    self.request,
                    "provider-op-race",
                )
                for _ in range(12)
            ]
            outcomes = [future.result() for future in futures]
        self.assertEqual(outcomes.count("reserved"), 1)
        self.assertEqual(outcomes.count("already_reserved"), 11)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(
                db.execute("SELECT COUNT(*) FROM provider_reservations").fetchone()[0],
                1,
            )
            self.assertEqual(
                db.execute("SELECT state FROM provider_reservations").fetchone()[0],
                "not_submitted",
            )

    def test_provider_key_conflict(self):
        claim(self.path, self.request)
        other = Claim("OTHER-PROJECT", "OTHER-RUN", 1, SHA)
        claim(self.path, other)
        reserve_provider_operation(self.path, self.request, "provider-op-1")
        with self.assertRaisesRegex(ValueError, "OPERATION_KEY_CONFLICT"):
            reserve_provider_operation(self.path, other, "provider-op-1")

    def test_reservation_requires_matching_parent(self):
        claim(self.path, self.request)
        with self.assertRaisesRegex(ValueError, "INVALID_PARENT_MANIFEST"):
            reserve_provider_operation(self.path, Claim("TEST-PROJECT", "TEST-RUN", 2, SHA), "new-op")

    def test_no_paid_provider_submission_or_approval_capability(self):
        claim(self.path, self.request)
        reserve_provider_operation(self.path, self.request, "provider-op-1")
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT state FROM provider_reservations").fetchone()[0],
                             "not_submitted")
            columns = {x[1] for x in db.execute("PRAGMA table_info(requests)")}
        self.assertFalse({"spend_authorized", "publish_authorized"} & columns)


if __name__ == "__main__":
    unittest.main(verbosity=2)
