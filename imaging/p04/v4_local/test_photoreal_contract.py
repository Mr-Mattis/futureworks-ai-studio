"""Offline, no model-loading or provider calls, V4 photo-real acceptance contract tests."""
import ast,json,pathlib,unittest
HERE=pathlib.Path(__file__).resolve().parent
REPO=HERE.parents[2]
SRC=(HERE/"generate_v4_photoreal_ab.py").read_text()
EVIDENCE=json.loads((REPO/"imaging/p04/evidence/P04_V4_PHOTOREAL_AB_VERIFICATION.json").read_text())
class PhotorealContract(unittest.TestCase):
 def test_explicit_credible_material_detail_target(self):
    required=("tread","hydraulic","bolts","weld seams","gaskets","weathered","scratches","grease","documentary","realistic")
    for detail in required:
        self.assertIn(detail,SRC.lower(),detail)
 def test_pinned_checkpoint_vae_upscaler(self):
    catalog=EVIDENCE["models"]
    self.assertEqual(catalog["base_sha256"],"c48bfd159cd7a6507b128685e963c398fa72399cefafaf603781df50ce836cc7")
    self.assertEqual(catalog["vae_sha256"],"735e4c3a447a3255760d7f86845f09f937809baa529c17370d83e4c3758f3c75")
    self.assertEqual(catalog["upscale_sha256"],"37f9a931c215f040aa6d50f711f2cb115f713c46df1d0d6469a8bd7bfe9a60bb")
    self.assertIn("openrail",catalog["base_license"])
 def test_alternative_paths_and_owned_review(self):
    assets=EVIDENCE["assets"]
    self.assertEqual(len(assets),4)
    names={x["asset"] for x in assets}
    self.assertEqual(names,{"V4_A_NATIVE","V4_B_NATIVE","V4_A_ESRGAN_1080P","V4_B_ESRGAN_1080P"})
    self.assertEqual(EVIDENCE["owner_visual_approval"],"PENDING")
    self.assertFalse(EVIDENCE["production_approved"])
    self.assertFalse(EVIDENCE["publish_authorized"])
    self.assertEqual(EVIDENCE["paid_calls"],0)
 def test_generation_code_local_only_and_no_blind_retry(self):
    ast.parse(SRC)
    self.assertIn('API="http://127.0.0.1:8188"',SRC)
    self.assertNotIn("runwayml.com",SRC)
    self.assertIn('row["state"]="submitting"',SRC)
    self.assertIn("ambiguous receipt, manual reconciliation",SRC)
    self.assertIn("Model SHA mismatch",SRC)
if __name__=="__main__":unittest.main()
