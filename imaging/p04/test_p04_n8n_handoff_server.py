"""P04 isolated authenticated gateway contract tests (no network, no secrets)."""
import importlib.util,json,pathlib,tempfile,unittest
from unittest import mock

HERE=pathlib.Path(__file__).resolve().parent
SERVER=HERE/"p04_n8n_handoff_server.py"
spec=importlib.util.spec_from_file_location("p04_gateway",SERVER)
gateway=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gateway)

class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.receipt=pathlib.Path(self.tmp.name)/"handoff.json"
        self.save=mock.patch.object(gateway,"RECEIPT",self.receipt)
        self.save.start();self.addCleanup(self.save.stop)
        self.root_patch=mock.patch.object(gateway,'OUT',pathlib.Path(self.tmp.name))
        self.root_patch.start();self.addCleanup(self.root_patch.stop)
        self.good={"status":"ACCEPTED_AUTHENTICATED_OWNER_SCOPED_REFERENCE_HANDOFF",
                   "paid_provider_calls":0,"scene_references":[{"scene_id":"S01"}],
                   "publication_authorized":False}
    def test_immutable_receipt_one_write(self):
        self.assertTrue(gateway.persist_once(self.good))
        self.assertFalse(gateway.persist_once(self.good))
        self.assertEqual(json.loads(self.receipt.read_text()),self.good)
    def test_mutated_receipt_fails_closed(self):
        gateway.persist_once(self.good)
        with self.assertRaises(gateway.Rejected):
            gateway.persist_once({**self.good,"paid_provider_calls":1})
    def test_production_and_paid_api_blocked_in_code(self):
        text=SERVER.read_text()
        self.assertIn('ThreadingHTTPServer(("0.0.0.0",18741)',text)
        self.assertIn('hmac.compare_digest(authorization,"Bearer "+configured)',text)
        self.assertIn("verify_scoped_pilot(",text)
        self.assertIn("make_scene_requests(BUNDLE)",text)
        self.assertNotIn("api.dev.runwayml.com",text)
        self.assertNotIn("POST /v1/image_to_video",text)
    def test_strict_payload_is_exactly_locked(self):
        payload={"project_id":"WRONG","run_id":"P04_GPU_001","manifest_sha256":gateway.EXPECTED_SHA,
                 "operation":"approved_reference_handoff"}
        with self.assertRaises(gateway.Rejected):
            gateway.verified_reference_handoff(payload)
    def test_missing_keys_fail_closed(self):
        with self.assertRaises(gateway.Rejected):
            gateway.verified_reference_handoff({"project_id":"FWAI-EP-0001"})

if __name__=="__main__":unittest.main()
