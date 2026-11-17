"""Local P04 owner-consent-bound pilot attestation.

No source manifest changes. Creates an approved DERIVATIVE under private owner PC,
with verified 3 immutable original reference hashes, scoped to this one authorized
Runway pilot. The machine HMAC protects integrity of the recorded consent; it is
NOT a claim that the human personally supplied a cryptographic signature.
"""
import hashlib,hmac,json,os,pathlib,secrets,sys,datetime
from zoneinfo import ZoneInfo
from runway_three_clip_pilot import (ROOT,OUT,BUNDLE,MANIFEST,PINNED,OWNER_APPROVAL,sha,iso)
KEY=pathlib.Path.home()/".config/futureworks-ai-studio/secrets/p04_pilot_attestation.key"
APPROVED=OUT/"approved-manifest-derivative.json"
RECORD=OUT/"signed-scope-authorization.json"
EXPIRY="2026-11-17T23:59:00-05:00"
def canonical(d):return json.dumps(d,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def build():
    import runway_three_clip_pilot as pilot
    selected=pilot.input_assets()
    original=json.loads(MANIFEST.read_text())
    original_sha=sha(MANIFEST.read_bytes())
    original["approval_state"]={
       "status":"approved","approved_revision":original["revision"],
       "approved_by":"project_owner_explicit_consent_in_conversation",
       "approval_record_id":"P04-P05-RUNWAY-PILOT-20261116"}
    original["asset_references"]=[{"asset_id":selected[s]["asset_id"],
                                   "sha256":selected[s]["sha256"],"scene_id":s} for s in sorted(selected)]
    # Keep a complete freeze of the original P01 fixture: only this derivative is amended.
    OUT.mkdir(parents=True,exist_ok=True)
    if APPROVED.exists() or RECORD.exists() or KEY.exists():
        raise RuntimeError("Scope artifacts already present; refusing independent regeneration")
    payload=canonical(original)
    approved_sha=sha(payload)
    now=datetime.datetime.now(ZoneInfo("America/New_York"))
    if now>=datetime.datetime.fromisoformat(EXPIRY):raise RuntimeError("Authorization expired")
    consent={
       "type":"owner_consent_machine_integrity_attestation_v1",
       "source_manifest_sha256":original_sha,"approved_derivative_sha256":approved_sha,
       "original_bundle_sha256":sha(BUNDLE.read_bytes()),
       "selected_asset_sha256":{s:selected[s]["sha256"] for s in sorted(selected)},
       "original_image_references":{s:selected[s]["asset_id"] for s in sorted(selected)},
       "human_source":"Owner explicitly approved creative manifest, confirmed rights, authorized selected three P04 image uploads to Runway for the $5 pilot in this conversation.",
       "owner_scope":OWNER_APPROVAL,"expiry":EXPIRY,"created_at":iso(),
       "independent_human_key_signature":False,
       "operator_attestation":"locally HMAC sealed based on explicit human consent",
       "production_approved":False,"publishing_approved":False}
    key=secrets.token_bytes(32)
    record=dict(consent,hmac_sha256=hmac.new(key,canonical(consent),hashlib.sha256).hexdigest())
    KEY.parent.mkdir(parents=True,exist_ok=True)
    with KEY.open("xb") as f:os.chmod(KEY,0o600);f.write(key)
    with APPROVED.open("xb") as f:f.write(payload)
    with RECORD.open("xb") as f:f.write(canonical(record))
    print("DERIVATIVE_SCOPE_CREATED SHA256",approved_sha)
    verify()
def verify():
    if not KEY.is_file() or not APPROVED.is_file() or not RECORD.is_file():
        raise RuntimeError("Scope authorization incomplete")
    record=json.loads(RECORD.read_text())
    mac=record.pop("hmac_sha256")
    key=KEY.read_bytes()
    if len(key)!=32 or not hmac.compare_digest(mac,hmac.new(key,canonical(record),hashlib.sha256).hexdigest()):
        raise RuntimeError("Scope attestation signature mismatch")
    if record["source_manifest_sha256"]!=sha(MANIFEST.read_bytes()) or record["approved_derivative_sha256"]!=sha(APPROVED.read_bytes()) or record["original_bundle_sha256"]!=sha(BUNDLE.read_bytes()):
        raise RuntimeError("Source/derivative bundle changed")
    approved=json.loads(APPROVED.read_text())
    if approved["approval_state"]["status"]!="approved" or approved["approval_state"]["approval_record_id"]!="P04-P05-RUNWAY-PILOT-20261116":
        raise RuntimeError("Derivative approval incomplete")
    if record["owner_scope"]!=OWNER_APPROVAL or record["selected_asset_sha256"]!={s:PINNED[s][1] for s in sorted(PINNED)}:
        raise RuntimeError("Scope mismatch")
    if datetime.datetime.now(datetime.timezone.utc) >= datetime.datetime.fromisoformat(record["expiry"]):
        raise RuntimeError("Pilot authorization expired")
    from runway_three_clip_pilot import input_assets
    input_assets()
    print("OWNER_SCOPED_CONSENT_AND_ASSET_HASHES_VERIFIED; expires",record["expiry"])
if __name__=="__main__":
    if sys.argv[1:] == ["create"]:build()
    elif sys.argv[1:] == ["verify"]:verify()
    else:raise SystemExit("Usage: ... create|verify")
