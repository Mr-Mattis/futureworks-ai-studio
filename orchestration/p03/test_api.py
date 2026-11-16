"""P03 bridge tests with fake HTTP transports; no socket, network or secrets."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest

from api import MANIFEST, service
from engine import Rejected

TOKEN = "development-fixture-token-with-at-least-32-bytes"
PROJECT = "FWAI-EP-0001"
RUN = "P03-HTTP-TEST-001"
BRIEF = "The PC That Became a Robot — explicitly fictional and non-functional."


class ApiTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.handler = service(tmp.name + "/dev.db", TOKEN)
        self.manifest_sha = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()

    def call(self, method, path, payload=None, token=TOKEN):
        obj = object.__new__(self.handler)
        obj.path = path
        obj.headers = {"Authorization": "Bearer " + token}
        obj._send = lambda status, response: setattr(obj, "response", (status, response))
        if payload is not None:
            obj._read = lambda: copy.deepcopy(payload)
        getattr(obj, "do_" + method)()
        return obj.response

    def intake(self):
        return dict(project_id=PROJECT, run_id=RUN,
                    manifest_sha256=self.manifest_sha, brief=BRIEF)

    def test_unauthorized_request_cannot_intake_or_dashboard(self):
        self.assertEqual(self.call("POST", "/v1/intake", self.intake(),
                                   token="wrong")[0], 401)
        self.assertEqual(self.call("GET", "/v1/health", token="wrong")[0], 401)

    def test_weak_token_denied_even_before_server_binds(self):
        with self.assertRaises(Rejected):
            service("/tmp/mock-p03.db", "bad")

    def test_exact_manifest_intake_replay_and_conflict(self):
        status, first = self.call("POST", "/v1/intake", self.intake())
        self.assertEqual(status, 200)
        self.assertEqual(first["action"], "created")
        status, repeated = self.call("POST", "/v1/intake", self.intake())
        self.assertEqual(repeated["action"], "replay_skipped")
        modified = self.intake() | dict(brief=BRIEF + " Altered.")
        status, failed = self.call("POST", "/v1/intake", modified)
        self.assertEqual(status, 400)
        self.assertIn("IDEMPOTENCY_CONFLICT", failed["detail"])

    def test_wrong_hash_unknown_project_and_extra_fields_rejected(self):
        for extra in (
            dict(project_id="WRONG"),
            dict(manifest_sha256="1" * 64),
            dict(publish_authorized=True),
            dict(brief=""),
        ):
            request = self.intake() | extra
            with self.subTest(extra=extra):
                self.assertEqual(self.call("POST", "/v1/intake", request)[0], 400)

    def test_webhook_style_intake_drives_all_seven_stages_to_pending_gate(self):
        self.assertEqual(self.call("POST", "/v1/intake", self.intake())[0], 200)
        status, result = self.call("POST", "/v1/drive",
                                   dict(project_id=PROJECT, run_id=RUN))
        self.assertEqual(status, 200)
        self.assertEqual(result["state"], "awaiting_approval")
        self.assertEqual(len(result["stages"]), 7)
        self.assertTrue(all(t["state"] == "passed" for t in result["stages"]))
        self.assertEqual({g["status"] for g in result["approvals"]}, {"pending"})
        self.assertFalse(any(result["authorization"].values()))
        self.assertFalse(result["dispatch_performed"])

    def test_dashboard_reports_costs_assets_issues_and_gates(self):
        self.call("POST", "/v1/intake", self.intake())
        query = "?project_id=" + PROJECT + "&run_id=" + RUN
        status, report = self.call("GET", "/v1/dashboard" + query)
        self.assertEqual(status, 200)
        self.assertEqual(report["costs_usd"], 0)
        self.assertEqual(report["assets_ready"], 0)
        self.assertEqual(len(report["approvals"]), 3)
        self.assertEqual(report["issues"], [])

    def test_mock_provider_poll_never_submits(self):
        self.call("POST", "/v1/intake", self.intake())
        status, r = self.call("POST", "/v1/reserve-mock",
                              dict(project_id=PROJECT, run_id=RUN,
                                   operation_key="P03-MOCK-OP-0001"))
        self.assertEqual(status, 200)
        self.assertFalse(r["provider_submission_performed"])

    def test_health_explicitly_disables_production(self):
        status, result = self.call("GET", "/v1/health")
        self.assertEqual(status, 200)
        self.assertFalse(result["paid_provider_enabled"])
        self.assertFalse(result["publish_enabled"])
        self.assertFalse(result["production_enabled"])

    def test_external_provider_or_publish_paths_not_exposed(self):
        for path in ("/v1/publish", "/v1/approve", "/v1/provider-submit"):
            self.assertEqual(self.call("POST", path, {"approve": True})[0], 404)


if __name__ == "__main__":
    unittest.main(verbosity=2)
