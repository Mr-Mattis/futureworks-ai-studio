"""P04 scoped external-provider pilot verification, fail closed.

Independent of the legacy locked P04 manifest verifier. Validates one locally
HMAC-sealed owner-consent scope and a P01-schema-valid approved derivative,
without elevating it to production, publication or any blanket rights grant.

Machine HMAC attestation proves integrity of a recorded owner decision, not
an independently human-operated private-key signature.
"""
from __future__ import annotations
import datetime,hashlib,hmac,json,pathlib
from zoneinfo import ZoneInfo
from jsonschema import Draft202012Validator

def canon(d):return json.dumps(d,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
class Rejected(ValueError):pass
def verify_scoped_pilot(*,original_manifest,approved_derivative,scope_record,
                        previous_scope_record,bundle,asset_dir,key_bytes,
                        schema_path,now=None):
    original_manifest=pathlib.Path(original_manifest)
    approved_derivative=pathlib.Path(approved_derivative)
    scope_record=pathlib.Path(scope_record)
    previous_scope_record=pathlib.Path(previous_scope_record)
    bundle=pathlib.Path(bundle)
    asset_dir=pathlib.Path(asset_dir)
    if not isinstance(key_bytes,bytes) or len(key_bytes)!=32:raise Rejected("Invalid private verifier key")
    try:
        signed=json.loads(scope_record.read_bytes())
        signature=signed.pop("hmac_sha256")
        expected=hmac.new(key_bytes,canon(signed),hashlib.sha256).hexdigest()
        if not isinstance(signature,str) or not hmac.compare_digest(signature,expected):
            raise Rejected("Cryptographic owner-scope record integrity check failed")
        expires=datetime.datetime.fromisoformat(signed["expiry"])
        when=now or datetime.datetime.now(datetime.timezone.utc)
        if expires.tzinfo is None or when>=expires:raise Rejected("Pilot consent has expired")
        if signed["original_manifest_sha256"]!=sha(original_manifest.read_bytes()) or signed["approved_manifest_derivative_sha256"]!=sha(approved_derivative.read_bytes()):
            raise Rejected("Manifest identity mismatch")
        if signed["previous_attestation_sha256"]!=sha(previous_scope_record.read_bytes()):
            raise Rejected("Review record chain broken")
        original=json.loads(original_manifest.read_bytes())
        approved=json.loads(approved_derivative.read_bytes())
        schema=json.loads(pathlib.Path(schema_path).read_bytes())
        if list(Draft202012Validator(schema).iter_errors(approved)):raise Rejected("Approved derivative violates P01 schema")
        if original["approval_state"]["status"]!="pending_review":
            raise Rejected("Original P01 evidence must remain immutable/pending")
        if approved["approval_state"]["status"]!="approved" or approved["project_id"]!=original["project_id"]:
            raise Rejected("No approved derivative for the original project")
        if approved["revision"]!=original["revision"] or approved["approval_state"]["approved_revision"]!=approved["revision"]:
            raise Rejected("Approved revision mismatch")
        if approved["approval_state"]["approval_record_id"]!="P04-P05-RUNWAY-PILOT-20261116-V2":
            raise Rejected("Wrong pilot approval identity")
        policy=signed["owner_scope"]
        if policy.get("external_provider")!="Runway Developer API" or policy.get("model")!="gen4.5" or policy.get("clip_count")!=3 or policy.get("duration_seconds_each")!=5 or policy.get("maximum_credits")!=500 or policy.get("maximum_dollars_usd")!="5.00" or not policy.get("no_paid_retries"):
            raise Rejected("Pilot model, duration, provider or budget exceeded scope")
        if signed.get("production_approved") is not False or signed.get("publishing_approved") is not False:
            raise Rejected("Unsafe publication/production flags")
        if policy.get("publish_authorized") is not False or policy.get("production_activation_authorized") is not False or not policy.get("rights_confirmed_by_owner"):
            raise Rejected("Missing bounded human rights authority")
        selected=signed["selected_original_pngs"]
        if set(selected)!={"S01","S02","S03"}:raise Rejected("Only three locked scenes permitted")
        evidence=json.loads(bundle.read_bytes())
        if evidence.get("status")!="ready_for_visual_director" or evidence.get("assets_count")!=10:
            raise Rejected("Original P04 handoff invalid")
        if evidence.get("project_id")!=original["project_id"]:
            raise Rejected("Original P04 project mismatch")
        references={a["scene_id"]:a for a in approved.get("asset_references",[])}
        if set(references)!=set(selected):raise Rejected("Derivative references differ from owner-scope records")
        for scene,digest in selected.items():
            ref=references[scene]
            if ref.get("kind")!="image" or ref.get("status")!="verified" or ref.get("sha256")!=digest:
                raise Rejected("Wrong approved source asset")
            listed=[a for a in evidence["assets"] if a["scene_id"]==scene and a["asset_id"]==ref["asset_id"]]
            if len(listed)!=1 or listed[0]["sha256"]!=digest:
                raise Rejected("No exact original provenance for "+scene)
            source=asset_dir/(ref["asset_id"]+".png")
            if not source.is_file() or sha(source.read_bytes())!=digest:
                raise Rejected("Original source bytes changed for "+scene)
        return {"status":"verified_scoped_owner_pilot_consent",
                "approved_derivative_sha256":sha(approved_derivative.read_bytes()),
                "verified_assets":3,"provider":"Runway Developer API",
                "max_credits":500,"publish_authorized":False,"production_approved":False}
    except (KeyError,TypeError,ValueError,json.JSONDecodeError) as exc:
        if isinstance(exc,Rejected):raise
        raise Rejected("Invalid scoped consent evidence") from exc
