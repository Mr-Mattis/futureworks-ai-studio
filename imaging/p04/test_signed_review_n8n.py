"""P04 managed-credential and signed-review n8n gate source regressions."""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import unittest

HERE=Path(__file__).resolve().parent
SOURCE=(HERE/"workflow.signed-review-gate.sdk.js").read_text()
JS=[json.loads(x) for x in re.findall(r'jsCode:("(?:\\.|[^"\\])*")',SOURCE)]
if len(JS)!=2:
    raise RuntimeError("Expected two exact owner-review code guards")


def vm(code,values):
    r=subprocess.run(["/usr/bin/node",str(HERE/"check_n8n_wrapper.cjs")],
                     input=json.dumps({"code":code,"items":values}),
                     capture_output=True,text=True,check=True,timeout=10)
    return json.loads(r.stdout)


class SignedReviewWorkflowTests(unittest.TestCase):
    def test_credential_bound_disabled_and_disconnected(self):
        self.assertIn("httpTemplatedCustomAuth:newCredential",SOURCE)
        self.assertIn("disabled:true",SOURCE)
        self.assertNotIn("Bearer __P04_DEV_API_TOKEN",SOURCE)
        self.assertNotIn("RUNWAYML_API_SECRET",SOURCE)
        self.assertNotIn("youtubeUpload",SOURCE)
    def test_frozen_pending_manifest_is_preserved(self):
        result=vm(JS[0],[{}])
        self.assertTrue(result["ok"],result)
        self.assertEqual(result["result"][0]["json"]["approval_state"],"pending_review")
        self.assertFalse(result["result"][0]["json"]["rights_reviewed"])
        self.assertFalse(vm(JS[0],[{"approved":True}])["ok"])
    def test_owner_review_gate_blocks_pretend_approval(self):
        x=vm(JS[0],[{}])["result"][0]["json"]
        self.assertFalse(vm(JS[1],[x])["ok"])
        self.assertFalse(vm(JS[1],[x|{"approval_state":"approved"}])["ok"])
        self.assertFalse(vm(JS[1],[x|{"approval_state":"approved",
                                      "rights_reviewed":True}])["ok"])

if __name__=="__main__":
    unittest.main(verbosity=2)
