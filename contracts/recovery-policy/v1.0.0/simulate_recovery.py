"""Synthetic offline crash/restart experiment. No provider or n8n client."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from recovery import create,begin_action,observe,decide,apply_charge,canonical


def save(path,value):
    fd,temp=tempfile.mkstemp(prefix='.save-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(canonical(value));f.flush();os.fsync(f.fileno())
        os.replace(temp,path)
        fd=os.open(path.parent,os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)
    finally:
        if os.path.exists(temp):os.unlink(temp)


def read(path):return json.loads(path.read_text())

def identity():
    return {'schema_version':'1.0.0','manifest_ref':{'schema_version':'1.0.0','project_id':'FWAI-P0106-TEST','revision':1,'sha256':'a'*64},'job_id':'P0106-RECOVERY-TEST','scene_id':'S01','provider':'synthetic_provider','provider_account_reference':'synthetic-account','operation':'generate_video','model_version':'synthetic-v1','request_sha256':'b'*64,'input_asset_sha256':['c'*64],'generation_intent':'initial'}


def run(mode,root):
    root.mkdir(parents=True,exist_ok=True)
    state=root/'operation.json';provider=root/'mock-provider.json';ledger=root/'ledger.json'
    if mode=='crash':
        if state.exists() or provider.exists():raise ValueError('Use an empty fixture directory')
        s=create(identity(),1000,reservation_record_id='synthetic-reservation')
        s,action=begin_action(s,1000,authorization_valid=True,writer_owned=True)
        assert action=='submit_new'
        save(state,s) # Write-ahead intent before the synthetic provider acceptance.
        save(provider,{'synthetic_only':True,'operation_key':s['operation_key'],'provider_job_id':'mock-job-1','submissions':1,'billable_events':1,'amount_microusd':250000})
        os._exit(17) # Deliberate process death before storing provider ID.
    if mode!='recover':raise ValueError('Unknown mode')
    s=read(state);p=read(provider)
    action=decide(s,1061,writer_owned=True)
    if action=='reuse_verified_result':
        report={'synthetic_only':True,'action':action,'submissions':p['submissions'],'billable_events':p['billable_events'],'recorded_charge_events':len(read(ledger)),'status':s['status']}
        save(root/'report.json',report);return report
    assert action=='reconcile_by_key'
    # Trusted mock lookup locates existing job; no second submission is sent.
    assert p['operation_key']==s['operation_key']
    s=observe(s,'accepted',1061,provider_job_id=p['provider_job_id']);save(state,s)
    s,action=begin_action(s,1061,writer_owned=True);assert action=='poll_existing_job';save(state,s)
    s=observe(s,'provider_succeeded',1061);save(state,s)
    s,action=begin_action(s,1061,writer_owned=True);assert action=='download_existing_asset';save(state,s)
    artifact=b'SYNTHETIC P01.06 artifact; not generated media\n'
    (root/'artifact.txt').write_bytes(artifact)
    s=observe(s,'artifact_verified',1061,sha256=hashlib.sha256(artifact).hexdigest());save(state,s)
    costs={}
    # Two deliveries of the same synthetic billing event produce one ledger entry.
    for _ in range(2):costs=apply_charge(costs,provider_account_reference='synthetic-account',event_id='mock-invoice-line-1',operation_key=s['operation_key'],amount_microusd=p['amount_microusd'])
    save(ledger,costs)
    report={'synthetic_only':True,'action':'reconciled_existing_job','submissions':p['submissions'],'billable_events':p['billable_events'],'recorded_charge_events':len(costs),'status':s['status']}
    save(root/'report.json',report);return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=['crash','recover']);parser.add_argument('directory',type=Path)
    args=parser.parse_args();print(json.dumps(run(args.mode,args.directory)))
