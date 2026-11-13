import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from jsonschema import Draft202012Validator
from recovery import *
from simulate_recovery import identity

class RecoveryTests(unittest.TestCase):
    def new(self,**kw):return create(identity(),1000,reservation_record_id='synthetic-reservation',**kw)
    def dispatched(self,**kw):return begin_action(self.new(**kw),1000,authorization_valid=True,writer_owned=True)[0]
    def accepted(self):return observe(self.dispatched(),'accepted',1001,provider_job_id='mock-job')

    def test_schemas(self):
        for schema in (IDENTITY_SCHEMA,SNAPSHOT_SCHEMA):Draft202012Validator.check_schema(schema)

    def test_identity_stable_and_every_input_bound(self):
        i=identity();k=operation_key(i)
        self.assertEqual(k,operation_key(dict(reversed(list(i.items())))))
        for field in ('job_id','scene_id','provider','provider_account_reference','operation','model_version','request_sha256','input_asset_sha256','generation_intent','manifest_ref'):
            with self.subTest(field=field):
                j=copy.deepcopy(i)
                if field=='manifest_ref':j[field]['revision']=2
                elif field=='request_sha256':j[field]='d'*64
                elif field=='input_asset_sha256':j[field]=['d'*64]
                elif field=='scene_id':j[field]='S02'
                else:j[field]+='-changed'
                self.assertNotEqual(k,operation_key(j))

    def test_no_authorization_reservation_or_writer_no_submit(self):
        for auth,owned in [(False,True),(True,False),(False,False)]:
            self.assertNotIn(decide(self.new(),1000,authorization_valid=auth,writer_owned=owned),('submit_new','replay_same_key'))
        s=create(identity(),1000)
        self.assertEqual(decide(s,1000,authorization_valid=True,writer_owned=True),'manual_review')

    def test_write_ahead_attempt_before_send(self):
        before=self.new();after,action=begin_action(before,1000,authorization_valid=True,writer_owned=True)
        self.assertEqual(action,'submit_new');self.assertEqual(after['status'],'dispatching');self.assertEqual(after['submit_attempts'],1)
        self.assertEqual(before['submit_attempts'],0)
        self.assertEqual(decide(after,1001,authorization_valid=True,writer_owned=True),'wait')

    def test_ambiguous_failure_never_blind_retries(self):
        s=observe(self.dispatched(),'unknown_submission_outcome',1060)
        self.assertEqual(decide(s,1060,authorization_valid=True,writer_owned=True),'reconcile_by_key')
        s['submit_attempts']=3
        self.assertEqual(decide(s,1060,authorization_valid=True,writer_owned=True),'reconcile_by_key')
        self.assertEqual(s['reservation_record_id'],'synthetic-reservation')

    def test_native_replay_requires_valid_contract_window_and_same_key(self):
        s=self.dispatched(adapter_contract_reference='synthetic-verified-contract',idempotency_guaranteed_until=2000)
        out,action=begin_action(s,1060,authorization_valid=True,writer_owned=True)
        self.assertEqual(action,'replay_same_key');self.assertEqual(out['operation_key'],s['operation_key'])
        for now in [1911,2000]:self.assertEqual(decide(s,now,authorization_valid=True,writer_owned=True),'reconcile_by_key')
        self.assertEqual(decide(s,1060,authorization_valid=False,writer_owned=True),'reconcile_by_key')

    def test_confirmed_nonacceptance_backoff_and_three_attempt_limit(self):
        s=self.dispatched();now=1001
        for attempt in (1,2,3):
            s=observe(s,'definitively_not_accepted',now,evidence_reference='synthetic-negative-receipt')
            self.assertEqual(decide(s,now,authorization_valid=True,writer_owned=True),'wait')
            now=s['not_before']
            out,action=begin_action(s,now,authorization_valid=True,writer_owned=True)
            if attempt<3:
                self.assertEqual(action,'retry_confirmed_unaccepted');s=out;now+=1
            else:self.assertEqual(action,'manual_review')
        with self.assertRaises(Rejected):observe(self.dispatched(),'definitively_not_accepted',1001)

    def test_retry_after_never_shortened(self):
        self.assertEqual(backoff(1,retry_after_seconds=900),900)
        self.assertEqual(backoff(2,jitter_seconds=5),15)
        self.assertEqual(backoff(100),300)
        for value in [-1,'30',True]:
            with self.assertRaises(Rejected):backoff(1,retry_after_seconds=value)

    def test_known_job_poll_never_regenerates(self):
        s=self.accepted()
        out,action=begin_action(s,1001,writer_owned=True)
        self.assertEqual(action,'poll_existing_job');self.assertEqual(out['submit_attempts'],1)
        self.assertEqual(out['provider_job_id'],'mock-job')
        s['poll_requests']=120
        self.assertEqual(decide(s,1001,writer_owned=True),'manual_review')

    def test_deadline_and_clock_rollback_stop_automation(self):
        for s in (self.new(),self.dispatched(),self.accepted()):
            self.assertEqual(decide(s,4600,authorization_valid=True,writer_owned=True),'manual_review')
            self.assertEqual(decide(s,999,authorization_valid=True,writer_owned=True),'manual_review')
        with self.assertRaises(Rejected):observe(self.accepted(),'provider_pending',999)

    def test_provider_failure_requires_new_intent(self):
        s=observe(self.accepted(),'provider_failed',1002)
        self.assertEqual(decide(s,1002,authorization_valid=True,writer_owned=True),'manual_review')
        self.assertEqual(s['submit_attempts'],1);self.assertIsNotNone(s['reservation_record_id'])

    def test_download_retries_same_job_bounded(self):
        s=observe(self.accepted(),'provider_succeeded',1002);now=1002
        for attempt in (1,2,3):
            s,action=begin_action(s,now,writer_owned=True)
            self.assertEqual(action,'download_existing_asset');self.assertEqual(s['submit_attempts'],1)
            s=observe(s,'download_retry',now+1);now=s['not_before']
        self.assertEqual(decide(s,now,writer_owned=True),'manual_review')
        self.assertEqual(s['provider_job_id'],'mock-job')

    def test_verified_result_reused_without_new_generation(self):
        s=observe(self.accepted(),'provider_succeeded',1002)
        s,_=begin_action(s,1002,writer_owned=True)
        s=observe(s,'artifact_verified',1003,sha256='d'*64)
        self.assertEqual(decide(s,5000),'reuse_verified_result')
        self.assertEqual(s['submit_attempts'],1)

    def test_cancellation_keeps_reservation(self):
        s=observe(self.dispatched(),'cancelled',1001)
        self.assertEqual(decide(s,1002,authorization_valid=True,writer_owned=True),'manual_review')
        self.assertEqual(s['reservation_record_id'],'synthetic-reservation')

    def test_duplicate_billing_event_applied_once_conflict_rejected(self):
        args=dict(provider_account_reference='mock-account',event_id='mock-event',operation_key=operation_key(identity()),amount_microusd=250000)
        ledger=apply_charge({},**args)
        again=apply_charge(ledger,**args);self.assertEqual(again,ledger);self.assertEqual(len(again),1)
        with self.assertRaises(Rejected):apply_charge(ledger,**{**args,'amount_microusd':250001})
        for amount in [-1,True,1.5,9007199254740992]:
            with self.assertRaises(Rejected):apply_charge({},**{**args,'amount_microusd':amount})

    def test_invalid_snapshot_and_events_rejected(self):
        for key,value in [('operation_key','wrong'),('deadline_at',99999),('status','approved'),('submit_attempts',4),('adapter_contract_reference','unpaired')]:
            s=self.new();s[key]=value
            with self.subTest(field=key):
                with self.assertRaises(Rejected):validate(s)
        with self.assertRaises(Rejected):observe(self.new(),'provider_succeeded',1001)
        with self.assertRaises(Rejected):observe(self.new(),'artifact_verified',1001,sha256='d'*64)

    def test_real_process_interruption_and_repeated_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            cmd=[sys.executable,str(ROOT/'simulate_recovery.py')]
            env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
            crashed=subprocess.run(cmd+['crash',directory],capture_output=True,env=env)
            self.assertEqual(crashed.returncode,17)
            for expected in ('reconciled_existing_job','reuse_verified_result'):
                recovered=subprocess.run(cmd+['recover',directory],capture_output=True,text=True,env=env)
                self.assertEqual(recovered.returncode,0,recovered.stderr)
                report=json.loads(recovered.stdout)
                self.assertEqual(report['action'],expected)
                self.assertEqual(report['submissions'],1);self.assertEqual(report['billable_events'],1);self.assertEqual(report['recorded_charge_events'],1)

if __name__=='__main__':unittest.main(verbosity=2)
