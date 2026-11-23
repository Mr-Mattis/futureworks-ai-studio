"""VQ03 development acceptance: repeatable files and exact rights guard.
Does NOT certify photorealism, true cloth physics, brand design, or collision accuracy.
"""
from pathlib import Path
from PIL import Image
import json,hashlib,subprocess,unittest,ast,os
HOME=Path.home()
ROOT=HOME/"Documents"/"futureworks-vq03"
OUT=ROOT/"proof-v5"
CANONICAL=HOME/"Documents"/"futureworks-p04-data"/"character-library"/"FWAI-M001"/"v2.0"/"FWAI-M001_APPROVED_FINAL_MASTER_V2.0.png"
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
class VQ03Technical(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scene=json.loads((OUT/"VQ03_PROOF_MANIFEST.json").read_text())
        cls.blender=json.loads((OUT/"VQ03_ACCEPTANCE.json").read_text())
        cls.gpu=json.loads((OUT/"VQ03_COMFY_RECEIPT.json").read_text())
    def test_01_height_metric(self):
        self.assertEqual(self.scene["mech_height_m"],1.9558)
        self.assertEqual(self.scene["height_inches"],77.0)
    def test_02_canon_sha(self):
        self.assertEqual(digest(CANONICAL),self.scene["canonical_reference_sha256"])
    def test_03_blend_sha(self):
        self.assertEqual(digest(OUT/self.scene["blend"]),self.scene["blend_sha256"])
    def test_04_pose_count(self):
        self.assertEqual(self.scene["pose_frames"],[1,36,72])
    def test_05_pose_renders(self):
        self.assertEqual(len(self.scene["render_files"]),3)
        for asset in self.scene["render_files"]:
            self.assertEqual(digest(OUT/asset["render"]),asset["sha256"])
            with Image.open(OUT/asset["render"]) as im:self.assertEqual(im.size,(1280,720))
    def test_06_pose_distinct(self):
        self.assertEqual(len(set(x["sha256"] for x in self.scene["render_files"])),3)
    def test_07_rig_mechanics(self):
        self.assertTrue(self.blender["all_pass"])
        self.assertEqual(self.blender["total"],21)
        self.assertTrue(self.blender["checks"]["ik_constraints"])
        self.assertTrue(self.blender["checks"]["actual_crouch_translation"])
    def test_08_fixed_foot_targets(self):
        feet=self.blender["foot_targets_by_frame"]
        self.assertEqual(feet["1"],feet["36"])
        self.assertEqual(feet["36"],feet["72"])
    def test_09_vinyl_and_collision_present(self):
        self.assertTrue(self.blender["checks"]["vinyl_phase_shapes"])
        self.assertTrue(self.blender["checks"]["car_collision_proxy"])
        self.assertFalse(self.scene["physical_cloth_solver_approved"])
    def test_10_gpu_was_actual(self):
        self.assertEqual(self.gpu["status"],"complete")
        self.assertTrue(self.gpu.get("task_id"))
        self.assertEqual(digest(OUT/self.gpu["output"]),self.gpu["output_sha256"])
        self.assertEqual(self.gpu["outside_mask_changes"],0)
    def test_11_video_exists(self):
        f=OUT/"VQ03_three_pose_3sec.mp4"
        self.assertTrue(f.is_file())
        self.assertGreater(f.stat().st_size,20000)
    def test_12_video_duration(self):
        raw=subprocess.check_output(["wsl.exe","-d","Ubuntu","--","ffprobe","-v","error",
          "-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",
          "/mnt/c/Users/"+os.environ["USERNAME"]+"/Documents/futureworks-vq03/proof-v5/VQ03_three_pose_3sec.mp4"],text=True)
        self.assertAlmostEqual(float(raw.strip()),3.0,places=2)
    def test_13_no_spend_or_publish(self):
        self.assertEqual(self.gpu["paid_calls"],0)
        self.assertFalse(self.gpu["publish"])
        self.assertFalse(self.scene["filming_approved"])
    def test_14_all_sources_parse(self):
        for file in ["build_vq03_scene.py","comfy_vq03.py","render_video.py",
           "enable_addons.py","fwai_vq03_addon.py","validate_blender_vq03.py","prepare_gui.py"]:
            ast.parse((ROOT/file).read_text(encoding="utf-8"))
    def test_15_original_image_immutable(self):
        self.assertEqual(digest(CANONICAL),"480263bdd7637bfb2d90cc2deecdeb616eef03492a35216dbebfd3b1f44c555c")
    def test_16_workflow_launchers_exist(self):
        self.assertTrue((ROOT/"run_vq03_poc.ps1").is_file())
        self.assertTrue((ROOT/"fwai_vq03_addon.py").is_file())
    def test_17_reference_pass_not_design_approval(self):
        self.assertFalse(self.scene["creative_approval"])
        self.assertFalse(self.gpu["photorealism_approved"])
        self.assertFalse(self.gpu["vinyl_simulation_approved"])
if __name__=="__main__":
    result=unittest.main(verbosity=2,exit=False).result
    summary={"schema":"FWAI_VQ03_COMBINED_TESTS","checks":result.testsRun,"failures":len(result.failures),
    "errors":len(result.errors),"all_pass":result.wasSuccessful(),"creative_approved":False}
    (OUT/"VQ03_COMBINED_TEST_RESULTS.json").write_text(json.dumps(summary,indent=2))
    if not result.wasSuccessful():raise SystemExit(1)
