"""Offline acceptance checks for Blender->ComfyUI and WLM POC.
Results demonstrate technical execution, NOT physical plausibility or owner approval.
"""
from pathlib import Path
import unittest,json,hashlib,ast,os
from PIL import Image,ImageChops
BASE=Path.home()/"Documents"/"futureworks-maintenance"
POC=BASE/"poc-bl05-gpu-baseline"
def checksum(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()
class TestIntegratedProof(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pose=json.loads((POC/"BL01_pose_manifest.json").read_text())
        cls.gpu=json.loads((POC/"BL01_P04_GPU_RECEIPT.json").read_text())
        cls.wlm=json.loads((BASE/"WLM01_report.json").read_text())
    def test_01_blender_scene_exists(self):
        self.assertTrue((POC/"BL01_mech_pose.blend").is_file())
        self.assertGreater((POC/"BL01_mech_pose.blend").stat().st_size,4000)
    def test_02_pose_control_manifest(self):
        self.assertEqual(self.pose["schema"],"FWAI_BL01_BLOCKING_V1")
        self.assertEqual(self.pose["resolution"],[1024,576])
        self.assertEqual(len(self.pose["pose_pixels"]["left_leg"]),4)
        self.assertEqual(len(self.pose["pose_pixels"]["right_leg"]),4)
    def test_03_blender_render_integrity(self):
        self.assertEqual(checksum(POC/"BL01_mech_pose_overlay.png"),self.pose["render_sha256"])
        with Image.open(POC/"BL01_mech_pose_overlay.png") as im:
            self.assertEqual(im.size,(1024,576))
    def test_04_live_local_gpu_receipt(self):
        self.assertEqual(self.gpu["status"],"complete")
        self.assertEqual(self.gpu["schema"],"FWAI_BL05_SD15_GPU_FALLBACK_V1")
        self.assertTrue(self.gpu.get("prompt_id"))
    def test_05_local_uncharged(self):
        self.assertEqual(self.gpu["paid_calls"],0)
        self.assertEqual(self.gpu["runway_calls"],0)
        self.assertFalse(self.gpu["visual_approval"])
    def test_06_final_integrity(self):
        self.assertEqual(checksum(POC/"BL05_P04_composite.png"),self.gpu["output_sha256"])
        with Image.open(POC/"BL05_P04_composite.png") as im:self.assertEqual(im.size,(1024,576))
    def test_07_outside_mask_exact_match(self):
        shot=Path.home()/"Documents"/"futureworks-p04-data"/"FWAI-M001_EP001_PREPRODUCTION"/"05_LOCAL_KEYFRAMES"/"S01"
        src=shot/"candidate_D4_env_crop"/"FWAI_EP001_S01_LOCAL_REFERENCE_CANDIDATE_1024x576.png"
        with Image.open(src) as a,Image.open(POC/"BL05_P04_composite.png") as b,Image.open(POC/"BL01_edit_mask.png") as mask:
            a=a.convert("RGB");b=b.convert("RGB"); m=mask.convert("L")
            self.assertEqual(a.size,b.size)
            ar,br,mr=a.load(),b.load(),m.load()
            outside=sum(1 for y in range(576) for x in range(1024) if mr[x,y]==0 and ar[x,y]!=br[x,y])
            self.assertEqual(outside,0)
    def test_08_review_triptych(self):
        with Image.open(POC/"BL01_P04_review_triptych.png") as im:
            self.assertEqual(im.size,(3072,576))
    def test_09_inventory_readonly(self):
        self.assertTrue(self.wlm["dry_run"])
        self.assertFalse(self.wlm["automatic_delete_enabled"])
        self.assertFalse(self.wlm["move_enabled"])
        self.assertGreater(self.wlm["file_count"],300)
        self.assertEqual(self.wlm["errors"],[])
    def test_10_duplicates_for_review_not_deletion(self):
        self.assertGreaterEqual(len(self.wlm["duplicate_groups"]),1)
        self.assertNotIn("delete_candidates",self.wlm)
    def test_11_scripts_no_destructive_calls(self):
        for fname in ("wlm01_inventory.py","blender_pose_plate.py","bl05_comfy_baseline.py"):
            code=(BASE/fname).read_text()
            ast.parse(code)
            for forbidden in ("shutil.rmtree(", "os.remove(", ".unlink(", "http://api.dev.runwayml.com", "https://api.dev.runwayml.com"):
                self.assertNotIn(forbidden,code)
    def test_12_reference_unchanged(self):
        src=Path.home()/"Documents"/"futureworks-p04-data"/"FWAI-M001_EP001_PREPRODUCTION"/"05_LOCAL_KEYFRAMES"/"S01"/"candidate_D4_env_crop"/"FWAI_EP001_S01_LOCAL_REFERENCE_CANDIDATE_1024x576.png"
        self.assertEqual(checksum(src),self.gpu["source_sha256"])
    def test_13_blender_rig_moves_actual_mesh(self):
        rigtest=BASE/"poc-bl04-rig-test"
        data=json.loads((rigtest/"BL01_pose_manifest.json").read_text())
        self.assertTrue(data["rig_drives_mesh_verified"])
        self.assertNotEqual(data["render_sha256"],data["variant_render_sha256"])
        self.assertEqual(checksum(rigtest/"BL01_mech_pose_variant.png"),data["variant_render_sha256"])
if __name__=="__main__":
    unittest.main(verbosity=2)
