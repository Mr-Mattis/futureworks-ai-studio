#!/usr/bin/env python3
import json,pathlib,unittest
from jsonschema import Draft202012Validator
from validate_manifest import validate
ROOT=pathlib.Path(__file__).parent
schema=json.loads((ROOT/'production_manifest.schema.json').read_text())

class ManifestTests(unittest.TestCase):
 def test_schema_is_valid(self):
  Draft202012Validator.check_schema(schema)
 def test_valid_five_scene_episode(self):
  example=json.loads((ROOT/'example.valid.json').read_text())
  self.assertEqual(len(example['scenes']),5)
  self.assertEqual(sum(s['duration_seconds'] for s in example['scenes']),360)
  self.assertEqual(validate(schema,example),[])
 def test_invalid_cases_rejected(self):
  files=sorted(ROOT.glob('example.invalid.*.json'))
  self.assertEqual(len(files),7)
  for path in files:
   with self.subTest(case=path.name):
    errors=validate(schema,json.loads(path.read_text()))
    self.assertTrue(errors,'Expected rejection: '+path.name)
 def test_live_worker_boundary(self):
  example=json.loads((ROOT/'example.valid.json').read_text())
  self.assertEqual(len(example['scenes']),5)
  self.assertTrue(any(s['duration_seconds'] not in (5,10) for s in example['scenes']))
  # Do not silently map a 360-second production manifest to legacy /jobs.
  self.assertNotIn('mode',example)

if __name__=='__main__':unittest.main(verbosity=2)
