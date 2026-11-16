"""Networkless audit of the actual one-shot n8n transport Code nodes."""
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
SOURCE = (HERE / "workflow.one-shot-transport.sdk.js").read_text()
CODES = [json.loads(x) for x in re.findall(r'jsCode:("(?:\\.|[^"\\])*")', SOURCE)]
if len(CODES) != 2:
    raise AssertionError("Expected one-shot intake and final gate Code nodes")
INTAKE, GATE = CODES
MANIFEST = REPO / "contracts/production-manifest/v1.0.0/example.valid.json"
PLAN = json.loads((REPO / "agents/executive_producer/reconciliation/execution-54.json"
                   ).read_text())["handoff"]["candidate"]
BRIEF = "The PC That Became a Robot — clearly fictional concept."
FIXTURE = dict(project_id="FWAI-EP-0001",run_id="P03-DEV-N8N-ONE-SHOT-001",
               manifest_sha256=hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
               brief=BRIEF)


def run_node(code, items):
    input_data = dict(code=code, items=items, context=None)
    proc = subprocess.run(["/usr/bin/node", str(HERE / "check_p03_wrapper.cjs")],
                          input=json.dumps(input_data), capture_output=True,
                          text=True, check=True, timeout=10)
    return json.loads(proc.stdout)


class OneShotTransportTests(unittest.TestCase):
    def test_source_has_only_one_fixed_development_destination(self):
        self.assertIn("n8n-nodes-base.webhook", SOURCE)
        self.assertIn("http://host.docker.internal:18731/v1/demo-once", SOURCE)
        self.assertNotIn("__P03_DEV_API_TOKEN_INJECT_AT_RUNTIME__", SOURCE)
        self.assertNotIn("api.runwayml.com", SOURCE)
        self.assertNotIn("api.heygen.com", SOURCE)
        self.assertNotIn("youtubeUpload", SOURCE)

    def test_only_frozen_concept_can_enter_transport(self):
        raw = dict(headers={}, body=dict(FIXTURE))
        out = run_node(INTAKE, [raw])
        self.assertTrue(out["ok"], out)
        self.assertEqual(out["output"][0]["json"], FIXTURE)
        for value in (
            dict(FIXTURE, project_id="OTHER"),
            dict(FIXTURE, manifest_sha256="a" * 64),
            dict(FIXTURE, run_id="P03-NEW-ARBITRARY"),
            dict(FIXTURE, spend_authorized=True),
        ):
            self.assertFalse(run_node(INTAKE, [dict(headers={},body=value)])["ok"])

    def test_actual_seven_stage_synthetic_dashboard_passes_final_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            studio = Studio(Path(temp) / "test.db")
            studio.submit(MANIFEST, PLAN, FIXTURE["run_id"], BRIEF)
            report = studio.drive(FIXTURE["project_id"], FIXTURE["run_id"], ReplayModel())
            out = run_node(GATE, [dict(mode="one_shot_synthetic_replay",
                                       receipt={"action":"created"},dashboard=report)])
            self.assertTrue(out["ok"], out)
            result = out["output"][0]["json"]
            self.assertEqual(result["status"], "awaiting_human_approval")
            self.assertFalse(result["dispatch_performed"])
            self.assertEqual(result["mode"], "synthetic_replay_transport_only")

    def test_gate_rejects_fake_paid_permission_or_early_approval(self):
        with tempfile.TemporaryDirectory() as temp:
            studio = Studio(Path(temp) / "test.db")
            studio.submit(MANIFEST, PLAN, FIXTURE["run_id"], BRIEF)
            report = studio.drive(FIXTURE["project_id"], FIXTURE["run_id"], ReplayModel())
            for edit in (
                lambda x: x["approvals"][0].update(status="approved"),
                lambda x: x["authorization"].update(publish_authorized=True),
                lambda x: x.update(costs_usd=2),
                lambda x: x["stages"].pop(),
                lambda x: x.update(dispatch_performed=True),
            ):
                changed = copy.deepcopy(report)
                edit(changed)
                self.assertFalse(run_node(GATE, [
                    dict(mode="one_shot_synthetic_replay",
                         receipt={"action":"created"}, dashboard=changed)])["ok"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
