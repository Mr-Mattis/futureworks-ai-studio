"""P04 source-controlled n8n adapter invariants, evaluated in Node VM offline."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import re
import subprocess
import unittest

HERE=Path(__file__).resolve().parent
SOURCE=(HERE/"workflow.inactive.sdk.js").read_text()
CODES=[json.loads(x) for x in re.findall(r'jsCode:("(?:\\.|[^"\\])*")',SOURCE)]
if len(CODES)!=3:
    raise AssertionError("Expected exactly three P04 Code-node policies")
FREEZE, ACK, REPORT=CODES
RUN="P04_DEV_N8N_001"
GOOD={"project_id":"FWAI-EP-0001","run_id":RUN,"image_count":10,
      "state":"accepted_for_async_generation","paid_provider_calls":0,
      "authorization":{"production_approved":False,"spend_authorized":False,
                       "publish_authorized":False}}
DASH={"run_id":RUN,"total":10,"completed":10,"needs_review":0,
      "status":"ready_for_visual_review","paid_provider_calls":0,
      "authorization":GOOD["authorization"],
      "images":[{"image_id":f"IMG_{i}","state":"complete",
                 "path":f"TEST_{i}.png","image_sha":"a"*64} for i in range(10)]}


def invoke(code, rows):
    p=subprocess.run(["/usr/bin/node",str(HERE/"check_n8n_wrapper.cjs")],
                     input=json.dumps({"code":code,"items":rows}),
                     capture_output=True,text=True,check=True,timeout=10)
    return json.loads(p.stdout)


class N8nAdapterTests(unittest.TestCase):
    def test_no_live_workflow_credentials_or_providers(self):
        self.assertIn("n8n-nodes-base.scheduleTrigger",SOURCE)
        self.assertIn("host.docker.internal:18741/v1/start",SOURCE)
        self.assertIn("host.docker.internal:18741/v1/status",SOURCE)
        self.assertIn("__P04_DEV_API_TOKEN_INJECT_AT_RUNTIME__",SOURCE)
        for prohibited in ("runwayml.com","api.heygen.com","youtubeUpload",
                           "api.openai.com","paidProviderSubmit"):
            self.assertNotIn(prohibited,SOURCE)

    def test_frozen_input_is_exact(self):
        result=invoke(FREEZE,[{}])
        self.assertTrue(result["ok"],result)
        x=result["result"][0]["json"]
        self.assertEqual(x["project_id"],"FWAI-EP-0001")
        self.assertEqual(x["manifest_sha256"],"cf2bbd17b2170755fef18de1be5ea4c08694ee894c8167c70ed322aa9906fe87")
        self.assertFalse(invoke(FREEZE,[{"brief":"unapproved"}])["ok"])

    def test_positive_queue_ack_has_no_authority(self):
        result=invoke(ACK,[GOOD])
        self.assertTrue(result["ok"],result)
        x=result["result"][0]["json"]
        self.assertFalse(any(x["authorization"].values()))
        self.assertEqual(x["status"],"async_image_batch_queued")

    def test_unsafe_ack_and_wrong_batch_rejected(self):
        for override in ({"image_count":9},
                         {"paid_provider_calls":1},
                         {"authorization":{"spend_authorized":True}},
                         {"state":"completed_and_published"},
                         {"run_id":"OTHER"}):
            with self.subTest(override=override):
                self.assertFalse(invoke(ACK,[GOOD|override])["ok"])

    def test_ready_report_requires_ten_indexed_images(self):
        result=invoke(REPORT,[DASH])
        self.assertTrue(result["ok"],result)
        self.assertTrue(result["result"][0]["json"]["visual_handoff_ready"])

    def test_dashboard_forgery_and_false_permissions_rejected(self):
        for change in (
            lambda x:x.update(completed=9),
            lambda x:x["images"].pop(),
            lambda x:x["images"][0].update(path=""),
            lambda x:x["images"][0].update(image_sha=""),
            lambda x:x["images"][0].update(state="needs_review"),
            lambda x:x["authorization"].update(publish_authorized=True),
            lambda x:x.update(run_id="WRONG"),
            lambda x:x.update(paid_provider_calls=2),
        ):
            altered=copy.deepcopy(DASH)
            change(altered)
            self.assertFalse(invoke(REPORT,[altered])["ok"])


if __name__=="__main__":
    unittest.main(verbosity=2)
