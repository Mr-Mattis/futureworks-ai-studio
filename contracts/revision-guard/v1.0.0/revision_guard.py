"""P01.05 validated, append-only revision files and guarded n8n row preparation.
No network access, n8n updates, paid calls or approval creation.
"""
import argparse
import copy
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import tempfile
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent
CONTRACTS = Path('/home/mattis983/futureworks-studio/futureworks-ai-studio/contracts')

class Rejected(ValueError):
    pass


def parse(raw):
    def pairs(items):
        result = {}
        for key,value in items:
            if key in result: raise Rejected('Duplicate JSON key: '+key)
            result[key] = value
        return result
    def constant(value): raise Rejected('Non-finite number: '+value)
    try:
        result=json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)
        # Reject exponent overflow too (e.g. 1e999).
        json.dumps(result,allow_nan=False)
        return result
    except (ValueError,UnicodeError,TypeError) as exc:
        raise Rejected('Invalid strict JSON: '+str(exc)) from exc


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def dependencies():
    pins=parse((ROOT/'dependencies.json').read_bytes())
    for name,digest in pins.items():
        if hashlib.sha256((CONTRACTS/name).read_bytes()).hexdigest()!=digest:
            raise Rejected('Dependency changed: '+name)


def check(value,schema):
    errors=list(Draft202012Validator(schema).iter_errors(value))
    if errors:raise Rejected('; '.join(e.message for e in errors))


def manifest(raw):
    dependencies()
    value=parse(raw)
    folder=CONTRACTS/'production-manifest/v1.0.0'
    schema=parse((folder/'production_manifest.schema.json').read_bytes())
    check(value,schema)
    try:
        errors=load_module('manifest_v1',folder/'validate_manifest.py').validate(schema,value)
    except (KeyError,TypeError,ValueError) as exc:
        raise Rejected('Manifest invariant validation rejected input: '+str(exc)) from exc
    if errors:raise Rejected('; '.join(errors))
    if type(value['revision']) is not int or not 1 <= value['revision'] <= 9007199254740991:
        raise Rejected('Revision must be a positive safe integer')
    return value


def reference(raw):
    m=manifest(raw)
    return {'schema_version':m['schema_version'],'project_id':m['project_id'],
            'revision':m['revision'],'sha256':hashlib.sha256(raw).hexdigest()}


def revision_id(ref):
    return f"{ref['project_id']}:r{ref['revision']}:{ref['sha256']}"


