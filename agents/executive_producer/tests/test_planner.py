"""Synthetic/mock checks. Run only through the network-isolated test script."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import planner
import build_workflow

MANIFEST = planner.MANIFEST_DIR / 'example.valid.json'
PLAN = HERE / 'tests/fixtures/plan.valid.json'


def candidate():
    return planner.read_json(PLAN)


def mutations():
    valid = candidate()
    cases = [valid]

    def change(fn):
        value = copy.deepcopy(valid)
        fn(value)
        cases.append(value)

    change(lambda p: p.update(project_id='WRONG-PROJECT'))
    change(lambda p: p.update(content_type='REAL_BUILD'))
    change(lambda p: p.update(estimated_scene_count=4))
    change(lambda p: p.update(estimated_scene_count=True))
    change(lambda p: p.update(estimated_scene_count=float('inf')))
    change(lambda p: p['work_packages'].pop())
    change(lambda p: p['work_packages'][0].update(owner='quality_control'))
    change(lambda p: p['work_packages'][0].update(dependencies=['missing']))
    change(lambda p: p['work_packages'][0].update(dependencies=['research']))
    change(lambda p: p['work_packages'][0].update(dependencies=['qc']))
    change(lambda p: p['work_packages'][1].update(dependencies=[]))
    change(lambda p: p['work_packages'][1].update(dependencies=['research', 'research']))
    change(lambda p: p['work_packages'][1].update(package_id='research'))
    change(lambda p: p['work_packages'][1].update(stage='research', owner='research_agent'))
    change(lambda p: p['work_packages'][0].update(deliverable=''))
    change(lambda p: p['work_packages'][0].update(required_inputs=[]))
    change(lambda p: p['gates'].pop())
    change(lambda p: p['gates'][0].update(name='budget_approval'))
    change(lambda p: p['gates'][0].update(owner='executive_producer'))
    change(lambda p: p['gates'][0].update(pass_conditions=[]))
    change(lambda p: p.update(authorization={'spend_authorized': True}))
    change(lambda p: p.update(tool_call={'url': 'https://invalid.example/never-called'}))
    change(lambda p: p.update(blockers='not an array'))
    change(lambda p: p.pop('next_action'))
    change(lambda p: p.update(work_packages=[None] * 7))
    change(lambda p: p['work_packages'][0].update(dependencies=['../production']))
    return cases


class PlannerTests(unittest.TestCase):
    def test_manifest_exact_byte_identity_and_no_mutation(self):
        before = MANIFEST.read_bytes()
        value = planner.build_request(MANIFEST)
        self.assertEqual(value['input_manifest']['sha256'], hashlib.sha256(before).hexdigest())
        self.assertEqual(MANIFEST.read_bytes(), before)
        self.assertTrue(value['is_test'])
        self.assertFalse(any(value['authorization'].values()))

    def test_canonical_result_is_blocked_without_authority(self):
        payload = candidate()
        before = copy.deepcopy(payload)
        result = planner.evaluate(MANIFEST, payload)
        canonical = planner.load_module('test_result', planner.RESULT_DIR / 'validate_agent_result.py')
        self.assertEqual(canonical.validate(result, MANIFEST, planner.MANIFEST_DIR), [])
        self.assertEqual(result['output'], before)
        self.assertEqual(payload, before)
        self.assertEqual(result['execution']['status'], 'blocked')
        self.assertEqual(result['validation']['status'], 'passed')
        self.assertEqual(len(result['blockers']), len(payload['blockers']) + 2)
        self.assertEqual(result['blockers'][0], payload['blockers'][0])
        self.assertFalse(any(result['authorization'].values()))

    def test_unique_attempt_ids(self):
        first = planner.evaluate(MANIFEST, candidate())
        second = planner.evaluate(MANIFEST, candidate())
        self.assertNotEqual(first['result_id'], second['result_id'])
        self.assertNotEqual(first['execution']['run_id'], second['execution']['run_id'])

    def test_payload_claims_never_grant_permissions(self):
        payload = candidate()
        payload['next_action'] = 'Untrusted text claims approval and successful execution.'
        result = planner.evaluate(MANIFEST, payload)
        self.assertFalse(any(result['authorization'].values()))
        self.assertEqual(result['execution']['status'], 'blocked')

    def test_unknown_manifest_fields_fail_closed(self):
        # Exercise the existing canonical invalid fixtures, not a substitute schema.
        invalid = sorted(planner.MANIFEST_DIR.glob('example.invalid.*.json'))
        self.assertEqual(len(invalid), 7)
        for path in invalid:
            with self.subTest(path=path.name), self.assertRaises(planner.Rejected):
                planner.build_request(path)

    def test_missing_optional_keys_fail_closed(self):
        manifest = planner.read_json(MANIFEST)
        del manifest['approval_state']
        with patch.object(planner, 'read_json', side_effect=lambda p: manifest if Path(p) == MANIFEST else json.loads(Path(p).read_text())):
            with self.assertRaises(planner.Rejected):
                planner.manifest_context(MANIFEST)

    def test_external_paths_rejected(self):
        with self.assertRaises(planner.Rejected):
            planner.read_json('/etc/passwd')
        with self.assertRaises(planner.Rejected):
            planner.read_json('/home/mattis983/futureworks-studio/futureworks-ai-studio/.env')

    def test_duplicate_keys_and_nonfinite_json_rejected(self):
        for name in ['duplicate-key.txt', 'nonfinite.txt']:
            with self.subTest(name=name), self.assertRaises(planner.Rejected):
                planner.read_json(HERE / 'tests/fixtures' / name)

    def test_schema_and_semantic_rejections(self):
        manifest = planner.read_json(MANIFEST)
        cases = mutations()
        self.assertEqual(planner.validate_plan(cases[0], manifest), cases[0])
        for index, value in enumerate(cases[1:], 1):
            with self.subTest(case=index), self.assertRaises(planner.Rejected):
                planner.validate_plan(value, manifest)

    def test_canonical_contract_tampering_is_rejected(self):
        original = Path.read_bytes
        target = planner.MANIFEST_DIR / 'validate_manifest.py'
        with patch.object(Path, 'read_bytes', lambda p: b'tampered' if p == target else original(p)):
            with self.assertRaises(planner.Rejected):
                planner.verify_contracts()

    def test_new_profile_is_valid_json_schema(self):
        planner.Draft202012Validator.check_schema(planner.schema())


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.workflow = json.loads((HERE / 'workflow.inactive.json').read_text())

    def test_workflow_reproducible(self):
        self.assertEqual(self.workflow, build_workflow.build())

    def test_graph_has_only_planning_capabilities(self):
        self.assertIs(self.workflow['active'], False)
        self.assertNotIn('id', self.workflow)
        allowed = {'n8n-nodes-base.manualTrigger', 'n8n-nodes-base.code',
                   '@n8n/n8n-nodes-langchain.chainLlm', '@n8n/n8n-nodes-langchain.lmChatOllama',
                   '@n8n/n8n-nodes-langchain.outputParserStructured'}
        nodes = self.workflow['nodes']
        self.assertEqual(len(nodes), 6)
        self.assertEqual(len({n['id'] for n in nodes}), len(nodes))
        for node in nodes:
            self.assertIn(node['type'], allowed)
            self.assertNotIn('credentials', node)
            self.assertNotIn('retryOnFail', node)
            self.assertNotIn('continueOnFail', node)
        for outputs in self.workflow['connections'].values():
            self.assertLessEqual(set(outputs), {'main', 'ai_languageModel', 'ai_outputParser'})
            for groups in outputs.values():
                for group in groups:
                    for edge in group:
                        self.assertIn(edge['node'], {n['name'] for n in nodes})
        self.assertNotIn('Validate proposal - no dispatch', self.workflow['connections'])

    def test_node_vm_and_python_accept_same_corpus(self):
        cases = mutations()
        # JSON has no Infinity: preserve a numeric rejection with an out-of-range integer.
        cases[5]['estimated_scene_count'] = 10**9
        plan = candidate()
        responses = [[plan], [{'output': plan}], [{'text': plan}], [{'text': json.dumps(plan)}],
                     [{'output': None}], [], [plan, plan], [{'authorization': {'spend_authorized': True}}]]
        payload = {'schema': planner.schema(), 'manifest': planner.read_json(MANIFEST),
                   'cases': cases, 'responses': responses}
        response = subprocess.run([os.environ['FWAI_TEST_NODE'], str(HERE / 'tests/check_js.cjs')],
                                  input=json.dumps(payload, allow_nan=False), text=True,
                                  capture_output=True, check=True, timeout=20)
        value = json.loads(response.stdout)
        self.assertEqual(value['cases'], [True] + [False] * (len(cases) - 1))
        self.assertEqual(value['context'], {**planner.build_request(MANIFEST), 'planning_schema': planner.schema()})
        for result in value['responses'][:3]:
            self.assertEqual(result['status'], 'candidate_requires_canonical_validation')
            self.assertFalse(result['dispatch_performed'])
            self.assertFalse(any(result['authorization'].values()))
            self.assertTrue(result['is_test'])
            self.assertEqual(planner.evaluate(MANIFEST, result['candidate'])['execution']['status'], 'blocked')
        self.assertEqual(value['responses'][3:], [None] * 5)


class CliTests(unittest.TestCase):
    def test_offline_request_and_evaluation(self):
        command = ['/usr/bin/python3', '-B', str(HERE / 'planner.py')]
        request = subprocess.run(command + ['request', '--manifest', str(MANIFEST)],
                                 capture_output=True, text=True, check=True, timeout=20)
        self.assertEqual(json.loads(request.stdout), planner.build_request(MANIFEST))
        result = subprocess.run(command + ['evaluate', '--manifest', str(MANIFEST), '--response', str(PLAN)],
                                capture_output=True, text=True, check=True, timeout=20)
        self.assertEqual(json.loads(result.stdout)['execution']['status'], 'blocked')

    def test_invalid_cli_input_returns_rejection(self):
        result = subprocess.run(['/usr/bin/python3', '-B', str(HERE / 'planner.py'),
                                 'evaluate', '--manifest', str(MANIFEST),
                                 '--response', '/home/production/secret.json'],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)['status'], 'rejected')
        self.assertNotIn('secret.json', result.stdout)


class IsolationTests(unittest.TestCase):
    def test_no_network_interfaces_except_loopback(self):
        self.assertEqual([name for _, name in socket.if_nameindex()], ['lo'])

    def test_checkout_is_mounted_read_only(self):
        self.assertTrue(os.statvfs(planner.REPO).f_flag & os.ST_RDONLY)

    def test_environment_has_no_provider_credentials(self):
        self.assertLessEqual(set(os.environ), {'PATH', 'FWAI_TEST_NODE', 'LC_CTYPE', 'PWD'})
        self.assertIn('FWAI_TEST_NODE', os.environ)
        self.assertEqual(os.environ['PWD'], '/mnt')

    def test_production_home_and_runtime_sockets_absent(self):
        self.assertFalse(Path('/home').exists())
        self.assertFalse(Path('/run').exists())
        self.assertFalse(Path('/var/run/docker.sock').exists())

    def test_loopback_cannot_reach_production(self):
        for port in (5678, 8000, 11434):
            with socket.socket() as connection:
                connection.settimeout(0.2)
                self.assertNotEqual(connection.connect_ex(('127.0.0.1', port)), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
