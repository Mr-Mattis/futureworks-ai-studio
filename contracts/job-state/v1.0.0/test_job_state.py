import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
from jsonschema import Draft202012Validator
from job_state import (ROOT, SPEC, STATES, EDGES, SCHEMA, RECEIPT_SCHEMA,
                       create_draft, transition, validate_snapshot, TransitionRejected)

MANIFEST_DIR = Path('/home/mattis983/futureworks-studio/futureworks-ai-studio/contracts/production-manifest/v1.0.0')
MANIFEST_FILE = MANIFEST_DIR / 'example.valid.json'
M = json.loads(MANIFEST_FILE.read_text())
REF = {k:M[k] for k in ('schema_version','project_id','revision')}
REF['sha256'] = hashlib.sha256(MANIFEST_FILE.read_bytes()).hexdigest()


def fixtures():
    receipts = {}
    for gate, kind in SPEC['receipt_types'].items():
        rid = 'synthetic-' + gate
        receipts[rid] = {'receipt_id':rid,'job_id':'SYNTHETIC-JOB-001','manifest_ref':copy.deepcopy(REF),
                         'gate':gate,'type':kind,'decision':'passed',
                         'actor':{'id':'synthetic-test-actor','kind':'owner' if kind=='human_approval' else 'service'},
                         'evidence_reference':'fixture-only:no-real-action'}
    snapshots = [create_draft('SYNTHETIC-JOB-001', REF)]
    for dest in STATES[1:]:
        current = snapshots[-1]
        evidence = {g:'synthetic-'+g for g in EDGES[(current['state'],dest)]}
        snapshots.append(transition(current,dest,expected_version=current['state_version'],
                                    manifest_ref=REF,evidence=evidence,resolve_receipt=receipts.get))
    return receipts, snapshots


