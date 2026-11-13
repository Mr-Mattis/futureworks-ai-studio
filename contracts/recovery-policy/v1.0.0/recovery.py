"""Offline P01.06 reference decisions. No network, payments or live-state writes."""
import copy
import hashlib
import json
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parent
POLICY=json.loads((ROOT/'policy.json').read_text())
LIMITS=POLICY['defaults']
IDENTITY_SCHEMA=json.loads((ROOT/'operation_identity.schema.json').read_text())
SNAPSHOT_SCHEMA=json.loads((ROOT/'operation_snapshot.schema.json').read_text())

class Rejected(ValueError): pass


def check(value,schema):
    errors=list(Draft202012Validator(schema).iter_errors(value))
    if errors:raise Rejected('; '.join(e.message for e in errors))


def canonical(value):
    # Defined Python JSON representation, NOT an RFC8785 cross-language claim.
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')


def operation_key(identity):
    check(identity,IDENTITY_SCHEMA)
    return 'fwai-op-v1-'+hashlib.sha256(canonical(identity)).hexdigest()


def validate(s):
    check(s,SNAPSHOT_SCHEMA)
    if s['operation_key']!=operation_key(s['identity']):raise Rejected('Operation identity changed')
    if s['deadline_at']!=s['created_at']+LIMITS['operation_deadline_seconds']:raise Rejected('Deadline cannot be extended silently')
    if s['last_observed_at']<s['created_at']:raise Rejected('Invalid recorded clock')
    if s['submit_attempts']>LIMITS['submit_attempts_total'] or s['poll_requests']>LIMITS['poll_requests_total'] or s['download_attempts']>LIMITS['download_attempts_total']:raise Rejected('Attempt limit exceeded')
    if s['status']=='prepared' and (s['submit_attempts'] or s['provider_job_id'] is not None):raise Rejected('Prepared state cannot claim a submission')
    if s['status'] in ('dispatching','retry_wait') and (not s['submit_attempts'] or s['provider_job_id'] is not None):raise Rejected('Invalid submission state')
    if s['status'] in ('accepted','download_pending','completed') and not s['provider_job_id']:raise Rejected('Missing provider job ID')
    if s['status']=='completed' and not s['result_sha256']:raise Rejected('Completion needs verified artifact checksum')
    if s['provider_job_id'] is not None and not s['submit_attempts']:raise Rejected('Provider ID without recorded submission')
    if (s['poll_requests'] or s['download_attempts']) and s['provider_job_id'] is None:raise Rejected('Read attempt without provider identity')
    if (s['adapter_contract_reference'] is None)!=(s['idempotency_guaranteed_until'] is None):raise Rejected('Incomplete verified adapter contract')


def create(identity,now,reservation_record_id=None,adapter_contract_reference=None,idempotency_guaranteed_until=None):
    s={'schema_version':'1.0.0','identity':copy.deepcopy(identity),'operation_key':operation_key(identity),
       'status':'prepared','provider_job_id':None,'submit_attempts':0,'poll_requests':0,'download_attempts':0,
       'created_at':now,'deadline_at':now+LIMITS['operation_deadline_seconds'],'last_observed_at':now,'not_before':now,
       'adapter_contract_reference':adapter_contract_reference,'idempotency_guaranteed_until':idempotency_guaranteed_until,
       'reservation_record_id':reservation_record_id,'result_sha256':None}
    validate(s);return s


def backoff(attempt, *, retry_after_seconds=0, jitter_seconds=0):
    if type(attempt) is not int or attempt<1:raise Rejected('Invalid attempt')
    if type(retry_after_seconds) is not int or retry_after_seconds<0:raise Rejected('Invalid Retry-After')
    if type(jitter_seconds) is not int or not 0<=jitter_seconds<=LIMITS['jitter_max_seconds']:raise Rejected('Invalid jitter')
    # Retry-After is never reduced to the cap. Deadline enforcement handles long waits.
    return max(min(LIMITS['backoff_cap_seconds'],LIMITS['backoff_base_seconds']*2**min(attempt-1,16)+jitter_seconds),retry_after_seconds)


def decide(s,now,*,authorization_valid=False,writer_owned=False):
    validate(s)
    if type(now) is not int or now<0:raise Rejected('Invalid clock')
    if type(authorization_valid) is not bool or type(writer_owned) is not bool:raise Rejected('Trust flags must be booleans')
    if now<s['last_observed_at']:return 'manual_review'
    if s['status']=='completed':return 'reuse_verified_result'
    if s['status'] in ('blocked','failed','cancelled'):return 'manual_review'
    if now>=s['deadline_at']:return 'manual_review'
    if not writer_owned:return 'wait_for_writer'
    if now<s['not_before']:return 'wait'
    if s['provider_job_id']:
        if s['status']=='accepted':return 'poll_existing_job' if s['poll_requests']<LIMITS['poll_requests_total'] else 'manual_review'
        if s['status']=='download_pending':return 'download_existing_asset' if s['download_attempts']<LIMITS['download_attempts_total'] else 'manual_review'
        return 'manual_review'
    if s['status']=='dispatching':
        # Unknown acceptance: only a verified, still-valid native guarantee permits replay.
        # Allow response timeout plus clock-skew margin before guarantee expiration.
        safe_until=s['idempotency_guaranteed_until']
        safe=safe_until is not None and safe_until>=now+LIMITS['submit_response_timeout_seconds']+30
        if safe and authorization_valid and s['reservation_record_id'] and s['submit_attempts']<LIMITS['submit_attempts_total']:
            return 'replay_same_key'
        return 'reconcile_by_key'
    if not authorization_valid or not s['reservation_record_id']:return 'manual_review'
    if s['submit_attempts']>=LIMITS['submit_attempts_total']:return 'manual_review'
    if s['status']=='prepared':return 'submit_new'
    if s['status']=='retry_wait':return 'retry_confirmed_unaccepted'
    return 'manual_review'


