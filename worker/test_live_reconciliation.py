"""Check the exact development n8n Code-node wrapper in a restricted Node VM."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agents/executive_producer"))
import planner

path = planner.HERE / "reconciliation/build_live_patch.py"
spec = importlib.util.spec_from_file_location("live_patch", path)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

VM = """
const vm=require('node:vm');
const fs=require('node:fs');
const {code,context,response}=JSON.parse(fs.readFileSync(0,'utf8'));
try {
  const sandbox={
    $: name=>({first:()=>({json:context})}),
    $input:{all:()=>[{json:response}]}
  };
  const out=vm.runInNewContext('(function(){'+code+'})()',sandbox,{timeout:1000});
  process.stdout.write(JSON.stringify({ok:true,out}));
} catch(error) { process.stdout.write(JSON.stringify({ok:false,error:String(error)})); }
"""


class LiveReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.params = builder.parameters()
        self.context = planner.build_request(
            planner.REPO / "contracts/production-manifest/v1.0.0/example.valid.json")
        self.context["planning_schema"] = planner.schema()
        self.plan = planner.read_json(planner.HERE / "tests/fixtures/plan.valid.json")

    def run_vm(self, code, response):
        p = subprocess.run(["/usr/bin/node", "-e", VM], input=json.dumps(dict(
            code=code, context=self.context, response=response)),
            text=True, capture_output=True, check=True)
        return json.loads(p.stdout)

    def test_real_wrapper_preserves_blockers_and_grants_no_authority(self):
        code = self.params["Validate and return agent_result"]["jsCode"]
        result = self.run_vm(code, {"output": self.plan})
        self.assertTrue(result["ok"], result)
        handoff = result["out"][0]["json"]
        self.assertEqual(handoff["candidate"], self.plan)
        self.assertEqual(handoff["status"], "candidate_requires_canonical_validation")
        self.assertFalse(any(handoff["authorization"].values()))
        self.assertFalse(handoff["dispatch_performed"])
        self.assertTrue(all(b in handoff["blockers"] for b in self.plan["blockers"]))

    def test_wrapper_rejects_dependency_gate_scene_and_authority_injection(self):
        code = self.params["Validate and return agent_result"]["jsCode"]
        for mutate in (
                lambda p: p["work_packages"][0].update(dependencies=["qc"]),
                lambda p: p["work_packages"][1].update(dependencies=[]),
                lambda p: p["gates"][0].update(owner="executive_producer"),
                lambda p: p.update(estimated_scene_count=4),
                lambda p: p.update(spend_authorized=True),
                lambda p: p.update(creative_constraints="legacy untyped string")):
            candidate = copy.deepcopy(self.plan)
            mutate(candidate)
            self.assertFalse(self.run_vm(code, {"output": candidate})["ok"])

    def test_preparation_rejects_changes_to_frozen_fixture(self):
        code = self.params["Prepare input"]["jsCode"]
        self.assertTrue(self.run_vm(code, self.context)["ok"])
        changed = copy.deepcopy(self.context)
        changed["authorization"]["spend_authorized"] = True
        self.assertFalse(self.run_vm(code, changed)["ok"])

    def test_patch_disables_dispatch_entry_and_has_no_credentials_or_activation(self):
        patch = builder.patch()
        self.assertEqual(patch["workflowId"], "HBvqaDLfhurpNLlu")
        self.assertTrue(all(op["type"] != "setNodeCredential" for op in patch["operations"]))
        self.assertTrue(all("credentials" not in op for op in patch["operations"]))
        self.assertTrue(any(op.get("nodeName") == "Called by orchestrator"
                            and op.get("disabled") is True for op in patch["operations"]))
        self.assertFalse(self.params["Structured Output Parser"]["autoFix"])
        self.assertEqual(self.params["Executive Producer Agent"]["needsFallback"], False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
