"""Pure P01.03 transition contract; no storage, provider calls or publishing."""
import copy
import json
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent
SPEC = json.loads((ROOT / 'transitions.json').read_text())
STATES = SPEC['states']
EDGES = {(e['from'], e['to']): e['required_gates'] for e in SPEC['transitions']}
SCHEMA = json.loads((ROOT / 'job_state.schema.json').read_text())
RECEIPT_SCHEMA = json.loads((ROOT / 'gate_receipt.schema.json').read_text())

class TransitionRejected(ValueError):
    pass


def check_schema(instance, schema):
    errors = list(Draft202012Validator(schema).iter_errors(instance))
    if errors:
        raise TransitionRejected('; '.join(e.message for e in errors))


def validate_snapshot(job):
    check_schema(job, SCHEMA)
    history = job['history']
    if job['state_version'] != len(history):
        raise TransitionRejected('state_version does not match history length')
    current = 'draft'
    for i, event in enumerate(history, 1):
        edge = (current, event['to'])
        if event['sequence'] != i or event['from'] != current or edge not in EDGES:
            raise TransitionRejected('History is not the locked sequential path')
        if set(event['evidence']) != set(EDGES[edge]):
            raise TransitionRejected('History evidence does not match transition gates')
        current = event['to']
    if job['state'] != current:
        raise TransitionRejected('Current state does not match history')


def create_draft(job_id, manifest_ref):
    """Caller supplies a reference from an already validated P01.01 manifest."""
    job = {'schema_version':'1.0.0','job_id':job_id,'manifest_ref':copy.deepcopy(manifest_ref),
           'state':'draft','state_version':0,'history':[]}
    validate_snapshot(job)
    return job


def transition(job, target, *, expected_version, manifest_ref, evidence, resolve_receipt):
    """Return a new snapshot only after gates pass.

    job must be loaded from trusted state storage by the future integration.
    resolve_receipt(id) must retrieve verified evidence from trusted storage,
    not from the agent payload or incoming request. There is deliberately no
    fallback resolver. Synthetic resolvers in tests are NOT real approvals.
    The caller must later atomically persist against expected_version; this
    pure function does not claim database concurrency or exactly-once behavior.
    """
    validate_snapshot(job)
    if type(expected_version) is not int or expected_version != job['state_version']:
        raise TransitionRejected('Stale or invalid expected state version')
    if manifest_ref != job['manifest_ref']:
        raise TransitionRejected('Manifest reference changed: start a separately reviewed revision')
    if not isinstance(target, str) or (job['state'], target) not in EDGES:
        raise TransitionRejected('Only the next locked state is allowed')
    required = EDGES[(job['state'], target)]
    if not isinstance(evidence, dict) or set(evidence) != set(required):
        raise TransitionRejected('Missing or unexpected transition evidence')
    if not callable(resolve_receipt):
        raise TransitionRejected('Trusted evidence resolver is required')
    for gate in required:
        receipt_id = evidence[gate]
        if not isinstance(receipt_id, str) or not receipt_id.strip():
            raise TransitionRejected('Evidence must be a nonempty receipt ID')
        try:
            receipt = resolve_receipt(receipt_id)
        except Exception as exc:
            raise TransitionRejected('Evidence resolution failed') from exc
        check_schema(receipt, RECEIPT_SCHEMA)
        if (receipt['receipt_id'] != receipt_id or receipt['job_id'] != job['job_id']
                or receipt['manifest_ref'] != job['manifest_ref'] or receipt['gate'] != gate):
            raise TransitionRejected('Receipt does not match this job, revision and gate')
        if receipt['decision'] != 'passed' or receipt['type'] != SPEC['receipt_types'][gate]:
            raise TransitionRejected('Gate is not satisfied by the required receipt type')
        if receipt['type'] == 'human_approval' and receipt['actor']['kind'] != 'owner':
            raise TransitionRejected('Human approval requires the owner')
        if receipt['type'] != 'human_approval' and receipt['actor']['kind'] == 'agent':
            raise TransitionRejected('Agent claims are not independently verified gate evidence')
    result = copy.deepcopy(job)
    result['state'] = target
    result['state_version'] += 1
    result['history'].append({'sequence':result['state_version'],'from':job['state'],
                              'to':target,'evidence':copy.deepcopy(evidence)})
    validate_snapshot(result)
    return result
