import copy
import json
import multiprocessing
from pathlib import Path
import tempfile
import unittest
from revision_guard import RevisionStore, Rejected, CONTRACTS, manifest, parse, reference, revision_id

BASE=parse((CONTRACTS/'production-manifest/v1.0.0/example.valid.json').read_bytes())
BASE['project_id']='FWAI-P0105-TEST'
BASE['approval_state']={'status':'pending_review','approved_revision':None,'approved_by':None,'approval_record_id':None}
def encoded(m):return (json.dumps(m,indent=2)+'\n').encode()
def competing(args):
    root,raw=args
    try:return ('accepted',RevisionStore(root).commit(raw))
    except Rejected as exc:return ('rejected',str(exc))

class RevisionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=RevisionStore(self.tmp.name);self.raw=encoded(BASE)
        self.job=self.store.prepare_job(self.raw,'P0105-TEST-JOB-R1',is_test=True,test_run_id='P0105-TEST')
        self.ref=reference(self.raw)

    def rows(self):
        rows=parse((CONTRACTS/'data-tables/v1.0.0/test-records.json').read_bytes())
        for row in rows.values():
            for key in ('project_id','job_id','manifest_revision','manifest_sha256','is_test','test_run_id'):row[key]=self.job[key]
        rows['production_jobs']=copy.deepcopy(self.job)
        receipt=parse(rows['approvals']['receipt_json']);receipt.update(job_id=self.job['job_id'],manifest_ref=self.ref)
        rows['approvals']['receipt_json']=json.dumps(receipt)
        return rows

    def test_immutable_identity_and_exact_bytes(self):
        self.assertEqual(self.store.read(self.ref),self.raw)
        self.assertEqual(self.job['record_id'],revision_id(self.ref))
        self.assertEqual(self.store.commit(self.raw),self.ref)
        changed=copy.deepcopy(BASE);changed['scenes'][0]['narration']+=' Changed script.'
        with self.assertRaises(Rejected):self.store.commit(encoded(changed))
        with self.assertRaises(Rejected):self.store.commit(self.raw+b'\n')
        self.assertEqual(self.store.read(self.ref),self.raw)

    def test_approved_script_cannot_be_overwritten(self):
        rows=self.rows();approval=rows['approvals'];r=parse(approval['receipt_json'])
        r.update(gate='human_production_approval',type='human_approval',decision='passed',actor={'id':'synthetic-test-owner','kind':'owner'})
        approval.update(gate=r['gate'],receipt_type=r['type'],decision=r['decision'],actor_id=r['actor']['id'],actor_kind='owner',receipt_json=json.dumps(r))
        self.store.validate_row('approvals',approval,self.job)
        modified=copy.deepcopy(BASE);modified['title']='Attempted overwrite after synthetic approval'
        with self.assertRaises(Rejected):self.store.commit(encoded(modified))
        self.assertEqual(self.store.read(self.ref),self.raw)

    def test_new_revision_resets_approval(self):
        changed=copy.deepcopy(BASE);changed['revision']=2;changed['title']='Revised script'
        for approval in [dict(status='approved',approved_revision=2,approved_by='synthetic-owner',approval_record_id='synthetic-receipt'),dict(status='needs_revision',approved_revision=None,approved_by=None,approval_record_id=None)]:
            changed['approval_state']=approval
            with self.assertRaises(Rejected):self.store.commit(encoded(changed))
        changed['approval_state']=copy.deepcopy(BASE['approval_state'])
        row=self.store.prepare_job(encoded(changed),'P0105-TEST-JOB-R2',is_test=True,test_run_id='P0105-TEST')
        self.assertNotEqual(row['record_id'],self.job['record_id']);self.assertEqual(row['state'],'draft')
        self.assertEqual(self.store.read(self.ref),self.raw)
        approval=self.rows()['approvals']
        with self.assertRaises(Rejected):self.store.validate_row('approvals',approval,row)

    def test_sequential_revision_numbers(self):
        m=copy.deepcopy(BASE);m['revision']=3
        with self.assertRaises(Rejected):self.store.commit(encoded(m))
        for bad in [True,1.5,9007199254740992]:
            m['revision']=bad
            with self.assertRaises(Rejected):self.store.commit(encoded(m))

    def test_invalid_manifests_never_committed(self):
        invalid=list((CONTRACTS/'production-manifest/v1.0.0').glob('example.invalid.*.json'))
        self.assertEqual(len(invalid),7)
        for p in invalid:
            with self.subTest(name=p.name):
                with self.assertRaises(Rejected):self.store.commit(p.read_bytes())
        self.assertEqual(len(list(Path(self.tmp.name).rglob('r*.json'))),1)

    def test_strict_json_and_optional_key_failure(self):
        for raw in [b'{"a":1,"a":2}',b'{"a":NaN}',b'{"a":1e999}',b'\xff',b'{']:
            with self.subTest(raw=raw):
                with self.assertRaises(Rejected):manifest(raw)
        m=copy.deepcopy(BASE);m['approval_state'].pop('approval_record_id')
        with self.assertRaises(Rejected):manifest(encoded(m))

    def test_all_six_row_validators(self):
        rows=self.rows()
        for key,row in rows.items():
            with self.subTest(table=key):self.store.validate_row(key,row,self.job,[rows['provider_jobs']])

    def test_row_field_and_relationship_rejections(self):
        rows=self.rows()
        mutations=[('costs','amount_microusd',1.2),('costs','amount_microusd',-1),('costs','amount_microusd',9007199254740992),('costs','currency','EUR'),('costs','cost_type','unknown'),('costs','provider_job_record_id','missing'),('errors','retryable','true'),('errors','stage','missing'),('errors','details_json','[]'),('scene_assets','scene_id','S99'),('provider_jobs','status','succeeded'),('provider_jobs','response_json','[]'),('approvals','decision','passed'),('production_jobs','state','approved'),('production_jobs','record_id','wrong'),('production_jobs','manifest_json',self.raw.decode()+'\n')]
        for table,key,value in mutations:
            with self.subTest(table=table,field=key,value=value):
                bad=copy.deepcopy(rows[table]);bad[key]=value
                with self.assertRaises((Rejected,ValueError)):self.store.validate_row(table,bad,self.job,[rows['provider_jobs']])
        for table in rows:
            for key,value in [('manifest_revision',2),('job_id','OTHER'),('is_test',False),('unknown',True)]:
                if table=='production_jobs' and key=='job_id':continue
                with self.subTest(table=table,field=key):
                    bad=copy.deepcopy(rows[table]);bad[key]=value
                    with self.assertRaises((Rejected,OSError)):self.store.validate_row(table,bad,self.job,[rows['provider_jobs']])

    def test_receipt_self_approval_rejected(self):
        row=self.rows()['approvals'];r=parse(row['receipt_json'])
        r.update(gate='human_production_approval',type='human_approval',decision='passed')
        row.update(gate=r['gate'],receipt_type=r['type'],decision=r['decision'],receipt_json=json.dumps(r))
        with self.assertRaises(Rejected):self.store.validate_row('approvals',row,self.job)

    def test_n8n_preflight_rejects_existing_identity(self):
        self.assertEqual(self.store.preflight_insert(self.job,[]),self.job)
        for field in ['record_id','job_id','revision']:
            old=copy.deepcopy(self.job)
            if field=='record_id':old.update(project_id='OTHER',manifest_revision=9,job_id='OTHER')
            elif field=='job_id':old.update(project_id='OTHER',manifest_revision=9,record_id='OTHER')
            else:old.update(record_id='OTHER',job_id='OTHER')
            with self.subTest(identity=field):
                with self.assertRaises(Rejected):self.store.preflight_insert(self.job,[old])

    def test_agent_result_bound_to_stored_manifest(self):
        result=parse((CONTRACTS/'agent-result/v1.0.0/agent_result.json').read_bytes())
        result['input_manifest']=self.ref;result['output']['project_id']=BASE['project_id']
        self.store.validate_agent_result(result,self.ref)
        result['input_manifest']['sha256']='0'*64
        with self.assertRaises(Rejected):self.store.validate_agent_result(result,reference(self.raw))

    def test_concurrent_conflicting_writers(self):
        a=copy.deepcopy(BASE);a.update(revision=2,title='Writer A')
        b=copy.deepcopy(a);b['title']='Writer B'
        with multiprocessing.get_context('fork').Pool(2) as pool:
            results=pool.map(competing,[(self.tmp.name,encoded(a)),(self.tmp.name,encoded(b))])
        self.assertEqual(sorted(r[0] for r in results),['accepted','rejected'])
        winner=next(r[1] for r in results if r[0]=='accepted')
        self.assertIn(self.store.read(winner),(encoded(a),encoded(b)))

    def test_restart_retains_revision_and_tamper_detected(self):
        other=RevisionStore(self.tmp.name)
        self.assertEqual(other.read(self.ref),self.raw)
        path=Path(self.tmp.name)/BASE['project_id']/'r1.json'
        path.chmod(0o644);path.write_bytes(self.raw+b'\n')
        with self.assertRaises(Rejected):other.read(self.ref)

    def test_path_and_symlink_rejected(self):
        m=copy.deepcopy(BASE);m['project_id']='../../escape'
        with self.assertRaises(Rejected):self.store.commit(encoded(m))
        p=Path(self.tmp.name)/BASE['project_id']/'r2.json';p.symlink_to('r1.json')
        m=copy.deepcopy(BASE);m['revision']=2
        with self.assertRaises(Rejected):self.store.commit(encoded(m))

    def test_live_n8n_capture_matches_guarded_revisions(self):
        folder=Path(__file__).resolve().parent
        live=parse((folder/'n8n-jobs-after.json').read_bytes())['rows']
        expected=parse((folder/'n8n-write-candidates.json').read_bytes())
        for n,row in enumerate(expected,1):
            raw=(folder/f'example.revision-{n}.json').read_bytes()
            self.store.commit(raw)
            actual=next(r for r in live if r['record_id']==row['record_id'])
            self.assertEqual({k:actual[k] for k in row},row)
            self.store.validate_row('production_jobs',actual,actual)
            self.assertEqual(actual['state'],'draft')
            self.assertIs(actual['is_test'],True)
if __name__=='__main__':unittest.main(verbosity=2)
