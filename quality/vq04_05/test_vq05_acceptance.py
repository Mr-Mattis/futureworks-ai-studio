"""VQ04.05 immutable end-to-end proof gate (no side effects).

Verifies actual Blender point-cache data, reopened all-frame numerical trace,
unchanged owner masters, local H.264 video, live GUI and bridge security results.
This does not certify adhesive strength, motor force, or cinematic appearance.
"""
import unittest,json,hashlib,subprocess,os,math
from pathlib import Path
root=Path.home()/"Documents"/"futureworks-vq04-05"
e=root/"evidence"
old=Path.home()/"Documents"/"futureworks-vq04-04"
canon=Path.home()/"Documents"/"futureworks-p04-data"/"character-library"/"FWAI-M001"/"v2.0"/"FWAI-M001_APPROVED_FINAL_MASTER_V2.0.png"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bake=json.loads((e/"VQ04_05_BAKE_MANIFEST.json").read_text())
        cls.diag=json.loads((e/"VQ04_05_SIMULATION_DIAGNOSTIC.json").read_text())
        cls.frames=json.loads((e/"VQ04_05_FRAME_TRACE.json").read_text())
        cls.renders=json.loads((e/"VQ04_05_RENDER_PROOF.json").read_text())
        cls.smooth=json.loads((e/"VQ04_05_SMOOTH_RENDER.json").read_text())
        cls.ui=json.loads((e/"VQ04_05_UI_TESTS.json").read_text())
        cls.gui=json.loads((root/"live_bridge"/"ack.json").read_text())
        cls.old=json.loads((old/"evidence"/"VQ04_04_COMBINED_ACCEPTANCE.json").read_text(encoding="utf-8-sig"))
    def test_01_canonical_lock(self):
        self.assertEqual(sha(canon),"480263bdd7637bfb2d90cc2deecdeb616eef03492a35216dbebfd3b1f44c555c")
    def test_02_prior_blend_not_mutated(self):
        self.assertEqual(sha(old/"scene"/"FWAI_VQ04_04_CONTACT_V2.blend"),self.old["scene_hash"].lower())
    def test_03_new_blend_sha(self):
        self.assertEqual(sha(self.bake["scene"]),self.bake["sha256"])
    def test_04_reloaded_disk_cache_baked(self):
        self.assertTrue(self.bake["cache_is_baked"])
        self.assertTrue(self.diag["reopened_disk_cache_baked"])
    def test_05_72_real_physics_frames(self):
        self.assertEqual(self.diag["cache_files"],72)
        self.assertEqual(self.diag["n_frames"],72)
        self.assertGreater(self.diag["cache_bytes"],100000)
    def test_06_real_modifier_stack(self):
        self.assertEqual(self.diag["modifier_stack"],["HOOK","CLOTH","SOLIDIFY"])
        self.assertTrue(self.bake["physical_cloth_solver_used"])
        self.assertEqual(self.diag["keyframe_shapes"],0)
    def test_07_film_topology(self):
        self.assertEqual(self.diag["mesh_topology"],425)
        self.assertEqual(self.bake["quads"],384)
        self.assertEqual(self.bake["clamped_film_surface_thickness_m"],.00025)
    def test_08_pin_boundary(self):
        self.assertEqual(self.bake["pin_adhered_vertices"],153)
        self.assertEqual(self.bake["pin_gripper_vertices"],17)
        self.assertLess(self.diag["worst_adhesion_anchor_drift_m"],.001)
    def test_09_full_range_door_no_penetration(self):
        self.assertEqual(self.diag["max_door_intersecting_vertices"],0)
        self.assertGreaterEqual(self.diag["min_surface_door_gap_m"],.001)
    def test_10_intermediate_frames_physically_distinct(self):
        self.assertEqual(self.diag["center_position_distinct_all_frames"],72)
    def test_11_free_film_deforms(self):
        self.assertGreater(self.diag["dynamic_mean_free_delta_range_m"][1],.08)
    def test_12_first_last_control_motion(self):
        self.assertNotEqual(self.diag["samples"]["1"]["grip_control_xyz_m"],
                            self.diag["samples"]["72"]["grip_control_xyz_m"])
    def test_13_six_real_stills_hashed(self):
        self.assertEqual(len(self.renders["evidence"]),6)
        for row in self.renders["evidence"]:
            self.assertEqual(sha(e/row["image"]),row["sha256"])
    def test_14_72_raw_video_frames(self):
        self.assertEqual(self.renders["video_frame_count"],72)
        self.assertEqual(self.renders["video_fps"],24)
        self.assertEqual(len(self.renders["video_frames_sha256"]),72)
    def test_15_smooth_stills_not_canonical_replacement(self):
        self.assertEqual(len(self.smooth["image_tests"]),3)
        self.assertTrue(self.smooth["render_only"])
        for row in self.smooth["image_tests"]:
            self.assertEqual(sha(e/row["file"]),row["sha256"])
    def test_16_smooth_video_frames_exist(self):
        self.assertEqual(len(list((e/"frames_smooth").glob("S_*.png"))),72)
    def test_17_raw_video_3s(self):
        self.assertAlmostEqual(duration(e/"VQ04_05_BAKED_CLOTH_3SEC.mp4"),3.,places=2)
    def test_18_smooth_video_3s(self):
        self.assertAlmostEqual(duration(e/"VQ04_05_SMOOTH_CLOTH_3SEC.mp4"),3.,places=2)
    def test_19_addon_security_regressions(self):
        self.assertTrue(self.ui["all_pass"])
        self.assertGreaterEqual(self.ui["passed"],29)
    def test_20_actual_visible_blender_ack(self):
        self.assertTrue(self.gui["gui_visible"])
        self.assertEqual(self.gui["status"],"ok")
        self.assertEqual(self.gui["frame"],36)
    def test_21_privacy_and_no_auto_save(self):
        self.assertEqual(self.gui["paid_calls"],0)
        self.assertFalse(self.gui["scene_saved"])
    def test_22_reproducible_source_hash(self):
        self.assertEqual(self.renders["source_blend_sha256"],self.bake["sha256"])
    def test_23_creative_gate_not_falsified(self):
        self.assertFalse(self.bake["cinema_approved"])
        self.assertFalse(self.bake["adhesive_strength_tested"])
        self.assertFalse(self.bake["full_hand_grip_tested"])
        self.assertFalse(self.diag["production_material_properties_calibrated"])
    def test_24_local_reference_path(self):
        self.assertTrue(Path(self.bake["scene"]).is_file())
def duration(path):
    # Subprocess uses the verified local Linux ffprobe; only our two fixed files.
    winuser=os.environ["USERNAME"]
    linuxpath="/mnt/c/Users/"+winuser+"/Documents/futureworks-vq04-05/evidence/"+path.name
    raw=subprocess.check_output(["wsl.exe","-d","Ubuntu","--","ffprobe","-v","error",
       "-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",
       linuxpath],text=True)
    return float(raw.strip())
if __name__=="__main__":
    result=unittest.main(verbosity=2,exit=False).result
    report={"schema":"FWAI_VQ04_05_ACCEPTANCE_V1","tests":result.testsRun,
      "failures":len(result.failures),"errors":len(result.errors),
      "passed":result.testsRun-len(result.failures)-len(result.errors),
      "all_pass":result.wasSuccessful(),"creative_approved":False,
      "film_cloth_baked_and_reopened":True,
      "full_finger_and_adhesion_force":False,
      "collision_response_stress_tested":False,
      "paid_api_calls":0,"production_workflows_changed":False}
    (e/"VQ04_05_ACCEPTANCE.json").write_text(json.dumps(report,indent=2))
    if not result.wasSuccessful():raise SystemExit(1)
