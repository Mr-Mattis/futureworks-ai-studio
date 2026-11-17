"""Synthetic offline vocabulary/shot contract tests, no AI provider calls."""
import json,pathlib,tempfile,unittest
from camera_direction_contract import load_catalog,compile_camera_direction,CameraSpecRejected,CATEGORY_PREFIX
class CameraContractTests(unittest.TestCase):
 def setUp(self):
    self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
    self.path=pathlib.Path(self.tmp.name)/"catalog.json"
    self.data={"version":"1.0","brand":"Future Works AI Studio","catalog":[]}
    for kind,(prefix,cat,n) in CATEGORY_PREFIX.items():
        for i in range(1,n+1):
            code=f"{prefix}-{i:03d}"
            self.data["catalog"].append({"id":code,"category":cat,"name":f"Term {code}",
                "definition":f"Normalized technical definition for {code}",
                "agent_instruction_example":f"Instructional example for {code}","usage":"Production reference"})
    self.dump()
 def dump(self):self.path.write_text(json.dumps(self.data))
 def shot(self,index):
    return compile_camera_direction(index,movement="MOV-009",angle="ANG-010",framing="FRM-003",
              optics="OPT-002",duration_seconds=5,scene_id="S01",
              subject="realistic AI-assisted orbital construction machinery")
 def test_90_valid_and_sample_compiles(self):
    index=load_catalog(self.path)
    self.assertEqual(len(index),90)
    shot=self.shot(index)
    self.assertEqual(shot["camera_codes"]["movement"],"MOV-009")
    self.assertFalse(shot["provider_calls_authorized"])
    self.assertIn("Duration: 5 seconds",shot["instruction"])
 def test_unknown_code_rejected(self):
    index=load_catalog(self.path)
    with self.assertRaises(CameraSpecRejected):
        compile_camera_direction(index,movement="MOV-999",angle="ANG-010",framing="FRM-003",
                optics="OPT-002",duration_seconds=5,scene_id="S01",subject="mechanical structure")
 def test_wrong_category_rejected(self):
    index=load_catalog(self.path)
    with self.assertRaises(CameraSpecRejected):
        compile_camera_direction(index,movement="ANG-010",angle="ANG-010",framing="FRM-003",
                optics="OPT-002",duration_seconds=5,scene_id="S01",subject="mechanical structure")
 def test_catalog_mutation_rejected(self):
    self.data["catalog"].pop();self.dump()
    with self.assertRaises(CameraSpecRejected):load_catalog(self.path)
 def test_duplicate_rejected(self):
    self.data["catalog"][0]["id"]=self.data["catalog"][1]["id"];self.dump()
    with self.assertRaises(CameraSpecRejected):load_catalog(self.path)
 def test_duration_rejected(self):
    index=load_catalog(self.path)
    with self.assertRaises(CameraSpecRejected):
        compile_camera_direction(index,movement="MOV-009",angle="ANG-010",framing="FRM-003",
                optics="OPT-002",duration_seconds=50,scene_id="S01",subject="mechanical structure")
if __name__=="__main__":unittest.main()
