"""Temporary, test-only bridge from the existing n8n adapter to installed P01 guards.

Bind only to the Future Works Docker gateway. It has no write or provider methods.
Stop it after the connected acceptance run; it is not a production API.
"""
import copy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path('/home/mattis983/futureworks-studio/futureworks-ai-studio')
GUARD = ROOT / 'contracts/revision-guard/v1.0.0/revision_guard.py'
STATE = ROOT / 'contracts/job-state/v1.0.0/job_state.py'
STORE = ROOT / 'data/manifest-revisions'
PROJECT = 'FWAI-P0105-LIVE-TEST'
JOB = 'P0105-LIVE-TEST-R2'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


guard = module('p0107_guard', GUARD)
state = module('p0107_state', STATE)
store = guard.RevisionStore(STORE)


def run(body):
    job = body['job']
    receipt = body['receipt']
    if job.get('project_id') != PROJECT or job.get('job_id') != JOB or job.get('is_test') is not True:
        raise ValueError('Only the selected synthetic job may be checked')
    if receipt.get('is_test') is not True or receipt.get('job_id') != JOB:
        raise ValueError('Only the selected synthetic receipt may be checked')
    clean_job = store.validate_row('production_jobs', job, job)
    clean_receipt = store.validate_row('approvals', receipt, job)
    raw = job['manifest_json'].encode('utf-8')
    ref = guard.reference(raw)
    if ref['sha256'] != job['manifest_sha256'] or store.read(ref) != raw:
        raise ValueError('Immutable manifest identity mismatch')

    bad_manifest = json.loads(raw)
    del bad_manifest['scenes'][0]['narration']
    try:
        guard.manifest(json.dumps(bad_manifest).encode('utf-8'))
    except guard.Rejected:
        invalid_manifest_rejected = True
    else:
        raise ValueError('Canonical manifest guard accepted missing narration')

    bad_job = copy.deepcopy(clean_job)
    bad_job['manifest_sha256'] = '0' * 64
    try:
        store.validate_row('production_jobs', bad_job, bad_job)
    except guard.Rejected:
        invalid_row_rejected = True
    else:
        raise ValueError('Canonical row guard accepted wrong revision hash')

    snapshot = guard.parse(job['snapshot_json'])
    if snapshot['state'] != 'draft' or snapshot['state_version'] != 0:
        raise ValueError('Test must start from the saved draft snapshot')
    parsed_receipt = guard.parse(receipt['receipt_json'])
    advanced = state.transition(
        snapshot, 'research', expected_version=0, manifest_ref=ref,
        evidence={'brief_validated': receipt['record_id']},
        resolve_receipt=lambda receipt_id: parsed_receipt if receipt_id == receipt['record_id'] else None,
    )
    return {
        'status': 'canonical_gates_passed',
        'job_id': JOB,
        'manifest_revision': ref['revision'],
        'manifest_sha256': ref['sha256'],
        'job_row_validated': bool(clean_job),
        'receipt_row_validated': bool(clean_receipt),
        'invalid_manifest_rejected': invalid_manifest_rejected,
        'invalid_row_rejected': invalid_row_rejected,
        'from_state': 'draft',
        'to_state': advanced['state'],
        'state_version': advanced['state_version'],
        'snapshot_json': json.dumps(advanced, sort_keys=True),
        'synthetic_only': True,
        'provider_calls': 0,
        'amount_microusd': 0,
    }


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != '/p01/check':
            return self.reply(404, {'error': 'not found'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 1 <= size <= 100_000:
                raise ValueError('Invalid body size')
            body = json.loads(self.rfile.read(size))
            self.reply(200, run(body))
        except (ValueError, KeyError, TypeError, guard.Rejected, state.TransitionRejected) as exc:
            self.reply(400, {'error': str(exc)[:400]})

    def reply(self, code, value):
        raw = json.dumps(value).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, fmt, *args):
        print(fmt % args, file=sys.stderr)


if __name__ == '__main__':
    ThreadingHTTPServer((os.environ.get('FWAI_TEST_BIND', '127.0.0.1'), 8765), Handler).serve_forever()
