"""Execute the exact nine persisted development Code-node validators offline.

Every Node VM receives only $input and a mocked upstream Code-node result.
No native tooling, network, filesystem, n8n credentials or provider clients
are exposed within the VM. Run only with the approved Bubblewrap test runner.
"""
from __future__ import annotations

import copy
import json
import subprocess
import unittest
from pathlib import Path

from role_validation import records
from test_role_validation import sample

HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE / "posthardening-workflows.redacted.json").read_text())
WORKFLOWS = {w["id"]: w for w in DATA["workflows"]}


def nodes(role):
    wf = WORKFLOWS[records()[role]["id"]] if role != "creative_director" else next(
        w for w in DATA["workflows"] if w["name"].endswith("P02.02 Creative Director"))
    return wf, {n["name"]: n for n in wf["nodes"]}


def vm(code, items, ctx=None):
    p = subprocess.run(
        ["/usr/bin/node", str(HERE / "check_wrapper.cjs")],
        input=json.dumps(dict(code=code, items=items, context=ctx)),
        capture_output=True, text=True, check=True, timeout=10)
    return json.loads(p.stdout)


def fixture(role):
    wf, n = nodes(role)
    name = "Frozen creative fixture" if role == "creative_director" else "Manual role fixture"
    original = n[name]["parameters"]["jsCode"].strip()
    assert original.startswith("return [{json:") and original.endswith("}];")
    return json.loads(original[len("return [{json:"):-len("}];")])


def prepared(role):
    _, n = nodes(role)
    raw = fixture(role)
    result = vm(n["Prepare input"]["parameters"]["jsCode"], [raw])
    if not result["ok"]:
        raise AssertionError(f"Preparation {role} failed: {result}")
    return result["output"][0]["json"]


def validator(role, candidate, context=None):
    _, n = nodes(role)
    name = ("Validate candidate (no dispatch)" if role == "creative_director"
            else "Validate canonical proposal - no dispatch")
    return vm(n[name]["parameters"]["jsCode"],
              [{"output": candidate}], prepared(role) if context is None else context)


class N8nRoleSafetyTests(unittest.TestCase):
    def test_all_nine_workflows_are_manual_and_inactive(self):
        self.assertEqual(len(WORKFLOWS), 9)
        for role in records():
            with self.subTest(role=role):
                wf, n = nodes(role)
                self.assertFalse(wf["active"])
                self.assertEqual(len(n), 7 if role == "creative_director" else 8)
                self.assertNotIn("credentials", json.dumps(wf))
                self.assertFalse(any("httpRequest" in node["type"] or
                                     "dataTable" in node["type"] or
                                     "tool" in node["type"].lower() or
                                     "executeCommand" in node["type"] for node in n.values()))
                self.assertTrue(any("manualTrigger" in node["type"] for node in n.values()))
                if role != "creative_director":
                    self.assertTrue(n["Called by orchestrator"]["disabled"])
                    self.assertNotIn("Called by orchestrator", wf["connections"])

    def test_all_nine_frozen_inputs_and_valid_candidates(self):
        for role in records():
            with self.subTest(role=role):
                ctx = prepared(role)
                self.assertEqual(ctx["run_id"], fixture(role)["run_id"])
                result = validator(role, sample(role), ctx)
                self.assertTrue(result["ok"], result)
                handoff = result["output"][0]["json"]
                self.assertEqual(handoff["status"], "candidate_requires_canonical_validation")
                self.assertFalse(handoff["dispatch_performed"])
                self.assertFalse(any(handoff["authorization"].values()))
                self.assertTrue(handoff["blockers"])
                self.assertEqual(handoff["candidate"], sample(role))

    def test_all_nine_reject_extra_authorization_properties(self):
        for role in records():
            with self.subTest(role=role):
                model = sample(role)
                model["publish_authorized"] = True
                self.assertFalse(validator(role, model)["ok"])

    def test_all_nine_reject_field_omission(self):
        for role in records():
            with self.subTest(role=role):
                model = sample(role)
                model.pop(next(iter(model)))
                self.assertFalse(validator(role, model)["ok"])

    def test_all_nine_reject_changed_input_fixture(self):
        for role in records():
            with self.subTest(role=role):
                _, n = nodes(role)
                altered = fixture(role)
                altered["attempt"] += 1
                result = vm(n["Prepare input"]["parameters"]["jsCode"], [altered])
                self.assertFalse(result["ok"])

    def test_creative_short_narration_fails_closed(self):
        c = sample("creative_director")
        c["scenes"][0]["narration"] = "Brief mention."
        self.assertFalse(validator("creative_director", c)["ok"])

    def test_research_no_fake_verified_claims(self):
        c = sample("research_agent")
        c["verified_claims"] = ["40 percent improvement measured"]
        self.assertFalse(validator("research_agent", c)["ok"])

    def test_qc_without_media_cannot_pass(self):
        c = sample("quality_control")
        c["overall_verdict"] = "pass"
        self.assertFalse(validator("quality_control", c)["ok"])

    def test_sop_cannot_claim_approval(self):
        c = sample("sop_knowledge")
        c["owner_approval_required"] = False
        self.assertFalse(validator("sop_knowledge", c)["ok"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