class StateTests(unittest.TestCase):
    def setUp(self):
        self.receipts, self.snapshots = fixtures()

    def advance(self, i=0, **overrides):
        job = self.snapshots[i]
        args = {'expected_version':i,'manifest_ref':REF,
                'evidence':{g:'synthetic-'+g for g in EDGES[(STATES[i],STATES[i+1])]},
                'resolve_receipt':self.receipts.get}
        args.update(overrides)
        return transition(job, STATES[i+1], **args)

    def test_schemas(self):
        Draft202012Validator.check_schema(SCHEMA)
        Draft202012Validator.check_schema(RECEIPT_SCHEMA)

    def test_manifest_contract_compatibility(self):
        spec = importlib.util.spec_from_file_location('manifest', MANIFEST_DIR/'validate_manifest.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.validate(json.loads((MANIFEST_DIR/'production_manifest.schema.json').read_text()), M), [])
        # The same exact ref used by the P01.02 canonical agent result.
        agent_path = MANIFEST_DIR.parents[1]/'agent-result/v1.0.0/agent_result.json'
        self.assertEqual(json.loads(agent_path.read_text())['input_manifest'], REF)

    def test_complete_path_retains_identifiers(self):
        self.assertEqual([j['state'] for j in self.snapshots], STATES)
        for i,j in enumerate(self.snapshots):
            validate_snapshot(j)
            self.assertEqual(j['manifest_ref'], REF)
            self.assertEqual(j['job_id'], 'SYNTHETIC-JOB-001')
            self.assertEqual(j['state_version'], i)

    def test_all_100_state_pairs(self):
        for i, job in enumerate(self.snapshots):
            for target in STATES:
                with self.subTest(source=job['state'],target=target):
                    gates = EDGES.get((job['state'],target),[])
                    args = dict(expected_version=i,manifest_ref=REF,evidence={g:'synthetic-'+g for g in gates},resolve_receipt=self.receipts.get)
                    if (job['state'],target) in EDGES:
                        self.assertEqual(transition(job,target,**args)['state'],target)
                    else:
                        with self.assertRaises(TransitionRejected):transition(job,target,**args)

    def test_each_gate_is_required(self):
        for i in range(9):
            for g in EDGES[(STATES[i],STATES[i+1])]:
                with self.subTest(state=STATES[i],gate=g):
                    evidence={k:'synthetic-'+k for k in EDGES[(STATES[i],STATES[i+1])] if k!=g}
                    with self.assertRaises(TransitionRejected):self.advance(i,evidence=evidence)

    def test_receipts_fail_closed(self):
        changes = {
            'wrong_job':lambda r:r.update(job_id='another-job'),
            'wrong_revision':lambda r:r['manifest_ref'].update(revision=999),
            'wrong_hash':lambda r:r['manifest_ref'].update(sha256='0'*64),
            'wrong_project':lambda r:r['manifest_ref'].update(project_id='OTHER-001'),
            'wrong_gate':lambda r:r.update(gate='research_complete'),
            'wrong_id':lambda r:r.update(receipt_id='wrong-id'),
            'wrong_type':lambda r:r.update(type='human_approval'),
            'failed':lambda r:r.update(decision='failed'),
            'pending':lambda r:r.update(decision='pending'),
            'revoked':lambda r:r.update(decision='revoked'),
            'agent_self_attestation':lambda r:r['actor'].update(kind='agent'),
            'missing_evidence':lambda r:r.pop('evidence_reference'),
        }
        for name,mutate in changes.items():
            with self.subTest(case=name):
                receipts=copy.deepcopy(self.receipts)
                mutate(receipts['synthetic-brief_validated'])
                with self.assertRaises(TransitionRejected):self.advance(resolve_receipt=receipts.get)

    def test_human_gates_reject_services_and_agents(self):
        for i,gate in [(3,'human_production_approval'),(8,'owner_publish_approval')]:
            for kind in ['service','agent']:
                with self.subTest(gate=gate,actor=kind):
                    receipts=copy.deepcopy(self.receipts)
                    receipts['synthetic-'+gate]['actor']['kind']=kind
                    with self.assertRaises(TransitionRejected):self.advance(i,resolve_receipt=receipts.get)

    def test_publishing_needs_confirmation_not_just_approval(self):
        with self.assertRaises(TransitionRejected):
            self.advance(8,evidence={'owner_publish_approval':'synthetic-owner_publish_approval'})

    def test_stale_version_and_revision_changes(self):
        for version in [-1,99,True,'0']:
            with self.subTest(version=version):
                with self.assertRaises(TransitionRejected):self.advance(expected_version=version)
        for field,value in [('revision',2),('sha256','0'*64),('project_id','OTHER-001'),('schema_version','2.0.0')]:
            ref=copy.deepcopy(REF);ref[field]=value
            with self.subTest(field=field):
                with self.assertRaises(TransitionRejected):self.advance(manifest_ref=ref)

    def test_malformed_history(self):
        mutations=[lambda j:j.update(state='published'),lambda j:j.update(state_version=99),
                   lambda j:j['history'][0].update(sequence=2),lambda j:j['history'][0].update(to='planned'),
                   lambda j:j['history'][0].update(evidence={}),lambda j:j.update(unknown=True)]
        for i,mutate in enumerate(mutations):
            with self.subTest(case=i):
                j=copy.deepcopy(self.snapshots[1]);mutate(j)
                with self.assertRaises(TransitionRejected):validate_snapshot(j)

    def test_no_mutation_on_success_or_failure(self):
        before=copy.deepcopy(self.snapshots); receipts=copy.deepcopy(self.receipts)
        out=self.advance()
        out['manifest_ref']['revision']=99
        self.assertEqual(self.snapshots,before)
        with self.assertRaises(TransitionRejected):self.advance(evidence={})
        self.assertEqual(self.snapshots,before)
        self.assertEqual(self.receipts,receipts)

    def test_resolver_required_and_unavailable(self):
        for resolver in [None,lambda _:None,lambda _:True]:
            with self.subTest(resolver=str(resolver)):
                with self.assertRaises(TransitionRejected):self.advance(resolve_receipt=resolver)
        def broken(_):raise RuntimeError('Unavailable')
        with self.assertRaises(TransitionRejected):self.advance(resolve_receipt=broken)
        with self.assertRaises(TransitionRejected):self.advance(evidence={'brief_validated':True})

if __name__=='__main__':unittest.main(verbosity=2)
