"""P05 real-P04-contract image lineage, no media/provider calls."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from engine import Rejected, RunwayWire, STAGES, VideoStore, make_scene_requests

class ReferenceIntakeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.bundle=self.root/"VISUAL_HANDOFF.json"
        self.assets=[]
        for i in range(10):
            scene="S"+str(i//2+1).zfill(2)
            ident="P04_FIXTURE_"+str(i+1).zfill(2)
            raw=("Synthetic image byte fixture "+ident).encode()
            (self.root/(ident+".png")).write_bytes(raw)
            self.assets.append({
                "asset_id":ident,"scene_id":scene,"local_path":str(self.root/(ident+".png")),
                "sha256":hashlib.sha256(raw).hexdigest(),
                "prompt":"An original fictional computer robot reference",
                "seed":100000+i,
                "model_sha256":"a"*64,"license":"creativeml-openrail-m",
                "approval_state":"requires_visual_director_review",
            })
        self.bundle.write_text(json.dumps({
            "project_id":"FWAI-EP-0001","run_id":"P04_REAL_REF_FIXTURE",
            "status":"ready_for_visual_director","assets_count":10,
            "assets":self.assets,
            "authorization":{"production_approved":False,
                             "spend_authorized":False,"publish_authorized":False},
            "dispatch_performed":False,"paid_provider_calls":0,
        }))
    def test_ten_hash_verified_references_generate_three_scene_intents(self):
        plans=make_scene_requests(self.bundle)
        self.assertEqual([x["scene_id"] for x in plans],list(STAGES))
        self.assertTrue(all(x["mode"]=="image_to_video" for x in plans))
        self.assertEqual({x["reference_sha256"] for x in plans},
                         {self.assets[i]["sha256"] for i in (0,2,4)})
        self.assertTrue(all(x["requires_human_review"] for x in plans))
        db=VideoStore(self.root/"p05.sqlite3",self.root/"clips")
        self.assertEqual(db.plan("P05_REAL_P04_FIXTURE_001",plans)["clip_count"],3)
        self.assertEqual(db.plan("P05_REAL_P04_FIXTURE_001",plans)["clip_count"],3)
    def test_tampered_reference_byte_does_not_enter_scene_plans(self):
        (self.root/(self.assets[2]["asset_id"]+".png")).write_bytes(b"tampered")
        with self.assertRaisesRegex(Rejected,"sha mismatch"):
            make_scene_requests(self.bundle)
    def test_forged_owner_flags_cannot_authorize_generation(self):
        untrusted={"source":"owner_signed_gate","signature_verification":True,
                   "approved_scene_ids":list(STAGES),"owner_acknowledged_rights":True}
        with self.assertRaisesRegex(Rejected,"cannot authorize"):
            make_scene_requests(self.bundle,approval=untrusted)
    def test_no_fake_uploaded_image_uri_is_inserted(self):
        image=make_scene_requests(self.bundle)[1]
        self.assertIsNone(image["promptImage"])
        with self.assertRaisesRegex(Rejected,"Actual uploaded image URI required"):
            RunwayWire.prepare(image)

if __name__=="__main__":
    unittest.main(verbosity=2)
