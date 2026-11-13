"""Validate captured live n8n storage evidence; performs no writes or API calls."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parent
CONTRACTS=Path('/home/mattis983/futureworks-studio/futureworks-ai-studio/contracts')
def read(name):return json.loads((ROOT/name).read_text())
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

class StorageEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.expected=read('test-records.json')
        self.actual={k:v['rows'][0] for k,v in read('live-readback.json').items()}

    def test_all_six_tables_and_exact_columns(self):
        definitions=read('table-definitions.json')['tables'];registry=read('table-registry.json')
        inventory={t['id']:t for t in read('live-table-inventory.json')['data']}
        self.assertEqual(set(definitions),{'production_jobs','scene_assets','provider_jobs','costs','approvals','errors'})
        self.assertEqual(len({v['id'] for v in registry['tables'].values()}),6)
        for key,d in definitions.items():
            with self.subTest(table=key):
                t=inventory[registry['tables'][key]['id']]
                self.assertEqual(t['name'],d['name'])
                self.assertEqual(t['projectId'],registry['project_id'])
                self.assertEqual({c['name']:c['type'] for c in t['columns']},{c['name']:c['type'] for c in d['columns']})

    def test_exact_roundtrip_and_native_metadata(self):
        for key,expected in self.expected.items():
            with self.subTest(table=key):
                self.assertEqual(read('live-readback.json')[key]['count'],1)
                row=self.actual[key]
                self.assertEqual({k:row[k] for k in expected},expected)
                self.assertIsInstance(row['id'],int)
                self.assertTrue(row['createdAt']);self.assertTrue(row['updatedAt'])

    def test_manifest_and_job_contracts(self):
        row=self.actual['production_jobs'];manifest=json.loads(row['manifest_json'])
        self.assertEqual(hashlib.sha256(row['manifest_json'].encode()).hexdigest(),row['manifest_sha256'])
        self.assertEqual(row['manifest_json'],(ROOT/'test-production-manifest.json').read_text())
        mp=CONTRACTS/'production-manifest/v1.0.0'
        validator=module('manifest_validator',mp/'validate_manifest.py')
        self.assertEqual(validator.validate(json.loads((mp/'production_manifest.schema.json').read_text()),manifest),[])
        snapshot=json.loads(row['snapshot_json'])
        module('job_state',CONTRACTS/'job-state/v1.0.0/job_state.py').validate_snapshot(snapshot)
        self.assertEqual(snapshot['job_id'],row['job_id'])
        self.assertEqual(snapshot['state'],row['state'])
        self.assertEqual(snapshot['state_version'],row['state_version'])
        self.assertEqual(snapshot['manifest_ref']['revision'],row['manifest_revision'])
        self.assertEqual(snapshot['manifest_ref']['sha256'],row['manifest_sha256'])

    def test_relationships_and_scene_reference(self):
        job=self.actual['production_jobs'];provider=self.actual['provider_jobs']
        for key,row in self.actual.items():
            with self.subTest(table=key):
                for field in ('job_id','project_id','manifest_revision','manifest_sha256','test_run_id'):
                    self.assertEqual(row[field],job[field])
        for key in ('scene_assets','costs','errors'):
            self.assertEqual(self.actual[key]['provider_job_record_id'],provider['record_id'])
        asset=self.actual['scene_assets']
        self.assertIn(asset['scene_id'],{s['scene_id'] for s in json.loads(job['manifest_json'])['scenes']})
        native=json.loads(asset['asset_json'])
        schema=json.loads((CONTRACTS/'production-manifest/v1.0.0/production_manifest.schema.json').read_text())
        Draft202012Validator(schema['properties']['asset_references']['items']).validate(native)
        for field in ('asset_id','scene_id','kind','status'):self.assertEqual(native[field],asset[field])

    def test_approval_receipt_preservation(self):
        row=self.actual['approvals'];receipt=json.loads(row['receipt_json'])
        schema=json.loads((CONTRACTS/'job-state/v1.0.0/gate_receipt.schema.json').read_text())
        Draft202012Validator(schema).validate(receipt)
        self.assertEqual(receipt['receipt_id'],row['record_id'])
        self.assertEqual(receipt['job_id'],row['job_id'])
        self.assertEqual(receipt['manifest_ref']['sha256'],row['manifest_sha256'])
        self.assertEqual(receipt['gate'],row['gate'])
        self.assertEqual(receipt['decision'],row['decision'])
        self.assertEqual(receipt['type'],row['receipt_type'])
        self.assertEqual(receipt['actor'],{'id':row['actor_id'],'kind':row['actor_kind']})

    def test_no_operational_authority_or_spend(self):
        for row in self.actual.values():
            self.assertIs(row['is_test'],True)
            self.assertEqual(row['test_run_id'],'P0104-v1-storage-test-001')
        self.assertEqual(self.actual['production_jobs']['state'],'draft')
        self.assertEqual(self.actual['approvals']['decision'],'pending')
        self.assertEqual(self.actual['provider_jobs']['status'],'not_submitted')
        self.assertIsNone(self.actual['provider_jobs']['provider_job_id'])
        self.assertEqual(self.actual['costs']['amount_microusd'],0)
        self.assertEqual(self.actual['costs']['currency'],'USD')
        self.assertEqual(self.actual['costs']['cost_type'],'estimate')
        self.assertEqual(self.actual['errors']['status'],'test_only')

    def test_error_contract_compatibility(self):
        row=self.actual['errors'];error=json.loads(row['details_json'])['agent_result_error']
        schema=json.loads((CONTRACTS/'agent-result/v1.0.0/agent_result.schema.json').read_text())
        Draft202012Validator(schema['properties']['errors']['items']).validate(error)
        self.assertEqual(error['code'],row['code']);self.assertEqual(error['retryable'],row['retryable'])

if __name__=='__main__':unittest.main(verbosity=2)
