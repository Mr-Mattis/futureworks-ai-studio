"""Fail-closed scoped P04 real-provider pilot regression tests; no network."""
import copy,datetime,hashlib,hmac,json,pathlib,tempfile,unittest
from scoped_review_gate import verify_scoped_pilot,Rejected,canon,sha
REPO=pathlib.Path(__file__).resolve().parents[2]
SOURCE=REPO/"contracts/production-manifest/v1.0.0/example.valid.json"
SCHEMA=REPO/"contracts/production-manifest/v1.0.0/production_manifest.schema.json"
KEY=bytes(range(32))
class ScopedPilotTests(unittest.TestCase):
 def setUp(self):
    self.tmp=tempfile.TemporaryDirectory()
    self.addCleanup(self.tmp.cleanup)
    self.root=pathlib.Path(self.tmp.name)
    self.images=self.root/"images";self.images.mkdir()
    self.original=self.root/"manifest-original.json"
    self.original.write_bytes(SOURCE.read_bytes())
    self.bundle=self.root/"bundle.json"
    self.manifest=self.root/"manifest-approved.json"
    self.old=self.root/"prior-record.json";self.old.write_text('{"prior":"retained"}')
    self.scope=self.root/"scope.json"
    original=json.loads(SOURCE.read_bytes())
    approved=copy.deepcopy(original)
    approved["approval_state"]={"status":"approved","approved_revision":original["revision"],"approved_by":"project_owner_explicit_consent_in_conversation","approval_record_id":"P04-P05-RUNWAY-PILOT-20261116-V2"}
    selected={}
    entries=[]
    approved["asset_references"]=[]
    for i in range(1,11):
        name=f"P04_SYNTH_{i:02d}"
        scene=f"S0{(i-1)//2+1}"
        data=b"\x89PNG\r\n\x1a\n"+bytes([i])*100
        digest=sha(data)
        entries.append({"scene_id":scene,"asset_id":name,"sha256":digest})
        if i in (1,3,5):
            (self.images/(name+".png")).write_bytes(data)
            selected[scene]=digest
            approved["asset_references"].append({"asset_id":name,"kind":"image","status":"verified","scene_id":scene,"file_uri":(self.images/(name+".png")).as_uri(),"sha256":digest,"source_reference":"synthetic verified P04"})
            approved["scenes"][(i-1)//2]["asset_references"]=[name]
    self.manifest.write_bytes(canon(approved))
    self.bundle.write_text(json.dumps({"status":"ready_for_visual_director","assets_count":10,"project_id":original["project_id"],"assets":entries}))
    scope={"human_consent_source":"owner message",
           "previous_attestation_sha256":sha(self.old.read_bytes()),
           "approved_manifest_derivative_sha256":sha(self.manifest.read_bytes()),
           "original_manifest_sha256":sha(self.original.read_bytes()),
           "selected_original_pngs":selected,
           "owner_scope":{"external_provider":"Runway Developer API","model":"gen4.5","clip_count":3,"duration_seconds_each":5,"maximum_credits":500,"maximum_dollars_usd":"5.00","no_paid_retries":True,"publish_authorized":False,"production_activation_authorized":False,"rights_confirmed_by_owner":True},
           "expiry":"2099-11-17T23:59:00-05:00",
           "production_approved":False,"publishing_approved":False}
    self.write_signed(scope)
 def write_signed(self,record):
    signed=dict(record,hmac_sha256=hmac.new(KEY,canon(record),hashlib.sha256).hexdigest())
    self.scope.write_bytes(canon(signed))
 def call(self,**overrides):
    kwargs=dict(original_manifest=self.original,approved_derivative=self.manifest,scope_record=self.scope,previous_scope_record=self.old,bundle=self.bundle,asset_dir=self.images,key_bytes=KEY,schema_path=SCHEMA)
    kwargs.update(overrides)
    return verify_scoped_pilot(**kwargs)
 def test_valid_scoped_three_asset_pilot(self):
    verdict=self.call()
    self.assertEqual(verdict["verified_assets"],3)
    self.assertEqual(verdict["max_credits"],500)
    self.assertFalse(verdict["publish_authorized"])
 def test_modified_owner_budget_without_resign_fails(self):
    record=json.loads(self.scope.read_text());record["owner_scope"]["maximum_credits"]=1000
    self.scope.write_text(json.dumps(record))
    with self.assertRaises(Rejected):self.call()
 def test_expired_authorization_fails_even_if_signed(self):
    record=json.loads(self.scope.read_text());record.pop("hmac_sha256")
    record["expiry"]="2020-01-01T00:00:00-05:00"
    self.write_signed(record)
    with self.assertRaises(Rejected):self.call()
 def test_changed_media_sha_fails(self):
    (self.images/"P04_SYNTH_01.png").write_bytes(b"different bytes")
    with self.assertRaises(Rejected):self.call()
 def test_derivative_schema_violation_fails(self):
    manifest=json.loads(self.manifest.read_text())
    manifest["asset_references"][0].pop("kind")
    self.manifest.write_bytes(canon(manifest))
    with self.assertRaises(Rejected):self.call()
 def test_invalid_source_or_chain_fails(self):
    self.old.write_bytes(b"different prior")
    with self.assertRaises(Rejected):self.call()
if __name__=="__main__":unittest.main()
