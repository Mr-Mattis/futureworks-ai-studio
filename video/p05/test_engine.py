"""P05.01–07 networkless contract, continuity and failure-injection tests."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
import uuid

from engine import (MANIFEST, MODEL, Rejected, RunwayWire, STAGES, TEMPLATES,
                    VideoStore, continuity_review, make_scene_requests,
                    mp4_probe, sha, validate_approval)

def mock_mp4():
    # Tiny ISO-BMFF *fixture* to test persistence; NOT a real video.
    ftyp = struct.pack(">I",24)+b"ftypisom"+bytes(12)
    moov = struct.pack(">I",8)+b"moov"
    mdat = struct.pack(">I",8)+b"mdat"
    return ftyp+moov+mdat

def plans():
    return [dict(project_id="FWAI-EP-0001", scene_id=s, mode="image_to_video",
                model=MODEL,ratio="1280:720",duration=5,
                promptText="Original fictional robot concept with consistent silhouette",
                reference_sha256="a"*64,reference_asset_id="P04_REF_"+s,
                reference_local_path="/isolated/test-only.png",
                promptImage=None,manifest_sha256="b"*64,requires_human_review=True)
            for s in STAGES]

class VideoEngineTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        self.studio=VideoStore(self.root/"jobs.db",self.root/"clips")
        self.run="P05_DEV_FIXTURE_001"
    def plan(self):
        return self.studio.plan(self.run,plans())
    def test_three_scene_plan_and_replay(self):
        x=self.plan()
        self.assertEqual(x["clip_count"],3)
        self.assertEqual(self.plan()["clip_count"],3)
        self.assertFalse(any(x["authorization"].values()))
        self.assertEqual(x["budget_authorized_cents"],0)
    def test_plan_identity_conflict(self):
        self.plan()
        bad=plans()
        bad[0]["promptText"]="altered"
        with self.assertRaisesRegex(Rejected,"Idempotency conflict"):
            self.studio.plan(self.run,bad)
    def test_paid_adapter_cannot_be_enabled(self):
        with self.assertRaisesRegex(Rejected,"Paid Runway"):
            RunwayWire(enable_paid_calls=True)
    def test_runway_current_version_text_to_video(self):
        req=dict(plans()[0],mode="text_to_video")
        result=RunwayWire.prepare(req)
        self.assertEqual(result["endpoint"],"/v1/text_to_video")
        self.assertEqual(result["version"],"2024-11-06")
        self.assertNotIn("promptImage",result["body"])
    def test_runway_current_version_image_to_video_requires_real_upload(self):
        with self.assertRaises(Rejected):
            RunwayWire.prepare(plans()[0])
        call=RunwayWire.prepare(plans()[0],image_uri="runway://uploads/test-image")
        self.assertEqual(call["endpoint"],"/v1/image_to_video")
        self.assertEqual(call["body"]["promptImage"],"runway://uploads/test-image")
    def test_provider_receipt_and_poll_identity(self):
        task=str(uuid.uuid4())
        self.assertEqual(RunwayWire.parse_created({"id":task}),task)
        self.assertEqual(RunwayWire.parse_status({"id":task,"status":"SUCCEEDED",
                           "output":["https://media.example.invalid/temporary.mp4"]},task),
                         ("SUCCEEDED","https://media.example.invalid/temporary.mp4"))
        with self.assertRaises(Rejected):
            RunwayWire.parse_status({"id":str(uuid.uuid4()),"status":"SUCCEEDED"},task)
    def test_provider_unknown_result_rejected(self):
        with self.assertRaises(Rejected):
            RunwayWire.parse_created({"status":"ok"})
        with self.assertRaises(Rejected):
            RunwayWire.parse_status({"id":"foo","status":"PAID_BUT_UNVERIFIED"},"foo")
    def test_simulated_task_receipts_cannot_duplicate(self):
        self.plan()
        t=str(uuid.uuid4())
        self.studio.stage_mock_receipt(self.run,"S01",t)
        with self.assertRaises(Rejected):
            self.studio.stage_mock_receipt(self.run,"S01",str(uuid.uuid4()))
    def test_async_mock_poll_bounded(self):
        self.plan()
        task=self.studio.stage_mock_receipt(self.run,"S01",str(uuid.uuid4()))
        self.assertEqual(self.studio.poll_mock(self.run,"S01",
                        {"id":task,"status":"RUNNING"}),"mock_running")
        self.assertEqual(self.studio.poll_mock(self.run,"S01",
                        {"id":task,"status":"RUNNING"}),"not_due")
        self.assertEqual(self.studio.poll_mock(self.run,"S01",
                        {"id":task,"status":"SUCCEEDED","output":["https://example.invalid/x.mp4"]},
                        at="9999-12-31T00:00:00+00:00"),"mock_output_pending")
    def test_throttled_task_has_bounded_backoff_and_quarantine(self):
        self.plan()
        task=self.studio.stage_mock_receipt(self.run,"S01",str(uuid.uuid4()))
        observed=[]
        for n in range(10):
            state=self.studio.poll_mock(self.run,"S01",
                {"id":task,"status":"THROTTLED"},
                at="9999-12-31T00:00:00+00:00")
            observed.append(state)
        self.assertEqual(observed[:9],["mock_running"]*9)
        self.assertEqual(observed[-1],"needs_review")
        with self.assertRaises(Rejected):
            self.studio.poll_mock(self.run,"S01",
                {"id":task,"status":"SUCCEEDED","output":["https://test.invalid/a.mp4"]},
                at="9999-12-31T00:00:00+00:00")

    def test_poll_receipt_survives_new_process_database_reopen(self):
        self.plan()
        task=self.studio.stage_mock_receipt(self.run,"S02",str(uuid.uuid4()))
        self.studio.poll_mock(self.run,"S02",{"id":task,"status":"RUNNING"})
        restarted=VideoStore(self.studio.database,self.studio.output)
        self.assertEqual(restarted.poll_mock(self.run,"S02",
             {"id":task,"status":"SUCCEEDED",
              "output":["https://example.invalid/temporary.mp4"]},
              at="9999-12-31T00:00:00+00:00"),"mock_output_pending")
        self.assertEqual(restarted.dashboard(self.run)["clips"][1]["poll_count"],2)

    def test_mock_failed_and_cancelled_needs_review(self):
        self.plan()
        for scene,state in [("S01","FAILED"),("S02","CANCELLED")]:
            task=self.studio.stage_mock_receipt(self.run,scene,str(uuid.uuid4()))
            self.assertEqual(self.studio.poll_mock(self.run,scene,{"id":task,"status":state}),
                             "needs_review")
    def test_mock_clip_persistence_and_integrity(self):
        self.plan()
        data=mock_mp4()
        for scene in STAGES:
            task=self.studio.stage_mock_receipt(self.run,scene,str(uuid.uuid4()))
            self.studio.poll_mock(self.run,scene,
                        {"id":task,"status":"SUCCEEDED",
                         "output":["https://example.invalid/temporary.mp4"]})
            path=self.studio.save_mock_clip(self.run,scene,data)
            self.assertEqual(path.read_bytes(),data)
        dashboard=self.studio.dashboard(self.run)
        self.assertEqual(dashboard["mock_archived"],3)
        self.assertEqual(dashboard["actual_paid_clips"],0)
        self.assertEqual(dashboard["actual_credits_used"],0)
    def test_bad_video_rejected(self):
        self.plan()
        task=self.studio.stage_mock_receipt(self.run,"S01",str(uuid.uuid4()))
        self.studio.poll_mock(self.run,"S01",
            {"id":task,"status":"SUCCEEDED","output":["https://example.invalid/x.mp4"]})
        with self.assertRaises(Rejected):
            self.studio.save_mock_clip(self.run,"S01",b"not video")
    def test_video_temporal_consistency_requires_manual_review(self):
        result=continuity_review(plans())
        self.assertEqual(result["verdict"],"human_review_required")
        self.assertFalse(result["publish_authorized"])
        self.assertTrue(result["issues"])
    def test_approvals_fail_closed(self):
        with self.assertRaises(Rejected):
            validate_approval({"source":"model","signature_verification":True})
        with self.assertRaises(Rejected):
            validate_approval({"source":"owner_signed_gate","signature_verification":False})
    def test_templates_three_categories(self):
        self.assertEqual(set(TEMPLATES),{"AI_CONCEPT","REAL_BUILD","HYBRID"})

if __name__=="__main__":
    unittest.main(verbosity=2)
