"""Correct original pilot approved-manifest derivative into valid P01 schema
without mutating the original frozen P01 manifest or signed prior record.
Creates V2 approved derivative + separate HMAC scope record, independently
validated by P01 schema and exact three source file SHA identities.
"""
import hashlib,hmac,json,pathlib,subprocess,datetime
from zoneinfo import ZoneInfo
import runway_three_clip_pilot as p
import sign_p04_pilot_scope as prior
V2=p.OUT/"approved-manifest-derivative-v2.json"
RECORD=p.OUT/"signed-scope-authorization-v2.json"
SCHEMA=pathlib.Path.home()/"futureworks-studio/futureworks-p04-quality-v3/contracts/production-manifest/v1.0.0/production_manifest.schema.json"
def build():
    original=json.loads(p.MANIFEST.read_bytes())
    selected=p.input_assets()
    original["approval_state"]={
        "status":"approved","approved_revision":original["revision"],
        "approved_by":"project_owner_explicit_consent_in_conversation",
        "approval_record_id":"P04-P05-RUNWAY-PILOT-20261116-V2"}
    original["asset_references"]=[
      {"asset_id":selected[s]["asset_id"],"kind":"image",
        "status":"verified","scene_id":s,
        "file_uri":pathlib.Path(selected[s]["file"]).as_uri(),
        "sha256":selected[s]["sha256"],
        "source_reference":"original immutable P04_GPU_001 ComfyUI receipt"}
      for s in sorted(selected)]
    for scene in original["scenes"]:
        if scene["scene_id"] in selected:scene["asset_references"]=[selected[scene["scene_id"]]["asset_id"]]
    raw=prior.canonical(original)
    if V2.exists() or RECORD.exists():raise RuntimeError("V2 already exists")
    V2.write_bytes(raw)
    verify_contract()
    content={
       "human_consent_source":prior.RECORD.name,
       "previous_attestation_sha256":p.sha(prior.RECORD.read_bytes()),
       "approved_manifest_derivative_sha256":p.sha(raw),
       "original_manifest_sha256":p.sha(p.MANIFEST.read_bytes()),
       "selected_original_pngs":{s:selected[s]["sha256"] for s in sorted(selected)},
       "owner_scope":p.OWNER_APPROVAL,
       "expiry":"2026-11-17T23:59:00-05:00",
       "independent_owner_signature":False,
       "created_at":p.iso(),
       "production_approved":False,
       "publishing_approved":False,
       "operator_machine_attestation":True}
    key=prior.KEY.read_bytes()
    signed={**content,"hmac_sha256":hmac.new(key,prior.canonical(content),hashlib.sha256).hexdigest()}
    RECORD.write_bytes(prior.canonical(signed))
    verify()
    print("P01_SCHEMA_VALIDATED_APPROVED_DERIVATIVE_V2",p.sha(raw))
def verify_contract():
    result=subprocess.run(["python3",str(SCHEMA.with_name("validate_manifest.py")),str(SCHEMA),str(V2)],capture_output=True,text=True,timeout=25)
    if result.returncode:raise RuntimeError("Manifest schema failed "+result.stdout[:800])
def verify():
    prior.verify()
    verify_contract()
    r=json.loads(RECORD.read_bytes())
    mac=r.pop("hmac_sha256")
    if not hmac.compare_digest(mac,hmac.new(prior.KEY.read_bytes(),prior.canonical(r),hashlib.sha256).hexdigest()):
        raise RuntimeError("V2 scope signature mismatch")
    if r["approved_manifest_derivative_sha256"]!=p.sha(V2.read_bytes()) or r["previous_attestation_sha256"]!=p.sha(prior.RECORD.read_bytes()):
        raise RuntimeError("Source lineage broken")
    if r["owner_scope"]!=p.OWNER_APPROVAL:
        raise RuntimeError("Owner scope changed")
    if datetime.datetime.now(ZoneInfo("America/New_York"))>=datetime.datetime.fromisoformat(r["expiry"]):
        raise RuntimeError("Consent expired")
    print("P04_APPROVED_DERIVATIVE_V2_VALID_AND_SCOPE_VERIFIED")
if __name__=="__main__":
    import sys
    if sys.argv[1:]==["create"]:build()
    elif sys.argv[1:]==["verify"]:verify()
    else:raise SystemExit("create|verify")
