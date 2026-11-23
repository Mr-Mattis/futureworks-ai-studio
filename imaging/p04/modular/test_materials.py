"""P04.06 material look-development: no-network contract regression tests.

Owner specifically authorized LOCAL GPU material rendering for FWAI-T001,
not environments, paid APIs, external uploads, production or publishing.
"""
import ast,hashlib,json,pathlib,re,unittest
HERE=pathlib.Path(__file__).resolve().parent
REPO=HERE.parents[2]
GEO=HERE/"FWAI-T001_geometry_spec.json"
AP=HERE/"FWAI-T001_owner_acceptance.json"
MA=HERE/"FWAI-T001_mechanical_owner_acceptance.json"
SOURCE=HERE/"material_source.py"
GPU=HERE/"material_gpu.py"
EXPECTED_G="7bc0379c02632018e78dfbea6eab467071ec0ffe9f97b3c9522c1634bf51b77e"
EXPECTED_M="07dc8ea721e2d2d69d47585bc67268c31a2ceb9d96e0724a5ffc55fd17465c5f"
class MaterialContractTests(unittest.TestCase):
 def test_geometry_source_matches_owner_acceptance(self):
  owner=json.loads(AP.read_text())
  self.assertEqual(hashlib.sha256(GEO.read_bytes()).hexdigest(),EXPECTED_G)
  self.assertEqual(owner["spec_sha256"],EXPECTED_G)
  self.assertEqual(owner["owner_decisions"]["P04.06-GEOMETRY"],"APPROVE")
 def test_mechanical_approval_exact_hash(self):
  owner=json.loads(MA.read_text())
  self.assertEqual(owner["mechanical_detail_sha256"],EXPECTED_M)
  self.assertEqual(owner["owner_decisions"]["P04.06-MECHANICAL"],"APPROVE")
  self.assertEqual(owner["owner_decisions"]["EXTERNAL_UPLOAD"],"NOT_AUTHORIZED")
  self.assertEqual(owner["owner_decisions"]["PUBLISH"],"NOT_AUTHORIZED")
 def test_render_isolated_subject_and_immutable_geometry(self):
  s=SOURCE.read_text()
  self.assertIn('g["environment"] is None',s)
  self.assertIn("APPROVED_G",s)
  self.assertIn("APPROVED_M",s)
  self.assertIn('neutral',GPU.read_text().lower())
  self.assertIn('"environment":None',s)
  self.assertIn("six",GPU.read_text().lower())
 def test_gpu_uses_only_loopback_comfy_and_pinned_models(self):
  s=GPU.read_text()
  self.assertIn('API="http://127.0.0.1:8188"',s)
  self.assertIn("c48bfd159cd7a6507b128685e963c398fa72399cefafaf603781df50ce836cc7",s)
  self.assertIn("735e4c3a447a3255760d7f86845f09f937809baa529c17370d83e4c3758f3c75",s)
  self.assertIn("37f9a931c215f040aa6d50f711f2cb115f713c46df1d0d6469a8bd7bfe9a60bb",s)
  self.assertNotIn("api.dev.runwayml.com",s)
  self.assertNotIn("openai.com",s)
 def test_durable_resubmission_refusal(self):
  s=GPU.read_text()
  self.assertIn('row["state"]="submitting"',s)
  self.assertIn('if row["state"]!="submitted"',s)
  self.assertLess(s.index('row["state"]="submitting"'),s.index('receipt=req("/prompt"'))
  self.assertIn("no blind retries",s)
 def test_only_two_review_variants_and_no_scene(self):
  for s in (GPU.read_text(),SOURCE.read_text()):
   ast.parse(s)
  self.assertEqual(GPU.read_text().count('"graphite_alloy"'),1)
  self.assertEqual(GPU.read_text().count('"ceramic_titanium"'),1)
  self.assertIn('"external_upload_authorized":False',SOURCE.read_text())
  self.assertIn('"human_visual_approval":False',SOURCE.read_text())
 def test_final_output_1920x1080(self):
  s=GPU.read_text()
  self.assertIn('"width":1920,"height":1080',s)
  self.assertIn('if image.size!=(1920,1080)',s)
  self.assertIn('row.update({"state":"complete"',s)
if __name__=="__main__":unittest.main()
