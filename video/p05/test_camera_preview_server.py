"""Network-free static tests for authenticated P05 camera-plan preview."""
import importlib.util,pathlib,unittest
from unittest.mock import patch
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("camera_preview_server",HERE/"camera_preview_server.py")
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
def item(scene):
    return {"scene_id":scene,"reference_sha256":"a"*64,"duration":5,
            "cinematography":{"camera_codes":{"movement":"MOV-009","angle":"ANG-010","framing":"FRM-003","optics":"OPT-002"},
            "instruction":"5-second orbit to reveal engineered futuristic hardware"}}
class PreviewContract(unittest.TestCase):
 def test_three_camera_intents_readonly(self):
    with patch.object(server,"planned_camera_scene_intents",return_value=[item(s) for s in ("S01","S02","S03")]):
        p=server.previews()
    self.assertEqual(p["scene_count"],3)
    self.assertEqual(p["catalog_version"],"1.0")
    self.assertEqual(p["paid_provider_calls"],0)
    self.assertFalse(p["production_activated"])
    self.assertFalse(p["publication_authorized"])
    self.assertTrue(all(s["provider_submit"] is False for s in p["scenes"]))
 def test_missing_scene_fails_closed(self):
    with patch.object(server,"planned_camera_scene_intents",return_value=[item("S01"),item("S02")]):
        with self.assertRaises(ValueError):server.previews()
 def test_endpoint_is_readonly_and_authenticated(self):
    src=(HERE/"camera_preview_server.py").read_text()
    self.assertIn("hmac.compare_digest",src)
    self.assertIn("def do_POST(self):return self.send(405",src)
    self.assertNotIn("api.dev.runwayml.com",src)
if __name__=="__main__":unittest.main()
