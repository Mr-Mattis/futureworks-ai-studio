"""Independent P04 owner-signoff regression suite, with no false approvals."""
from __future__ import annotations
import hashlib
import hmac
import json
from pathlib import Path
import tempfile
import unittest
from approval_gate import verify_approval
from imaging_gate_support import Rejected, canonical_bytes

MANIFEST=Path(__file__).resolve().parents[2]/"contracts/production-manifest/v1.0.0/example.valid.json"
KEY=b"this_is_only_a_synthetic_test_key_never_a_real_operator_secret"

class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.bundle=self.root/"images.json"
        self.approval=self.root/"review.json"
        self.assets=[{"sha256":hashlib.sha256(str(n).encode()).hexdigest()}
                     for n in range(10)]
        self.bundle.write_text(json.dumps({
            "project_id":"FWAI-EP-0001","run_id":"P04_SIGNED_FIXTURE",
            "status":"ready_for_visual_director","assets_count":10,
            "assets":self.assets}))
    def signed(self,**overrides):
        fields={"source":"owner_signed_gate","project_id":"FWAI-EP-0001",
                "run_id":"P04_SIGNED_FIXTURE",
                "manifest_sha256":hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
                "asset_sha256":sorted(x["sha256"] for x in self.assets),
                "decision":"approved","rights_reviewed":True,
                "image_quality_reviewed":True,"consistency_reviewed":True,
                "reviewer":"Synthetic test-only owner"}
        fields.update(overrides)
        fields["hmac_sha256"]=hmac.new(KEY,canonical_bytes(fields),hashlib.sha256).hexdigest()
        self.approval.write_text(json.dumps(fields))
    def test_unapproved_canonical_manifest_still_blocks_signed_test_review(self):
        self.signed()
        with self.assertRaisesRegex(Rejected,"manifest has not been separately approved"):
            verify_approval(self.approval,self.bundle,owner_key=KEY)
    def test_all_independent_approvals_required(self):
        for change in ({"image_quality_reviewed":False},
                       {"rights_reviewed":False},
                       {"consistency_reviewed":False},
                       {"decision":"pending"},
                       {"asset_sha256":["0"*64]*10}):
            with self.subTest(change=change):
                self.signed(**change)
                with self.assertRaises(Rejected):
                    verify_approval(self.approval,self.bundle,owner_key=KEY)
    def test_signature_tampering_rejected(self):
        self.signed()
        data=json.loads(self.approval.read_text())
        data["reviewer"]="Injected attacker"
        self.approval.write_text(json.dumps(data))
        with self.assertRaisesRegex(Rejected,"signature invalid"):
            verify_approval(self.approval,self.bundle,owner_key=KEY)
    def test_operator_secret_must_be_strong(self):
        self.signed()
        with self.assertRaisesRegex(Rejected,"Strong"):
            verify_approval(self.approval,self.bundle,owner_key=b"short")

if __name__=="__main__":
    unittest.main(verbosity=2)
