"""Offline acceptance over nine REAL Ollama outputs retained from n8n manual tests.

No provider services or live n8n access. Requires all nine successful blocked
candidate artifacts and revalidates each with canonical P01.02 contracts.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

import role_validation as roles

ROOT = Path(__file__).resolve().parent
RUNS = ROOT / "live-runs"
MANIFEST = roles.REPO / "contracts/production-manifest/v1.0.0/example.valid.json"
REVISION = roles.REPO / "contracts/revision-guard/v1.0.0/example.revision-1.json"


def expected_context(role):
    if role != "creative_director":
        return roles.records()[role]["fixture"]
    manifest = json.loads(MANIFEST.read_text())
    return {
        "scope": "episode", "project_id": manifest["project_id"],
        "input_manifest": {key: manifest[key] for key in
                           ("schema_version", "project_id", "revision")} |
                          {"sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest()},
        "run_id": "P0202-creative-director-dev-001", "attempt": 1,
        "role_input": {"content_type": manifest["content_type"]},
    }


class LiveRoleEvidenceTests(unittest.TestCase):
    def test_all_nine_verified_live_artifacts_and_canonical_handoffs(self):
        roles_seen = set()
        for role in roles.records():
            with self.subTest(role=role):
                path = RUNS / (role + ".json")
                self.assertTrue(path.is_file(), "Missing live acceptance artifact " + role)
                record = json.loads(path.read_text())
                self.assertEqual(record["role"], role)
                self.assertEqual(record["checkpoint"], roles.records()[role]["checkpoint"])
                self.assertEqual(record["model"], "qwen3.6:latest")
                h = record["handoff"]
                self.assertEqual(h["status"], "candidate_requires_canonical_validation")
                self.assertEqual(h["input_manifest"], expected_context(role)["input_manifest"])
                self.assertFalse(h["dispatch_performed"])
                self.assertFalse(any(h["authorization"].values()))
                self.assertTrue(h["blockers"])
                ctx = expected_context(role)
                output = roles.envelope(
                    role, h["candidate"], ctx,
                    manifest_path=None if ctx["scope"] == "studio" else
                    MANIFEST if role == "creative_director" else REVISION)
                self.assertEqual(output["agent"]["role"], role)
                self.assertEqual(output["execution"]["status"], "blocked")
                self.assertTrue(output["blockers"])
                self.assertFalse(any(output["authorization"].values()))
                roles_seen.add(role)
        self.assertEqual(roles_seen, set(roles.records()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