def begin_action(s,now,*,authorization_valid=False,writer_owned=False):
    """Caller MUST durably save returned snapshot before performing returned action.
    If save fails, do not send. Hold writer lock through response recording.
    """
    action=decide(s,now,authorization_valid=authorization_valid,writer_owned=writer_owned)
    out=copy.deepcopy(s)
    if action in ('submit_new','replay_same_key','retry_confirmed_unaccepted'):
        out['submit_attempts']+=1;out['status']='dispatching'
        out['not_before']=now+LIMITS['submit_response_timeout_seconds']
    elif action=='poll_existing_job':
        out['poll_requests']+=1;out['not_before']=now+LIMITS['poll_interval_seconds']
    elif action=='download_existing_asset':
        out['download_attempts']+=1;out['not_before']=now+LIMITS['download_timeout_seconds']
    else:return out,action
    out['last_observed_at']=now;validate(out);return out,action


def observe(s,event,now,**details):
    """Only trusted adapters may assert authoritative nonacceptance/terminal results.
    A timeout or generic HTTP error alone is never definitive nonacceptance.
    """
    validate(s)
    if type(now) is not int or now<s['last_observed_at']:raise Rejected('Clock moved backwards')
    out=copy.deepcopy(s);out['last_observed_at']=now
    if event=='accepted':
        if s['status']!='dispatching':raise Rejected('Acceptance outside submission reconciliation')
        pid=details.get('provider_job_id')
        if not isinstance(pid,str) or not pid:raise Rejected('Provider job ID required')
        out.update(provider_job_id=pid,status='accepted',not_before=now)
    elif event=='definitively_not_accepted':
        evidence=details.get('evidence_reference')
        if s['status']!='dispatching' or not isinstance(evidence,str) or not evidence.strip():raise Rejected('Authoritative nonacceptance evidence required')
        delay=backoff(s['submit_attempts'],retry_after_seconds=details.get('retry_after_seconds',0),jitter_seconds=details.get('jitter_seconds',0))
        out.update(status='retry_wait',not_before=now+delay)
    elif event=='unknown_submission_outcome':
        if s['status']!='dispatching':raise Rejected('No submission to reconcile')
        # Keep dispatching; retain reservation and original key. Not a retryable failure.
    elif event=='provider_pending':
        if s['status']!='accepted':raise Rejected('No accepted job to poll')
        retry_after=details.get('retry_after_seconds',0)
        if type(retry_after) is not int or retry_after<0:raise Rejected('Invalid Retry-After')
        out['not_before']=max(s['not_before'],now+LIMITS['poll_interval_seconds'],now+retry_after)
    elif event=='provider_succeeded':
        if s['status']!='accepted':raise Rejected('No accepted job')
        out.update(status='download_pending',not_before=now)
    elif event=='provider_failed':
        if s['status']!='accepted':raise Rejected('No accepted job')
        out.update(status='failed')  # Regeneration is a different explicitly approved intent.
    elif event=='artifact_verified':
        if s['status']!='download_pending' or s['download_attempts']==0:raise Rejected('No download in progress')
        out.update(status='completed',result_sha256=details.get('sha256'))
    elif event=='download_retry':
        if s['status']!='download_pending' or s['download_attempts']==0:raise Rejected('No download to retry')
        out['not_before']=now+backoff(s['download_attempts'],retry_after_seconds=details.get('retry_after_seconds',0))
    elif event=='cancelled':out['status']='cancelled'
    else:raise Rejected('Unknown recovery event')
    validate(out);return out


def billing_event_key(provider_account_reference,event_id):
    if not all(isinstance(x,str) and x.strip() for x in (provider_account_reference,event_id)):raise Rejected('Billing event identity required')
    return 'fwai-charge-v1-'+hashlib.sha256(canonical([provider_account_reference,event_id])).hexdigest()


def apply_charge(ledger,*,provider_account_reference,event_id,operation_key,amount_microusd):
    """Pure ledger decision; trusted writer must atomically persist returned ledger.
    Repeat matching event does not add cost; conflicting event requires reconciliation.
    """
    if type(amount_microusd) is not int or not 0<=amount_microusd<=9007199254740991:raise Rejected('Unsafe cost amount')
    key=billing_event_key(provider_account_reference,event_id)
    value={'operation_key':operation_key,'amount_microusd':amount_microusd,'currency':'USD'}
    if key in ledger and ledger[key]!=value:raise Rejected('Conflicting billing event')
    out=copy.deepcopy(ledger);out[key]=value
    if sum(x['amount_microusd'] for x in out.values())>9007199254740991:raise Rejected('Unsafe ledger total')
    return out
