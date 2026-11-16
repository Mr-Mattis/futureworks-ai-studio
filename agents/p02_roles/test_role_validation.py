"""Synthetic role-policy tests; no model, network, production paths or writes."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import unittest

import role_validation as roles

MANIFEST = roles.REPO / "contracts/production-manifest/v1.0.0/example.valid.json"
REVISION = roles.REPO / "contracts/revision-guard/v1.0.0/example.revision-1.json"


def context(role):
    inventory = roles.records()[role]
    if inventory["fixture"]:
        return copy.deepcopy(inventory["fixture"])
    manifest = json.loads(MANIFEST.read_text())
    return {
        "scope": "episode", "project_id": manifest["project_id"],
        "input_manifest": {k: manifest[k] for k in ("schema_version", "project_id", "revision")} |
                          {"sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest()},
        "run_id": "p02-creative-director-test-001", "attempt": 1,
        "role_input": {"content_type": manifest["content_type"],
                       "target_duration_seconds": 360, "scene_ids": ["S01", "S02", "S03", "S04", "S05"]},
    }


def sample(role):
    ctx = context(role)
    item = {}
    for key in roles.schema(role)["required"]:
        rule = roles.schema(role)["properties"][key]
        kind = rule.get("type", "string")
        if key == "project_id":
            item[key] = ctx["project_id"]
        elif key == "currency":
            item[key] = "USD"
        elif key == "content_type":
            item[key] = ctx["role_input"]["content_type"]
        elif key == "overall_verdict":
            item[key] = "needs_review"
        elif key == "target_duration_seconds":
            item[key] = 360
        elif key in ("manual_review_required", "approval_required", "owner_approval_required"):
            item[key] = True
        elif key == "scenes":
            item[key] = [
                {"scene_id": "S" + str(i).zfill(2), "duration_seconds": 72,
                 "description": "One original fictional computer concept scene.",
                 "narration": "Original, clearly fictional script narration.",
                 "visual_intent": "An original computer concept, not recorded reality."}
                for i in range(1, 6)
            ]
        elif key == "shots":
            item[key] = [{"scene_id": "S01", "shot_id": "SH01",
                          "positive_prompt": "Fictional art, not produced media."}]
        elif key in ("unverified_claims", "required_consents", "missing_assets",
                     "missing_rates", "data_gaps"):
            item[key] = ["Needs independent verification"]
        elif kind == "array":
            item[key] = []
        elif kind == "number":
            item[key] = 0.0
        elif kind == "integer":
            item[key] = 1
        elif kind == "boolean":
            item[key] = False
        elif kind == "object":
            item[key] = {}
        else:
            item[key] = "Pending owner review"
    return item


class RoleBoundaryTests(unittest.TestCase):
    def test_all_nine_roles_have_distinct_contracts_and_registry_entries(self):
        self.assertEqual(len(roles.records()), 9)
        self.assertEqual(len(roles.registry()), 10)
        self.assertEqual(len({r["checkpoint"] for r in roles.records().values()}), 9)
        self.assertTrue(all(r in roles.registry() for r in roles.records()))

    def test_synthetic_role_output_hardening_and_canonical_handoff(self):
        for role in roles.records():
            with self.subTest(role=role):
                ctx = context(role)
                proposal = sample(role)
                before = copy.deepcopy(proposal)
                checked = roles.checked_output(role, proposal, ctx)
                self.assertEqual(checked, before)
                result = roles.envelope(role, proposal, ctx, manifest_path=(
                    None if ctx["scope"] == "studio" else
                    MANIFEST if role == "creative_director" else REVISION))
                self.assertEqual(result["execution"]["status"], "blocked")
                self.assertEqual(result["validation"]["status"], "passed")
                self.assertTrue(result["blockers"])
                self.assertFalse(any(result["authorization"].values()))
                self.assertEqual(proposal, before)

    def test_rejects_model_authorization_injection_all_roles(self):
        for role in roles.records():
            with self.subTest(role=role):
                proposal = sample(role)
                proposal["spend_authorized"] = True
                with self.assertRaises(roles.Rejected):
                    roles.checked_output(role, proposal, context(role))

    def test_rejects_missing_required_field_all_roles(self):
        for role in roles.records():
            with self.subTest(role=role):
                proposal = sample(role)
                proposal.pop(next(iter(roles.schema(role)["required"])))
                with self.assertRaises(roles.Rejected):
                    roles.checked_output(role, proposal, context(role))

    def test_rejects_unverified_research_claims(self):
        c = sample("research_agent")
        c["verified_claims"] = [{"claim": "40% increase", "source_url": "fabricated"}]
        with self.assertRaisesRegex(roles.Rejected, "invented"):
            roles.checked_output("research_agent", c, context("research_agent"))

    def test_rejects_unmeasured_growth_patterns(self):
        c = sample("growth_strategist")
        c["observed_patterns"] = ["Fake impressions"]
        with self.assertRaisesRegex(roles.Rejected, "invented"):
            roles.checked_output("growth_strategist", c, context("growth_strategist"))

    def test_rejects_unapproved_sop(self):
        c = sample("sop_knowledge")
        c["owner_approval_required"] = False
        with self.assertRaises(roles.Rejected):
            roles.checked_output("sop_knowledge", c, context("sop_knowledge"))

    def test_rejects_unsourced_qc_pass(self):
        c = sample("quality_control")
        c["overall_verdict"] = "pass"
        with self.assertRaises(roles.Rejected):
            roles.checked_output("quality_control", c, context("quality_control"))

    def test_rejects_unapproved_budget(self):
        c = sample("budget_controller")
        c["approval_required"] = False
        with self.assertRaises(roles.Rejected):
            roles.checked_output("budget_controller", c, context("budget_controller"))

    def test_rejects_creative_identity_scene_tampering(self):
        c = sample("creative_director")
        c["scenes"][1]["scene_id"] = "S01"
        with self.assertRaises(roles.Rejected):
            roles.checked_output("creative_director", c, context("creative_director"))

    def test_rejects_manifest_byte_drift(self):
        c = context("creative_director")
        c["input_manifest"]["sha256"] = "b" * 64
        with self.assertRaisesRegex(roles.Rejected, "byte identity"):
            roles.envelope("creative_director", sample("creative_director"), c, manifest_path=MANIFEST)


if __name__ == "__main__":
    unittest.main(verbosity=2)
