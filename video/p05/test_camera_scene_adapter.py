"""Offline camera catalog→P05 scene integration tests; never submit provider tasks."""
import copy,pathlib,unittest
from unittest.mock import patch
from camera_scene_adapter import planned_camera_scene_intents,CAMERA_BY_SCENE,CATALOG
from camera_direction_contract import load_catalog,CameraSpecRejected
from engine import STAGES
BASE={"mode":"image_to_video","model":"gen4.5","ratio":"1280:720","duration":5,
      "promptText":"Original fictional AI-assisted industrial technology, preserve silhouette",
      "reference_sha256":"a"*64,"requires_human_review":True}
class SceneCameraTests(unittest.TestCase):
 def fixture(self):
    return [dict(BASE,scene_id=scene,reference_sha256=chr(97+i)*64) for i,scene in enumerate(STAGES)]
 def test_all_three_scenes_compile_from_actual_90_term_catalog(self):
    self.assertEqual(len(load_catalog(CATALOG)),90)
    with patch("camera_scene_adapter.make_scene_requests",return_value=self.fixture()):
        results=planned_camera_scene_intents("synthetic-bundle")
    self.assertEqual([x["scene_id"] for x in results],list(STAGES))
    for result in results:
        self.assertFalse(result["provider_submit"])
        self.assertFalse(result["external_asset_upload"])
        self.assertFalse(result["publish_authorized"])
        self.assertTrue(result["requires_human_review"])
        self.assertIn("CINEMATOGRAPHY CONTRACT",result["promptText"])
        self.assertEqual(result["camera_catalog_version"],"1.0")
 def test_reference_bytes_and_scene_order_preserved(self):
    original=self.fixture()
    with patch("camera_scene_adapter.make_scene_requests",return_value=original):
        results=planned_camera_scene_intents("synthetic-bundle")
    self.assertEqual([x["reference_sha256"] for x in results],[x["reference_sha256"] for x in original])
    self.assertEqual(set(CAMERA_BY_SCENE),set(STAGES))
 def test_wrong_scene_count_fail_closed(self):
    with patch("camera_scene_adapter.make_scene_requests",return_value=self.fixture()[:2]):
        with self.assertRaises(CameraSpecRejected):planned_camera_scene_intents("synthetic-bundle")
 def test_unknown_model_code_fail_closed(self):
    with patch("camera_scene_adapter.make_scene_requests",return_value=self.fixture()):
        with patch.dict(CAMERA_BY_SCENE,{"S01":{**CAMERA_BY_SCENE["S01"],"movement":"MOV-999"}}):
            with self.assertRaises(CameraSpecRejected):planned_camera_scene_intents("synthetic-bundle")
if __name__=="__main__":unittest.main()
