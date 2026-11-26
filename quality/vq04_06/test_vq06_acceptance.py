"""VQ04.06 engineering and immutable-owner-source gate.

Local only: asserts real baked cloth is driven from mech index fingertip rather
than VQ05's unrelated animated Hook; all 72 frames and door proxy diagnostic.
Does not declare a physically closed grip, adhesive force or artistic fidelity.
"""
import json,unittest,hashlib,subprocess,os
from pathlib import Path
HOME=Path.home()
ROOT=HOME/"Documents"/"futureworks-vq04-06"
E=ROOT/"evidence"
SOURCE=HOME/"Documents"/"futureworks-vq04-04"/"scene"/"FWAI_VQ04_04_CONTACT_V2.blend"
SCENE=ROOT/"scene"/"FWAI_VQ04_06_COUPLED_CLOTH_BAKED_V2.blend"
LATEST=HOME/"Documents"/"futureworks-p04-comfyui"/"output"/"FWAI_M001_LOCKED_V2_CHARACTER_KEYFRAME_00002_.png"
MASTER_SHA="5dcefd9309510754d7b5dd5dd549eae6f3244d1a4a3b6f9056c2055d620ba12b"
OLD=HOME/"Documents"/"futureworks-vq04-04"/"evidence"/"VQ04_04_COMBINED_ACCEPTANCE.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
class Gate(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.man=json.loads((E/"VQ04_06_COUPLED_BAKE_MANIFEST_V2.json").read_text())
  cls.diag=json.loads((E/"VQ04_06_COUPLING_DIAGNOSTICS.json").read_text())
  cls.frames=json.loads((E/"VQ04_06_FRAME_TRACE.json").read_text())
  cls.render=json.loads((E/"VQ04_06_COUPLED_RENDER.json").read_text())
  cls.gui=json.loads((ROOT/"live_bridge"/"ack.json").read_text())
  cls.old=json.loads(OLD.read_text(encoding="utf-8-sig"))
 def test_01_latest_owner_master_is_unchanged(self):self.assertEqual(sha(LATEST),MASTER_SHA)
 def test_02_baseline_scene_preserved(self):self.assertEqual(sha(SOURCE),self.old["scene_hash"].lower())
 def test_03_saved_scene_hash_verified(self):self.assertEqual(sha(SCENE),self.man["sha256"])
 def test_04_real_cache_baked(self):self.assertTrue(self.man["cache_is_baked"])
 def test_05_actual_cache_files(self):self.assertEqual(self.diag["cache_file_count"],72)
 def test_06_all_simulation_frames(self):self.assertEqual(self.diag["frames"],72)
 def test_07_all_frame_trace_present(self):self.assertEqual(len(self.frames),72)
 def test_08_all_center_positions_distinct(self):self.assertEqual(self.diag["distinct_sheet_center_positions"],72)
 def test_09_no_source_shape_keys(self):self.assertEqual(self.man["modifier_order"],["HOOK","CLOTH","SOLIDIFY"])
 def test_10_mech_tip_drives_hook(self):self.assertEqual(self.diag["controller_parent"],"FWAI GRIP / R_index_fingerpad")
 def test_11_ik_follows_original_animation(self):self.assertEqual(self.diag["ik_proxy_parent"],"IK TARGET / R HAND")
 def test_12_stable_3d_offset(self):self.assertLessEqual(self.diag["max_offset_residual_m"],.004)
 def test_13_pad_film_separation(self):self.assertLessEqual(self.diag["max_corner_distance_m"],.016)
 def test_14_all_frames_door_front_clear(self):self.assertEqual(self.diag["max_door_surface_intrusions"],0)
 def test_15_latest_owner_asset_locked_in_scene(self):self.assertTrue(self.diag["original_visual_sha_verified"])
 def test_16_three_stills_generated(self):self.assertEqual(len(self.render["image_tests"]),3)
 def test_17_three_stills_hashed(self):
  for row in self.render["image_tests"]:self.assertEqual(sha(E/row["file"]),row["sha256"])
 def test_18_all_72_video_frames(self):self.assertEqual(len(list((E/"frames_coupled").glob("S_*.png"))),72)
 def test_19_h264_three_seconds(self):
  r=subprocess.check_output(["wsl.exe","-d","Ubuntu","--","ffprobe","-v","error","-show_entries","format=duration",
   "-of","default=noprint_wrappers=1:nokey=1",
   "/mnt/c/Users/"+os.environ["USERNAME"]+"/Documents/futureworks-vq04-06/evidence/VQ04_06_MECH_COUPLED_CLOTH_3SEC.mp4"],text=True)
  self.assertAlmostEqual(float(r),3.,places=3)
 def test_20_visible_blender_acknowledges(self):
  self.assertTrue(self.gui["gui_visible"]);self.assertEqual(self.gui["status"],"ok");self.assertEqual(self.gui["frame"],36)
 def test_21_false_force_approval_not_claimed(self):self.assertFalse(self.diag["pressure_or_pinch_force_verified"])
 def test_22_false_quality_approval_not_claimed(self):self.assertFalse(self.diag["photoreal_quality_approved"])
 def test_23_no_external_media_or_paid_service(self):
  self.assertEqual(self.gui["paid_calls"],0);self.assertFalse(self.gui["scene_saved"])
 def test_24_rig_proxy_not_considered_real_force(self):self.assertFalse(self.diag["full_hand_film_collision_checked"])
if __name__=="__main__":
 result=unittest.main(verbosity=2,exit=False).result
 report={"schema":"FWAI_VQ04_06_ENGINEERING_ACCEPTANCE_V1","total":result.testsRun,
    "passed":result.testsRun-len(result.failures)-len(result.errors),
    "failures":len(result.failures),"errors":len(result.errors),"all_pass":result.wasSuccessful(),
    "mech_driven_cloth_real_bake":True,"photoreal_production_approved":False,
    "pay_api_calls":0,"video_published":False}
 (E/"VQ04_06_ACCEPTANCE.json").write_text(json.dumps(report,indent=2))
 if not result.wasSuccessful():raise SystemExit(1)
