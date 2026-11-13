"""Synthetic crash/recovery bound to P01.07 manifest. No external calls."""
import hashlib,json,os,pathlib,sys,tempfile
ROOT=pathlib.Path(__file__).resolve().parent
CONTRACTS=pathlib.Path('/home/mattis983/futureworks-studio/futureworks-ai-studio/contracts')
sys.path.insert(0,str(CONTRACTS/'recovery-policy/v1.0.0'))
from recovery import create,begin_action,decide,observe,apply_charge,operation_key,canonical

def write(path,value):
    fd,temp=tempfile.mkstemp(dir=path.parent,prefix='.atomic-')
    try:
        with os.fdopen(fd,'wb') as f:f.write(canonical(value));f.flush();os.fsync(f.fileno())
        os.replace(temp,path)
        directory=os.open(path.parent,os.O_DIRECTORY)
        try:os.fsync(directory)
        finally:os.close(directory)
    finally:
        if os.path.exists(temp):os.unlink(temp)

def read(path):return json.loads(path.read_text())

def main(mode,folder):
    folder.mkdir(parents=True,exist_ok=True)
    context=read(ROOT/'test-context.json');ref=context['manifest_ref']
    identity={'schema_version':'1.0.0','manifest_ref':ref,'job_id':context['job_id'],'scene_id':'S01','provider':'synthetic_no_provider','provider_account_reference':'P0107-synthetic-account','operation':'data_gate_test','model_version':'fixture-v1','request_sha256':hashlib.sha256(b'P0107 no paid request').hexdigest(),'input_asset_sha256':[],'generation_intent':'P0107-first-test'}
    state=folder/'operation.json';provider=folder/'mock-provider.json';ledger=folder/'ledger.json'
    if mode=='crash':
        if state.exists():raise RuntimeError('Fresh simulation directory required')
        operation=create(identity,1000,reservation_record_id='P0107-synthetic-zero-reservation')
        operation,action=begin_action(operation,1000,authorization_valid=True,writer_owned=True)
        assert action=='submit_new'
        write(state,operation)
        write(provider,{'synthetic_only':True,'operation_key':operation_key(identity),'job_id':'P0107-mock-provider-job','submissions':1,'amount_microusd':0})
        os._exit(17)
    operation=read(state);mock=read(provider)
    action=decide(operation,1061,writer_owned=True)
    if action=='reconcile_by_key':
        assert operation['operation_key']==mock['operation_key']
        operation=observe(operation,'accepted',1061,provider_job_id=mock['job_id']);write(state,operation)
        operation,action=begin_action(operation,1061,writer_owned=True);assert action=='poll_existing_job';write(state,operation)
        operation=observe(operation,'provider_succeeded',1061);write(state,operation)
        operation,action=begin_action(operation,1061,writer_owned=True);assert action=='download_existing_asset';write(state,operation)
        artifact=b'P01.07 synthetic data-gate artifact; not generated media\n'
        (folder/'artifact.txt').write_bytes(artifact)
        operation=observe(operation,'artifact_verified',1061,sha256=hashlib.sha256(artifact).hexdigest());write(state,operation)
        charges={}
        for _ in range(2):charges=apply_charge(charges,provider_account_reference=identity['provider_account_reference'],event_id='P0107-mock-bill-event',operation_key=operation['operation_key'],amount_microusd=0)
        write(ledger,charges)
        outcome='reconciled_existing_job'
    else:
        assert action=='reuse_verified_result'
        assert hashlib.sha256((folder/'artifact.txt').read_bytes()).hexdigest()==operation['result_sha256']
        outcome='reused_verified_result'
    charges=read(ledger)
    report={'synthetic_only':True,'manifest_ref':ref,'operation_key':operation['operation_key'],'outcome':outcome,'submissions':mock['submissions'],'charge_events':len(charges),'amount_microusd':sum(x['amount_microusd'] for x in charges.values()),'status':operation['status'],'artifact_sha256':operation['result_sha256']}
    write(folder/'report.json',report)
    print(json.dumps(report))

if __name__=='__main__':main(sys.argv[1],pathlib.Path(sys.argv[2]))
