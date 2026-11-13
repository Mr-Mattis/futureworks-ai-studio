#!/usr/bin/env python3
"""Offline acceptance tests; fixtures are synthetic, not agent executions."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
from validate_agent_result import ROOT, DEFAULT_MANIFEST_DIR, load_json, validate

MANIFEST = DEFAULT_MANIFEST_DIR / 'example.valid.json'
BASE = load_json(ROOT / 'agent_result.json')

class ContractTests(unittest.TestCase):
    def test_schema(self):
        Draft202012Validator.check_schema(load_json(ROOT / 'agent_result.schema.json'))

    def test_all_ten_live_roles(self):
        roles = load_json(ROOT / 'agent-registry.json')
        self.assertEqual(len(roles), 10)
        for agent in roles:
            with self.subTest(role=agent['key']):
                result = load_json(ROOT / 'examples' / (agent['key'] + '.json'))
                before = copy.deepcopy(result)
                self.assertEqual(validate(result, MANIFEST), [])
                self.assertEqual(result, before)
                self.assertEqual(result['output'], load_json(ROOT / 'payload-fixtures.json')[agent['key']])

    def test_two_studio_roles(self):
        for role in ('growth_strategist', 'sop_knowledge'):
            with self.subTest(role=role):
                r = load_json(ROOT / 'examples' / (role + '.studio.json'))
                self.assertEqual(validate(r), [])
                self.assertTrue(validate(r, MANIFEST))

    def test_terminal_statuses(self):
        for status in ('failed', 'blocked', 'needs_revision'):
            with self.subTest(status=status):
                r = copy.deepcopy(BASE)
                r['execution']['status'] = status
                if status == 'failed':
                    r['output'] = None
                    r['errors'] = [{'code':'test-error','message':'Synthetic failure','retryable':True,'details':{}}]
                    r['validation']['status'] = 'not_run'
                elif status == 'blocked':
                    r['output'] = None
                    r['blockers'] = ['Synthetic missing input']
                    r['validation']['status'] = 'not_run'
                else:
                    r['validation'] = {'status':'failed','findings':[{'code':'test-finding','severity':'error','message':'Synthetic revision needed','path':'/output','scene_id':'S01'}]}
                self.assertEqual(validate(r, MANIFEST), [])

    def test_invalid_results(self):
        mutations = {
            'unknown_version': lambda r: r.update(schema_version='2.0.0'),
            'unknown_envelope_field': lambda r: r.update(typo=True),
            'missing_identity': lambda r: r.pop('agent'),
            'unknown_role': lambda r: r['agent'].update(role='not_an_agent'),
            'wrong_instance': lambda r: r['agent'].update(instance_id='wrong-instance'),
            'missing_manifest': lambda r: r.update(input_manifest=None),
            'wrong_project': lambda r: r['input_manifest'].update(project_id='OTHER-EPISODE'),
            'wrong_revision': lambda r: r['input_manifest'].update(revision=99),
            'wrong_hash': lambda r: r['input_manifest'].update(sha256='0'*64),
            'wrong_manifest_version': lambda r: r['input_manifest'].update(schema_version='2.0.0'),
            'studio_scope_wrong_role': lambda r: r.update(scope='studio',input_manifest=None),
            'missing_role_payload_field': lambda r: r['output'].pop('scenes'),
            'wrong_role_payload_type': lambda r: r['output'].update(scenes='not an array'),
            'wrong_output_project': lambda r: r['output'].update(project_id='OTHER-EPISODE'),
            'unknown_scene': lambda r: r['output']['scenes'][0].update(scene_id='S99'),
            'bad_scene_type': lambda r: r['output']['scenes'][0].update(scene_id=[]),
            'bad_timestamp': lambda r: r['execution'].update(started_at='yesterday'),
            'time_reversed': lambda r: r['execution'].update(finished_at='2026-11-09T04:00:00Z'),
            'attempt_zero': lambda r: r['execution'].update(attempt=0),
            'success_null_output': lambda r: r.update(output=None),
            'success_unvalidated': lambda r: r['validation'].update(status='not_run'),
            'success_error': lambda r: r['errors'].append({'code':'test-error','message':'Failure','retryable':False,'details':{}}),
            'success_blocker': lambda r: r['blockers'].append('Blocked'),
            'passed_with_error_finding': lambda r: r['validation']['findings'].append({'code':'test-error','severity':'error','message':'Error','path':'','scene_id':None}),
            'failed_without_error': lambda r: (r['execution'].update(status='failed'),r.update(output=None)),
            'blocked_without_reason': lambda r: r['execution'].update(status='blocked'),
            'revision_without_findings': lambda r: (r['execution'].update(status='needs_revision'),r['validation'].update(status='failed')),
            'spending': lambda r: r['authorization'].update(spend_authorized=True),
            'publishing': lambda r: r['authorization'].update(publish_authorized=True),
            'production_approval': lambda r: r['authorization'].update(production_approved=True),
            'nonfinite': lambda r: r['output'].update(untrusted_number=float('nan')),
        }
        for name, mutate in mutations.items():
            with self.subTest(case=name):
                r = copy.deepcopy(BASE)
                mutate(r)
                self.assertTrue(validate(r, MANIFEST), name)

    def test_missing_manifest_file(self):
        self.assertTrue(validate(BASE))
        self.assertTrue(validate(BASE, ROOT / 'missing.json'))

    def test_manifest_invariants_and_file_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'manifest.json'
            for name in ['example.valid.json'] + [p.name for p in DEFAULT_MANIFEST_DIR.glob('example.invalid.*.json')]:
                with self.subTest(manifest=name):
                    path.write_bytes((DEFAULT_MANIFEST_DIR / name).read_bytes())
                    r = copy.deepcopy(BASE)
                    r['input_manifest']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
                    errors = validate(r, path)
                    self.assertEqual(bool(errors), name != 'example.valid.json')
            # Same project/revision but changed bytes must not reuse the old result.
            path.write_bytes(MANIFEST.read_bytes() + b'\n')
            self.assertTrue(validate(BASE, path))

    def test_dependency_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            for name in load_json(ROOT / 'manifest-dependency.json')['sha256']:
                (target / name).write_bytes((DEFAULT_MANIFEST_DIR / name).read_bytes())
            with (target / 'production_manifest.schema.json').open('a') as out:
                out.write('\n')
            self.assertTrue(validate(BASE, MANIFEST, target))

    def test_strict_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'bad.json'
            for text in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', '{'):
                with self.subTest(text=text):
                    p.write_text(text)
                    with self.assertRaises(ValueError):
                        load_json(p)

    def test_cli_exit_codes(self):
        cmd = [sys.executable, str(ROOT / 'validate_agent_result.py')]
        good = subprocess.run(cmd + [str(ROOT / 'agent_result.json'), '--manifest',str(MANIFEST)],capture_output=True)
        self.assertEqual(good.returncode,0,good.stdout)
        bad = subprocess.run(cmd + [str(ROOT / 'agent_result.json')],capture_output=True)
        self.assertEqual(bad.returncode,1)
        missing = subprocess.run(cmd + [str(ROOT / 'missing.json')],capture_output=True)
        self.assertEqual(missing.returncode,2)

if __name__ == '__main__':
    unittest.main(verbosity=2)
