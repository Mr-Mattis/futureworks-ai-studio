"""No-network, no-money static regression for pinned one-shot Runway pilot."""
import importlib.util,json,pathlib,unittest,ast
HERE=pathlib.Path(__file__).resolve().parent
REPO=HERE.parents[2]
EVIDENCE=REPO/"imaging/p04/evidence/P04_GPU_001.json"
def load():
    spec=importlib.util.spec_from_file_location("runway_three_clip_pilot",HERE/"runway_three_clip_pilot.py")
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m
class PilotContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=load()
    def test_owner_scope_limited(self):
        p=self.p
        self.assertEqual(p.MAX_TOTAL_CREDITS,500)
        self.assertEqual(p.EXPECTED_TOTAL_CREDITS,180)
        self.assertEqual(p.DURATION,5)
        self.assertEqual(p.RATIO,"1280:720")
        self.assertEqual(p.MODEL,"gen4.5")
        self.assertFalse(p.OWNER_APPROVAL["publish_authorized"])
        self.assertFalse(p.OWNER_APPROVAL["production_activation_authorized"])
        self.assertTrue(p.OWNER_APPROVAL["no_paid_retries"])
    def test_original_sha_source_locked(self):
        p=self.p
        data=json.loads(EVIDENCE.read_text())
        for scene,(asset_id,digest) in p.PINNED.items():
            a=[x for x in data["images"] if x["scene_id"]==scene and x["asset_id"]==asset_id]
            self.assertEqual(len(a),1)
            self.assertEqual(a[0]["sha256"],digest)
        self.assertEqual(len(set(x[1] for x in p.PINNED.values())),3)
    def test_prompt_limited_and_explicit_material_realism(self):
        p=self.p
        self.assertEqual(set(p.PROMPTS),set(p.PINNED))
        for prompt in p.PROMPTS.values():
            self.assertLess(len(prompt),1000)
            self.assertIn("metal",prompt)
            self.assertIn("No text",prompt)
    def test_submit_uses_durable_attempt_before_one_post(self):
        src=(HERE/"runway_three_clip_pilot.py").read_text()
        tree=ast.parse(src)
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="submit")
        body=ast.get_source_segment(src,fn)
        self.assertIn('row.update({"state":"submission_attempted"',body)
        self.assertIn('save(OUT/"pilot-journal.json",state)',body)
        self.assertIn('response=api("POST","/v1/image_to_video",payload)',body)
        self.assertLess(body.index('"submission_attempted"'),body.index('response=api("POST"'))
        self.assertEqual(body.count('response=api("POST"'),1)
    def test_readonly_prepare_never_uploads(self):
        src=(HERE/"runway_three_clip_pilot.py").read_text()
        tree=ast.parse(src)
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="begin")
        self.assertNotIn('api("POST"',ast.get_source_segment(src,fn))
if __name__=="__main__":unittest.main()
