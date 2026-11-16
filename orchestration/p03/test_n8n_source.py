"""Exact source-controlled n8n webhook/approval Code-node regressions.

Pin-free JS VM execution; no n8n execution, socket, credentials or paid tools.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from engine import REPO, Studio
from model import ReplayModel

HERE = Path(__file__).resolve().parent
SOURCE = (HERE / "workflow.inactive.sdk.js").read_text()
MATCHES = re.findall(r'jsCode:("(?:\\.|[^"\\])*")', SOURCE)
if len(MATCHES) != 2:
    raise AssertionError("Expected exact webhook and approval-gate Code nodes")
INTAKE_CODE, GATE_CODE = [json.loads(x) for x in MATCHES]
MANIFEST = REPO / "contracts/production-manifest/v1.0.0/example.valid.json"
PLAN = json.loads((REPO / "agents/executive_producer/reconciliation/execution-54.json"
                   ).read_text())["handoff"]["candidate"]
PROJECT, RUN = "FWAI-EP-0001", "P03-N8N-VM-001"
BRIEF = "The PC That Became a Robot — clearly fictional concept."
FROZEN = dict(
    project_id=PROJECT, run_id=RUN, brief=BRIEF,
    manifest_sha256=hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
)


def vm(code, items, context=None):
    process = subprocess.run(
        ["/usr/bin/node", str(HERE / "check_p03_wrapper.cjs")],
        input=json.dumps({"code": code, "items": items, "context": context}),
        text=True, capture_output=True, check=True, timeout=10)
    return json.loads(process.stdout)


class N8nSourceTests(unittest.TestCase):
    def test_exact_runtime_sdk_contract(self):
        self.assertIn("n8n-nodes-base.webhook", SOURCE)
        self.assertIn("Run seven development specialists", SOURCE)
        self.assertIn("Read stage dashboard", SOURCE)
        self.assertIn("Return blocked development dashboard", SOURCE)
        self.assertIn("__P03_DEV_API_TOKEN_INJECT_AT_RUNTIME__", SOURCE)
        self.assertIn("__P03_WEBHOOK_GATE_INJECT_AT_RUNTIME__", SOURCE)
        self.assertNotIn("RUNWAY_API_KEY", SOURCE)
        self.assertNotIn("ELEVENLABS_API_KEY", SOURCE)
        self.assertNotIn("youtubeUpload", SOURCE)
        self.assertNotIn("/data/output", SOURCE)

    def test_intake_frozen_identity_and_header_gate(self):
        raw = {"headers": {"x-fwai-dev-gate":
                           "__P03_WEBHOOK_GATE_INJECT_AT_RUNTIME__"},
               "body": dict(FROZEN)}
        out = vm(INTAKE_CODE, [raw])
        self.assertTrue(out["ok"], out)
        self.assertEqual(out["output"][0]["json"], FROZEN)
        for field, changed in (
            ("project_id", "OTHER"), ("manifest_sha256", "a" * 64),
            ("run_id", " "), ("brief", "no title")):
            with self.subTest(field=field):
                invalid = copy.deepcopy(raw)
                invalid["body"][field] = changed
                self.assertFalse(vm(INTAKE_CODE, [invalid])["ok"])
        missing_header = copy.deepcopy(raw)
        missing_header["headers"] = {}
        self.assertFalse(vm(INTAKE_CODE, [missing_header])["ok"])

    def test_intake_overposting_authorization_rejected(self):
        raw = {"headers": {"x-fwai-dev-gate":
                           "__P03_WEBHOOK_GATE_INJECT_AT_RUNTIME__"},
               "body": dict(FROZEN, publish_authorized=True)}
        self.assertFalse(vm(INTAKE_CODE, [raw])["ok"])

    def test_whole_pipeline_dashboard_approval_hold_in_node_vm(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        studio = Studio(Path(tmp.name) / "test.db")
        studio.submit(MANIFEST, PLAN, RUN, BRIEF)
        report = studio.drive(PROJECT, RUN, ReplayModel())
        out = vm(GATE_CODE, [report], dict(FROZEN))
        self.assertTrue(out["ok"], out)
        final = out["output"][0]["json"]
        self.assertEqual(final["status"], "awaiting_human_approval")
        self.assertEqual(final["dashboard"]["state"], "awaiting_approval")
        self.assertEqual(len(final["dashboard"]["stages"]), 7)
        self.assertFalse(any(final["authorization"].values()))
        self.assertFalse(final["dispatch_performed"])

    def test_final_gate_denies_approval_and_missing_stage(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        studio = Studio(Path(tmp.name) / "test.db")
        studio.submit(MANIFEST, PLAN, RUN, BRIEF)
        report = studio.drive(PROJECT, RUN, ReplayModel())
        for mutator in (
            lambda x: x["authorization"].update(spend_authorized=True),
            lambda x: x.update(costs_usd=1),
            lambda x: x.update(dispatch_performed=True),
            lambda x: x["approvals"][0].update(status="approved"),
            lambda x: x["stages"].pop(),
            lambda x: x["stages"][0].update(state="failed"),
            lambda x: x.update(state="generating"),
        ):
            invalid = copy.deepcopy(report)
            mutator(invalid)
            self.assertFalse(vm(GATE_CODE, [invalid], dict(FROZEN))["ok"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
