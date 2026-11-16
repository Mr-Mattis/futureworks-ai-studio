"""P04 Visual Director metadata delivery tests: no model calls or pixel claims."""
from __future__ import annotations
from contextlib import contextmanager
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from engine import ImagePipeline, MANIFEST, MODEL, Rejected
from test_engine import FakeComfy, RUN
from visual_bridge import inspect_handoff, send_to_visual, REPO


class VisualBridgeTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.runner=ImagePipeline(self.root/"images.db",self.root/"images",FakeComfy())
        ids=self.runner.prepare(MANIFEST,run_id=RUN,model_sha=MODEL["sha256"])
        for i in ids:
            self.runner.submit_one(i)
            self.runner.poll_one(i)
        self.runner.visual_handoff(RUN)
        self.handoff=self.root/"images"/("VISUAL_DIRECTOR_HANDOFF_"+RUN+".json")
        self.assertTrue(self.handoff.is_file())

    def test_ten_files_validate_and_preserve_scene_provenance(self):
        data,refs=inspect_handoff(self.handoff)
        self.assertEqual(len(refs),10)
        self.assertEqual({r["scene_id"] for r in refs},
                         {"S01","S02","S03","S04","S05"})
        self.assertEqual({r["model_sha256"] for r in refs},{MODEL["sha256"]})
        self.assertFalse(any(data["authorization"].values()))

    def test_tamper_detection_prevents_visual_role_intake(self):
        data=json.loads(self.handoff.read_text())
        data["assets"][0]["sha256"]="0"*64
        self.handoff.write_text(json.dumps(data))
        with self.assertRaisesRegex(Rejected,"hash"):
            inspect_handoff(self.handoff)

    def test_false_asset_approval_is_rejected(self):
        data=json.loads(self.handoff.read_text())
        data["assets"][0]["approval_state"]="approved"
        self.handoff.write_text(json.dumps(data))
        with self.assertRaises(Rejected):
            inspect_handoff(self.handoff)

    def test_external_ollama_prohibited(self):
        with self.assertRaises(Rejected):
            send_to_visual(self.handoff,ollama_url="https://api.openai.com/v1/chat")

    def test_real_role_contract_uses_ten_asset_ids_in_planning_output(self):
        _,refs=inspect_handoff(self.handoff)
        path=REPO/"agents/p02_roles/live-runs/visual_director.json"
        candidate=copy.deepcopy(json.loads(path.read_text())["handoff"]["candidate"])
        candidate["project_id"]="FWAI-EP-0001"
        candidate["shots"]=[
            {"reference_asset_id":r["asset_id"],"scene_id":r["scene_id"],
             "shot_id":"SH"+str(i+1).zfill(2),
             "shot_notes":"Fictional concept reference; no pixel quality inspection"}
            for i,r in enumerate(refs)]
        candidate["unresolved_assets"]=["Human pixel-level inspection required"]
        class Response:
            def __enter__(self):
                return self
            def __exit__(self,*args):
                return None
            def read(self,limit=None):
                return json.dumps({"message":{"content":json.dumps(candidate)}}).encode()
        with patch("visual_bridge.urllib.request.urlopen",return_value=Response()):
            result=send_to_visual(self.handoff,target=self.root/"images"/"visual-result.json")
        self.assertEqual(result["agent_result"]["agent"]["role"],"visual_director")
        self.assertEqual(result["agent_result"]["execution"]["status"],"blocked")
        self.assertEqual(result["agent_result"]["validation"]["status"],"passed")
        self.assertFalse(any(result["agent_result"]["authorization"].values()))
        self.assertEqual(len(result["p04_reference_assets"]),10)
        canonical=result["agent_result"]
        # Prove adding P04 reference metadata never breaks the locked P01
        # envelope's additionalProperties=false contract.
        import importlib.util
        src=REPO/"contracts/agent-result/v1.0.0/validate_agent_result.py"
        spec=importlib.util.spec_from_file_location("p04_canonical_check",src)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.validate(canonical,MANIFEST,
            REPO/"contracts/production-manifest/v1.0.0"),[])


    def test_repack_legacy_visual_result_preserves_canonical_p01_contract(self):
        _,refs=inspect_handoff(self.handoff)
        source=REPO/"agents/p02_roles/live-runs/visual_director.json"
        candidate=copy.deepcopy(json.loads(source.read_text())["handoff"]["candidate"])
        candidate["project_id"]="FWAI-EP-0001"
        candidate["shots"]=[
            {"reference_asset_id":item["asset_id"],
             "scene_id":item["scene_id"],
             "shot_id":"SH"+str(i+1).zfill(2),
             "shot_notes":"Synthetic metadata only; pixel review pending."}
            for i,item in enumerate(refs)
        ]
        class Response:
            def __enter__(self):return self
            def __exit__(self,*args):return None
            def read(self,limit=None):
                return json.dumps({"message":{"content":json.dumps(candidate)}}).encode()
        legacy=self.root/"images"/"visual-old.json"
        with patch("visual_bridge.urllib.request.urlopen",return_value=Response()):
            bundle=send_to_visual(self.handoff,target=legacy)
        canonical=copy.deepcopy(bundle["agent_result"])
        canonical["p04_reference_assets"]=bundle["p04_reference_assets"]
        canonical["p04_visual_media_status"]=bundle["p04_visual_media_status"]
        legacy.write_text(json.dumps(canonical))
        from repack_visual import repack
        fixed=repack(self.handoff,legacy)
        self.assertEqual(fixed["agent_result"],bundle["agent_result"])
        self.assertEqual(repack(self.handoff,legacy),fixed)
        self.assertEqual(set(fixed),{
            "checkpoint","agent_result","p04_reference_assets","p04_visual_media_status"})

    def test_model_cannot_drop_reference_assets(self):
        _,refs=inspect_handoff(self.handoff)
        candidate={
            "project_id":"FWAI-EP-0001","look_bible":{},
            "continuity_rules":["Keep graphitic material"],
            "shots":[{"reference_asset_id":refs[0]["asset_id"],
                      "scene_id":refs[0]["scene_id"]}],
            "unresolved_assets":["Missing visual references"],
            "quality_criteria":["Manual review required"],
        }
        class Response:
            def __enter__(self):return self
            def __exit__(self,*args):return None
            def read(self,limit=None):
                return json.dumps({"message":{"content":json.dumps(candidate)}}).encode()
        with patch("visual_bridge.urllib.request.urlopen",return_value=Response()):
            with self.assertRaisesRegex(Rejected,"all ten"):
                send_to_visual(self.handoff)


if __name__=="__main__":
    unittest.main(verbosity=2)
