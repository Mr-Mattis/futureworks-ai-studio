"""P01.07 contract/data gate acceptance over one live-stored dummy manifest."""
import copy,hashlib,importlib.util,json,os,pathlib,subprocess,sys,tempfile
from jsonschema import Draft202012Validator
ROOT=pathlib.Path(__file__).resolve().parent
CONTRACTS=pathlib.Path('/home/mattis983/futureworks-studio/futureworks-ai-studio/contracts')
def read(p):return json.loads(pathlib.Path(p).read_text())
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def main():
    context=read(ROOT/'test-context.json');live=read(ROOT/'live-readback.json')
    job=live['production_jobs']['rows'][0];ref=context['manifest_ref']
    guard=load('revision_guard_v1',CONTRACTS/'revision-guard/v1.0.0/revision_guard.py')
    store=guard.RevisionStore('/home/mattis983/futureworks-studio/futureworks-ai-studio/data/manifest-revisions')
    checks=[];rejections=[]
    def passed(name):checks.append(name)
    raw=store.read(ref);manifest=guard.manifest(raw)
    assert ref==guard.reference(raw)
    assert manifest['project_id']==job['project_id'] and manifest['revision']==job['manifest_revision']
    assert sum(s['duration_seconds'] for s in manifest['scenes'])==manifest['target_duration_seconds']
    assert len({s['scene_id'] for s in manifest['scenes']})==len(manifest['scenes'])==5
    passed('P01.01 exact manifest schema, five scene IDs and 360-second total')
    store.validate_row('production_jobs',job,job);passed('P01.05 immutable revision and draft job row')
    provider=live['provider_jobs']['rows'][0]
    for key in ('provider_jobs','scene_assets','costs','approvals','errors'):
        row=live[key]['rows'][0]
        expected=read(ROOT/(key+'.candidate.json'))
        assert {k:row[k] for k in expected}==expected
        store.validate_row(key,row,job,[provider])
        passed('P01.04 '+key+' live roundtrip and guarded validation')
    assert live['approvals']['rows'][0]['decision']=='pending'
    assert live['provider_jobs']['rows'][0]['status']=='not_submitted'
    assert live['costs']['rows'][0]['amount_microusd']==0
    passed('no passed live approval, provider submission or paid charge')
    bad_cases={
        'production_jobs':('manifest_json',job['manifest_json']+'\n'),
        'provider_jobs':('status','succeeded'),
        'scene_assets':('scene_id','S99'),
        'costs':('currency','EUR'),
        'approvals':('decision','passed'),
        'errors':('retryable','true'),
    }
    for key,(field,value) in bad_cases.items():
        bad=copy.deepcopy(live[key]['rows'][0]);bad[field]=value
        try:store.validate_row(key,bad,job,[provider])
        except guard.Rejected:rejections.append('invalid '+key+' field '+field)
        else:raise AssertionError('Invalid '+key+' accepted')
    agent_dir=CONTRACTS/'agent-result/v1.0.0'
    roles=read(agent_dir/'agent-registry.json')
    for role in roles:
        result=read(agent_dir/'examples'/(role['key']+'.json'))
        result['input_manifest']=copy.deepcopy(ref)
        if 'project_id' in result['output']:result['output']['project_id']=ref['project_id']
        store.validate_agent_result(result,ref)
        assert result['agent']['instance_id']==role['id']
        passed('P01.02 '+role['key']+' handoff')
        if role==roles[0]:
            invalid_result=copy.deepcopy(result)
            invalid_result['input_manifest']['revision']+=1
            try:store.validate_agent_result(invalid_result,ref)
            except guard.Rejected:rejections.append('agent result wrong manifest revision')
            else:raise AssertionError('Wrong-revision agent result accepted')
    # Live state stays draft. These in-memory receipts are explicitly synthetic.
    state_mod=load('job_state_v1',CONTRACTS/'job-state/v1.0.0/job_state.py')
    state=json.loads(job['snapshot_json']);state_mod.validate_snapshot(state)
    receipts={}
    for edge in read(CONTRACTS/'job-state/v1.0.0/transitions.json')['transitions']:
        evidence={}
        for gate in edge['required_gates']:
            rid='P0107-synthetic-'+gate
            rtype=state_mod.SPEC['receipt_types'][gate]
            receipts[rid]={'receipt_id':rid,'job_id':job['job_id'],'manifest_ref':copy.deepcopy(ref),'gate':gate,'type':rtype,'decision':'passed','actor':{'id':'synthetic-fixture','kind':'owner' if rtype=='human_approval' else 'service'},'evidence_reference':'synthetic-only:never-stored-as-live-approval'}
            evidence[gate]=rid
        try:state_mod.transition(state,edge['to'],expected_version=state['state_version'],manifest_ref=ref,evidence={},resolve_receipt=receipts.get)
        except state_mod.TransitionRejected:rejections.append('missing '+edge['to']+' gate evidence')
        else:raise AssertionError('Missing gate accepted')
        if edge['to']=='approved':
            invalid_receipts=copy.deepcopy(receipts)
            invalid_receipts[evidence['human_production_approval']]['actor']['kind']='agent'
            try:state_mod.transition(state,edge['to'],expected_version=state['state_version'],manifest_ref=ref,evidence=evidence,resolve_receipt=invalid_receipts.get)
            except state_mod.TransitionRejected:rejections.append('agent self-approval blocked')
            else:raise AssertionError('Agent self-approval accepted')
        state=state_mod.transition(state,edge['to'],expected_version=state['state_version'],manifest_ref=ref,evidence=evidence,resolve_receipt=receipts.get)
        assert state['manifest_ref']==ref and state['job_id']==job['job_id']
        passed('P01.03 synthetic '+edge['from']+' to '+edge['to']+' contract gate')
    assert state['state']=='published' and job['state']=='draft'
    invalid=list((CONTRACTS/'production-manifest/v1.0.0').glob('example.invalid.*.json'))
    assert len(invalid)==7
    for p in invalid:
        try:guard.manifest(p.read_bytes())
        except guard.Rejected:rejections.append('invalid manifest '+p.name)
        else:raise AssertionError('Invalid manifest accepted')
    altered=copy.deepcopy(manifest);altered['title']='same-revision forbidden overwrite'
    with tempfile.TemporaryDirectory() as revision_dir:
        isolated=guard.RevisionStore(revision_dir)
        isolated.commit(raw)
        try:isolated.commit((json.dumps(altered)+'\n').encode())
        except guard.Rejected:rejections.append('same revision overwrite')
        else:raise AssertionError('Overwrite accepted')
    with tempfile.TemporaryDirectory() as directory:
        cmd=[sys.executable,str(ROOT/'simulate_interruption.py')]
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
        crash=subprocess.run(cmd+['crash',directory],capture_output=True,env=env)
        assert crash.returncode==17
        first=json.loads(subprocess.run(cmd+['recover',directory],check=True,capture_output=True,text=True,env=env).stdout)
        second=json.loads(subprocess.run(cmd+['recover',directory],check=True,capture_output=True,text=True,env=env).stdout)
        assert first['outcome']=='reconciled_existing_job' and second['outcome']=='reused_verified_result'
        assert all(x['manifest_ref']==ref and x['submissions']==1 and x['charge_events']==1 and x['amount_microusd']==0 for x in (first,second))
        passed('P01.06 crash/restart reconciles same key without duplicate synthetic job or expense')
        recovery={'crash_exit_code':17,'first':first,'second':second}
    report={'checkpoint':'P01.07','status':'PASS','synthetic_only':True,'manifest_ref':ref,'job_id':job['job_id'],'live_job_state_unchanged':'draft','checks_passed':len(checks),'expected_rejections':len(rejections),'checks':checks,'rejections':rejections,'recovery':recovery,'real_provider_calls':0,'real_expenses_microusd':0,'publication_actions':0}
    (ROOT/'gate-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','checks_passed','expected_rejections','real_provider_calls','real_expenses_microusd')}))
if __name__=='__main__':main()