class RevisionStore:
    """Trusted local filesystem only. Never expose this root to an agent shell.
    Exclusive publication plus per-project flock protect cooperative writers.
    Not protection against an administrator modifying files outside this API.
    """
    def __init__(self, root):
        self.root=Path(root)

    def _path(self, project, revision):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{2,79}',project):raise Rejected('Unsafe project ID')
        if type(revision) is not int or not 1 <= revision <= 9007199254740991:raise Rejected('Invalid revision')
        return self.root/project/f'r{revision}.json'

    def read(self, ref):
        check(ref,parse((CONTRACTS/'job-state/v1.0.0/job_state.schema.json').read_bytes())['properties']['manifest_ref'])
        path=self._path(ref['project_id'],ref['revision'])
        if path.is_symlink():raise Rejected('Revision must not be a symlink')
        raw=path.read_bytes()
        if reference(raw)!=ref:raise Rejected('Stored revision identity/hash mismatch')
        return raw

    def commit(self, raw):
        ref=reference(raw);m=parse(raw)
        path=self._path(ref['project_id'],ref['revision'])
        path.parent.mkdir(parents=True,exist_ok=True)
        if path.parent.is_symlink():raise Rejected('Project directory must not be a symlink')
        # Existing manifest files are never opened for writing.
        with (path.parent/'.revision.lock').open('a+b') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            if path.exists() or path.is_symlink():
                if path.is_symlink() or path.read_bytes()!=raw:
                    raise Rejected('Immutable revision conflict: existing revision cannot be overwritten')
                return ref
            revisions=sorted(int(p.stem[1:]) for p in path.parent.glob('r*.json') if re.fullmatch(r'r[1-9][0-9]*',p.stem))
            expected=(revisions[-1]+1) if revisions else 1
            if m['revision']!=expected:raise Rejected('New revision must be the next consecutive number')
            # All new submissions start unapproved. Approvals live separately.
            if m['approval_state']['status']!='pending_review' or any(m['approval_state'].get(k) is not None for k in ('approved_revision','approved_by','approval_record_id')):
                raise Rejected('New revision must start pending_review with no inherited approval')
            fd,name=tempfile.mkstemp(prefix='.revision-',dir=path.parent)
            try:
                with os.fdopen(fd,'wb') as out:
                    out.write(raw);out.flush();os.fsync(out.fileno())
                os.chmod(name,0o444)
                os.link(name,path)  # Atomic publication; never replaces an existing path.
                dirfd=os.open(path.parent,os.O_DIRECTORY)
                try:os.fsync(dirfd)
                finally:os.close(dirfd)
            finally:
                os.unlink(name)
        return ref

    def validate_agent_result(self, result, ref):
        self.read(ref)
        folder=CONTRACTS/'agent-result/v1.0.0'
        errors=load_module('agent_result_v1',folder/'validate_agent_result.py').validate(result,self._path(ref['project_id'],ref['revision']))
        if errors:raise Rejected('; '.join(errors))

    def prepare_job(self, raw, job_id, *, is_test=False, test_run_id=None):
        if type(is_test) is not bool:raise Rejected('is_test must be boolean')
        if is_test != bool(test_run_id):raise Rejected('Test flag/run ID must agree')
        if not isinstance(job_id,str) or not job_id.strip():raise Rejected('job_id required')
        ref=self.commit(raw)
        state=load_module('job_state_v1',CONTRACTS/'job-state/v1.0.0/job_state.py').create_draft(job_id,ref)
        return {'record_id':revision_id(ref),'schema_version':'1.0.0','project_id':ref['project_id'],
                'job_id':job_id,'manifest_revision':ref['revision'],'manifest_sha256':ref['sha256'],
                'is_test':is_test,'test_run_id':test_run_id,'state':'draft','state_version':0,
                'manifest_json':raw.decode('utf-8'),'snapshot_json':json.dumps(state,sort_keys=True)}

    def validate_row(self, table, row, job, providers=()):
        """Validate a prospective row against trusted job and provider snapshots.
        Caller must authenticate source/actor and serialize writes separately.
        """
        dependencies()
        definitions=parse((CONTRACTS/'data-tables/v1.0.0/table-definitions.json').read_bytes())['tables']
        if table not in definitions:raise Rejected('Unknown table')
        columns={c['name']:c['type'] for c in definitions[table]['columns']}
        clean={k:v for k,v in row.items() if k not in ('id','createdAt','updatedAt')}
        if set(clean)!=set(columns):raise Rejected('Missing or unknown row fields')
        nullable={'test_run_id','provider_job_record_id','provider_job_id','scene_id'}
        for key,value in clean.items():
            if value is None and key in nullable:continue
            expected={'string':str,'boolean':bool,'number':int}[columns[key]]
            if type(value) is not expected:raise Rejected('Invalid column type: '+key)
            if expected is str and not value.strip():raise Rejected('Empty column: '+key)
            if expected is int and not 0 <= value <= 9007199254740991:raise Rejected('Unsafe integer: '+key)
        if clean['schema_version']!='1.0.0' or clean['manifest_revision']<1:raise Rejected('Invalid row version')
        if clean['is_test'] != bool(clean['test_run_id']):raise Rejected('Test identity mismatch')
        ref={'schema_version':'1.0.0','project_id':clean['project_id'],'revision':clean['manifest_revision'],'sha256':clean['manifest_sha256']}
        raw=self.read(ref);m=parse(raw)
        if table!='production_jobs':
            self.validate_row('production_jobs',job,job)
            for key in ('project_id','job_id','manifest_revision','manifest_sha256','is_test','test_run_id'):
                if clean[key]!=job[key]:raise Rejected('Job context mismatch: '+key)
        if table=='production_jobs':
            if clean['record_id']!=revision_id(ref):raise Rejected('Job record ID must be the immutable revision ID')
            if clean['manifest_json'].encode()!=raw:raise Rejected('Manifest bytes changed')
            snapshot=parse(clean['snapshot_json'])
            load_module('job_state_v1',CONTRACTS/'job-state/v1.0.0/job_state.py').validate_snapshot(snapshot)
            if snapshot['manifest_ref']!=ref or any(snapshot[k]!=clean[k] for k in ('job_id','state','state_version')):raise Rejected('Snapshot/index mismatch')
        elif table=='approvals':
            receipt=parse(clean['receipt_json'])
            check(receipt,parse((CONTRACTS/'job-state/v1.0.0/gate_receipt.schema.json').read_bytes()))
            if receipt['manifest_ref']!=ref or receipt['job_id']!=clean['job_id']:raise Rejected('Receipt revision/job mismatch')
            for key,rkey in [('record_id','receipt_id'),('gate','gate'),('receipt_type','type'),('decision','decision')]:
                if clean[key]!=receipt[rkey]:raise Rejected('Receipt/index mismatch')
            if receipt['actor']!={'id':clean['actor_id'],'kind':clean['actor_kind']}:raise Rejected('Receipt actor mismatch')
            types=parse((CONTRACTS/'job-state/v1.0.0/transitions.json').read_bytes())['receipt_types']
            if receipt['type']!=types[receipt['gate']]:raise Rejected('Wrong gate receipt type')
            if receipt['decision']=='passed':
                if receipt['actor']['kind']=='agent' or (receipt['type']=='human_approval' and receipt['actor']['kind']!='owner'):raise Rejected('Invalid approval actor kind')
        elif table=='scene_assets':
            asset=parse(clean['asset_json']);schema=parse((CONTRACTS/'production-manifest/v1.0.0/production_manifest.schema.json').read_bytes())
            check(asset,schema['properties']['asset_references']['items'])
            if any(asset[k]!=clean[k] for k in ('asset_id','scene_id','kind','status')):raise Rejected('Asset/index mismatch')
            if asset['scene_id'] is not None and asset['scene_id'] not in {s['scene_id'] for s in m['scenes']}:raise Rejected('Unknown scene')
            if asset['status'] in ('generated','verified') and not asset.get('file_uri'):raise Rejected('Generated asset has no file')
            if asset['status']=='verified' and not asset.get('sha256'):raise Rejected('Verified asset has no checksum')
        elif table=='provider_jobs':
            if clean['status'] not in ('not_submitted','queued','running','succeeded','failed','cancelled'):raise Rejected('Invalid provider status')
            if clean['status']=='not_submitted' and clean['provider_job_id'] is not None:raise Rejected('Unsubmitted provider ID')
            if clean['status'] in ('queued','running','succeeded') and not clean['provider_job_id']:raise Rejected('Missing external provider ID')
            if not isinstance(parse(clean['response_json']),dict):raise Rejected('Provider response must be object')
        elif table=='costs':
            if clean['currency']!='USD' or clean['cost_type'] not in ('estimate','reservation','actual'):raise Rejected('Invalid cost units/type')
        elif table=='errors':
            states=parse((CONTRACTS/'job-state/v1.0.0/transitions.json').read_bytes())['states']
            if clean['stage'] not in states or clean['severity'] not in ('info','warning','error') or clean['status'] not in ('open','resolved','test_only'):raise Rejected('Invalid error enums')
            details=parse(clean['details_json'])
            if not isinstance(details,dict):raise Rejected('Error details must be object')
            if 'agent_result_error' in details:
                schema=parse((CONTRACTS/'agent-result/v1.0.0/agent_result.schema.json').read_bytes())
                check(details['agent_result_error'],schema['properties']['errors']['items'])
        provider_id=clean.get('provider_job_record_id')
        if provider_id is not None:
            matches=[p for p in providers if p['record_id']==provider_id]
            if len(matches)!=1:raise Rejected('Missing/ambiguous provider reference')
            self.validate_row('provider_jobs',matches[0],job)
        return clean

    def preflight_insert(self, row, existing_rows):
        """Reject conflicts in a fresh n8n inventory. Not a distributed lock."""
        self.validate_row('production_jobs',row,row)
        for old in existing_rows:
            same_revision=(old['project_id'],old['manifest_revision'])==(row['project_id'],row['manifest_revision'])
            if same_revision or old['record_id']==row['record_id'] or old['job_id']==row['job_id']:
                raise Rejected('Existing n8n identity; update/overwrite is forbidden')
        if row['state']!='draft' or row['state_version']!=0:raise Rejected('New job must start draft')
        return row


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest');parser.add_argument('--store',required=True)
    parser.add_argument('--job-id',required=True);parser.add_argument('--test-run-id')
    args=parser.parse_args()
    try:
        row=RevisionStore(args.store).prepare_job(Path(args.manifest).read_bytes(),args.job_id,is_test=bool(args.test_run_id),test_run_id=args.test_run_id)
        print(json.dumps(row,indent=2));return 0
    except (Rejected,OSError) as exc:
        print('REJECTED: '+str(exc),file=__import__('sys').stderr);return 1

if __name__=='__main__':raise SystemExit(main())
