"""P04 authenticated local Comfy image API isolated tests, no sockets."""
from __future__ import annotations

import hashlib
import json
import tempfile
import time
from pathlib import Path
import unittest
from unittest.mock import patch

from api import MANIFEST, make_handler
from engine import MODEL, Rejected
from test_engine import FakeComfy

TOKEN="p04-synthetic-development-token-0000000000000000000000"
PROJECT="FWAI-EP-0001"
RUN="P04_API_TEST_001"
HASH=hashlib.sha256(MANIFEST.read_bytes()).hexdigest()


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder=Path(self.tmp.name)
        self.mock=FakeComfy()
        with patch("api.verify_model",return_value=MODEL["sha256"]):
            self.handler=make_handler(self.folder/"test.sqlite3",self.folder/"imgs",
                                      self.folder/MODEL["filename"],TOKEN,comfy=self.mock)

    def call(self,verb,path,body=None,token=TOKEN):
        req=object.__new__(self.handler)
        req.path=path
        req.headers={"Authorization":"Bearer "+token}
        req.respond=lambda status,payload:setattr(req,"answer",(status,payload))
        if body is not None:
            req.read_json=lambda:body
        getattr(req,"do_"+verb)()
        return req.answer

    def payload(self):
        return {"project_id":PROJECT,"run_id":RUN,"manifest_sha256":HASH}

    def test_no_unauthorized_intake_or_read(self):
        self.assertEqual(self.call("POST","/v1/start",self.payload(),token="bad")[0],401)
        self.assertEqual(self.call("GET","/v1/status?run_id="+RUN,token="bad")[0],401)

    def test_weak_token_fails_before_api_exists(self):
        with self.assertRaises(Rejected):
            make_handler(self.folder/"invalid.sqlite3",self.folder/"other",
                         self.folder/MODEL["filename"],"weak",comfy=self.mock)

    def test_frozen_manifest_and_overposted_authorization_blocked(self):
        for edits in (
            {"project_id":"WRONG"}, {"run_id":" "},
            {"manifest_sha256":"f"*64}, {"spend_authorized":True},
            {"publish_authorized":True}, {"provider":"heygen"},
        ):
            with self.subTest(edits=edits):
                status,_=self.call("POST","/v1/start",self.payload()|edits)
                self.assertEqual(status,400)

    def test_real_asynchronous_mock_10_asset_batch_without_manual_transfer(self):
        status,receipt=self.call("POST","/v1/start",self.payload())
        self.assertEqual(status,202)
        self.assertEqual(receipt["image_count"],10)
        self.assertFalse(any(receipt["authorization"].values()))
        deadline=time.monotonic()+4
        while time.monotonic()<deadline:
            _,status_report=self.call("GET","/v1/status?run_id="+RUN)
            if status_report["completed"]==10:
                break
            time.sleep(.03)
        self.assertEqual(status_report["completed"],10)
        self.assertEqual(status_report["status"],"ready_for_visual_review")
        code,result=self.call("GET","/v1/visual-handoff?run_id="+RUN)
        self.assertEqual(code,200)
        self.assertEqual(result["assets_count"],10)
        self.assertTrue(all(x["approval_state"]=="requires_visual_director_review"
                            for x in result["assets"]))
        self.assertFalse(any(result["authorization"].values()))
        self.assertEqual(len(self.mock.submissions),10)

    def test_replay_request_cannot_submit_duplicate_work(self):
        self.call("POST","/v1/start",self.payload())
        self.call("POST","/v1/start",self.payload())
        deadline=time.monotonic()+4
        while time.monotonic()<deadline and len(self.mock.submissions)<10:
            time.sleep(.02)
        self.assertEqual(len(self.mock.submissions),10)

    def test_paid_and_approval_routes_not_available(self):
        for path in ("/v1/provider-submit","/v1/publish","/v1/approve",
                     "/v1/send-to-runway"):
            code,_=self.call("POST",path,self.payload())
            self.assertEqual(code,404)

    def test_health_reports_local_only(self):
        status,data=self.call("GET","/v1/health")
        self.assertEqual(status,200)
        self.assertEqual(data["engine"],"comfyui-local")
        self.assertEqual(data["paid_provider_calls"],0)

    def test_early_visual_handoff_denied(self):
        # Do not launch a background generator that can race teardown.
        # A completely absent run must always fail closed.
        status,_=self.call("GET","/v1/visual-handoff?run_id=UNKNOWN")
        self.assertEqual(status,400)

    def test_accepted_run_reaches_stable_completed_state_before_teardown(self):
        status,_=self.call("POST","/v1/start",self.payload())
        self.assertEqual(status,202)
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            code,report=self.call("GET","/v1/status?run_id="+RUN)
            if code==200 and report["completed"]==10:
                break
            time.sleep(.02)
        self.assertEqual(report["completed"],10)
        self.assertEqual(report["needs_review"],0)


if __name__=="__main__":
    unittest.main(verbosity=2)
