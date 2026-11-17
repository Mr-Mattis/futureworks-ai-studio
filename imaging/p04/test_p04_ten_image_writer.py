"""Offline contract/security tests for owner's local-only P04 ten-design writer.

No ComfyUI HTTP requests, no Windows subprocesses, no n8n execution.
"""
from __future__ import annotations
import importlib.util,hashlib,json,pathlib,tempfile,unittest
from unittest.mock import patch

HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("p04_ten_writer",HERE/"p04_ten_image_writer.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class BatchWriterContractTests(unittest.TestCase):
 def setUp(self):
    self.temp=tempfile.TemporaryDirectory()
    self.addCleanup(self.temp.cleanup)
    self.root=pathlib.Path(self.temp.name)
    for key,value in (("ROOT",self.root),("RECEIPT",self.root/"receipt.json"),("JOURNAL",self.root/"journal.json")):
        p=patch.object(module,key,value);p.start();self.addCleanup(p.stop)
 def test_scope_exactly_ten_and_local(self):
    self.assertEqual(module.ALLOWED,{"operation":"create_local_photoreal_10",
        "batch_id":"P04_V5_CIVILIAN_AI_001","image_count":10,
        "external_provider_calls_allowed":False,"publication_allowed":False})
 def test_absent_receipt_fails_to_submit(self):
    self.assertEqual(module.accepted(),{"status":"not_started","completed":0})
 def test_completes_only_hash_verified_images(self):
    module.RECEIPT.write_text(json.dumps({"scope":module.ALLOWED}))
    records={}
    for i in range(1,11):
        n=f"{i:02d}";data=(b"image-test-"+n.encode())*12
        (self.root/("FUT_"+n+"_1920x1080.png")).write_bytes(data)
        records[n]={"state":"complete","sha256":hashlib.sha256(data).hexdigest()}
    module.JOURNAL.write_text(json.dumps(records))
    p=module.accepted()
    self.assertEqual(p["status"],"completed_pending_owner_visual_review")
    self.assertEqual(p["completed"],10)
    self.assertFalse(p["published"])
    self.assertEqual(p["external_provider_calls"],0)
    self.assertEqual(p["review"],"HOLD")
    (self.root/"FUT_04_1920x1080.png").write_bytes(b"changed")
    with self.assertRaises(ValueError):module.accepted()
 def test_does_not_claim_completion_for_partial_journal(self):
    module.RECEIPT.write_text(json.dumps({"scope":module.ALLOWED}))
    module.JOURNAL.write_text(json.dumps({"01":{"state":"submitted"}}))
    out=module.accepted()
    self.assertEqual(out["status"],"submitted_or_processing")
    self.assertEqual(out["completed"],0)
 def test_tampered_receipt_rejected(self):
    module.RECEIPT.write_text(json.dumps({"scope":{**module.ALLOWED,"image_count":100}}))
    with self.assertRaises(ValueError):module.accepted()
 def test_loopback_windows_provider_and_no_paid_endpoints(self):
    source=(HERE/"p04_ten_image_writer.py").read_text()
    self.assertIn("if not self.auth():return self.send(401",source)
    self.assertIn('with RECEIPT.open("x")',source)
    self.assertIn('if payload!=ALLOWED:return self.send(422',source)
    self.assertNotIn("api.dev.runwayml.com",source)
    self.assertNotIn("OpenAI",source)
    self.assertIn('"needs_owner_review":True',source)

if __name__=="__main__":unittest.main()
