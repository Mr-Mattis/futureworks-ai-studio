"""P04 restricted authenticated local n8n handoff service — no model/paid calls.

Only the exact signed, P01-schema-valid three-original-image Runway pilot
scope is eligible. This is an isolated reference intake writer, NOT a
production Comfy generation gateway or publication pathway.
"""
from __future__ import annotations
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import hashlib,hmac,json,os,sys,datetime
from zoneinfo import ZoneInfo

HOME=Path.home()
REPO=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO/"imaging/p04"))
sys.path.insert(0,str(REPO/"video/p05"))
from scoped_review_gate import verify_scoped_pilot, Rejected
import importlib.util
p05_spec=importlib.util.spec_from_file_location('fwai_p05_engine',REPO/'video/p05/engine.py')
p05_engine=importlib.util.module_from_spec(p05_spec)
p05_spec.loader.exec_module(p05_engine)
make_scene_requests=p05_engine.make_scene_requests

ROOT=Path("/mnt/c/Users/yashi/Documents/futureworks-p04-data/images")
OUT=Path("/mnt/c/Users/yashi/Documents/futureworks-p05-data/real-runway-pilot-001")
SECRET=HOME/".config/futureworks-ai-studio/secrets/p04_n8n_gateway_token"
OWNER_KEY=HOME/".config/futureworks-ai-studio/secrets/p04_pilot_attestation.key"
SCHEMA=REPO/"contracts/production-manifest/v1.0.0/production_manifest.schema.json"
MANIFEST=REPO/"contracts/production-manifest/v1.0.0/example.valid.json"
DERIVATIVE=OUT/"approved-manifest-derivative-v2.json"
SCOPE=OUT/"signed-scope-authorization-v2.json"
PREVIOUS=OUT/"signed-scope-authorization.json"
BUNDLE=ROOT/"VISUAL_DIRECTOR_HANDOFF_P04_GPU_001.json"
RECEIPT=OUT/"P04_AUTHENTICATED_N8N_REFERENCE_HANDOFF.json"
EXPECTED_SHA="ac14488fd251d88d5ffaa0ad47aa7c4010274d2e4597bc29519a16b57e08ebad"

def verified_reference_handoff(payload):
    if not isinstance(payload,dict) or set(payload)!={"project_id","run_id","manifest_sha256","operation"}:
        raise Rejected("Strict four-field handoff request required")
    if payload!={"project_id":"FWAI-EP-0001","run_id":"P04_GPU_001",
                "manifest_sha256":EXPECTED_SHA,
                "operation":"approved_reference_handoff"}:
        raise Rejected("Only original P04 owner-authorized scope is eligible")
    evidence=verify_scoped_pilot(
        original_manifest=MANIFEST,approved_derivative=DERIVATIVE,
        scope_record=SCOPE,previous_scope_record=PREVIOUS,bundle=BUNDLE,
        asset_dir=ROOT,key_bytes=OWNER_KEY.read_bytes(),schema_path=SCHEMA)
    if evidence["approved_derivative_sha256"]!=EXPECTED_SHA or evidence["verified_assets"]!=3:
        raise Rejected("Approved image hash lineage mismatch")
    plans=make_scene_requests(BUNDLE)
    signed=json.loads(SCOPE.read_bytes())
    authorized=signed["selected_original_pngs"]
    if set(authorized)!={"S01","S02","S03"}:raise Rejected("Wrong authorized scenes")
    selected=[]
    for item in plans:
        scene=item["scene_id"]
        if item["reference_sha256"]!=authorized[scene]:
            raise Rejected("P05 reference hash differs from owner authorization")
        selected.append({"scene_id":scene,"reference_asset_id":item["reference_asset_id"],
                        "reference_sha256":item["reference_sha256"],
                        "reference_local_path":item["reference_local_path"],
                        "provider_submit":False,"needs_human_review":True})
    return {"status":"ACCEPTED_AUTHENTICATED_OWNER_SCOPED_REFERENCE_HANDOFF",
            "project_id":payload["project_id"],"run_id":payload["run_id"],
            "approved_derivative_sha256":EXPECTED_SHA,"image_count":len(selected),
            "scene_references":selected,"paid_provider_calls":0,
            "production_activated":False,"publication_authorized":False}

def persist_once(result):
    OUT.mkdir(parents=True,exist_ok=True)
    serialized=json.dumps(result,sort_keys=True,indent=2).encode()
    if RECEIPT.exists():
        if RECEIPT.read_bytes()!=serialized:raise Rejected("Immutable receipt already exists with different bytes")
        return False
    # An accidental concurrent duplicate must fail closed, not overwrite.
    try:
        with RECEIPT.open("xb") as f:
            f.write(serialized);f.flush();os.fsync(f.fileno())
    except FileExistsError:
        if RECEIPT.read_bytes()!=serialized:raise Rejected("Concurrent receipt mismatch")
        return False
    return True

class Handler(BaseHTTPRequestHandler):
    def log_message(self,format,*args):pass  # Do not log headers, tokens, paths or media.
    def send(self,status,body):
        raw=json.dumps(body,separators=(",",":")).encode()
        self.send_response(status);self.send_header("Content-Type","application/json")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(raw)));self.end_headers();self.wfile.write(raw)
    def do_GET(self):
        if self.path=="/healthz":self.send(200,{"status":"alive","paid_calls":0,"production":False})
        else:self.send(404,{"error":"not_found"})
    def do_POST(self):
        if self.path!="/v1/start":
            self.send(404,{"error":"not_found"});return
        try:
            if not SECRET.is_file() or SECRET.is_symlink():raise Rejected("Missing isolated managed secret")
            configured=SECRET.read_text().strip()
            authorization=self.headers.get("Authorization","")
            if len(configured)<32 or not hmac.compare_digest(authorization,"Bearer "+configured):
                self.send(401,{"error":"unauthorized"});return
            length=self.headers.get("Content-Length","")
            if not length.isdecimal() or not 1<=int(length)<=2048:
                raise Rejected("Strict bounded request size required")
            request=json.loads(self.rfile.read(int(length)))
            result=verified_reference_handoff(request)
            created=persist_once(result)
            self.send(201 if created else 200,{**result,"idempotent_replay":not created})
        except (Rejected,ValueError,KeyError,OSError,json.JSONDecodeError) as exc:
            # Never reveal private filesystem paths or signature details in HTTP.
            self.send(422,{"error":"scope_or_approval_rejected"})
        except Exception:
            self.send(503,{"error":"internal_rejection"})

if __name__=="__main__":
    if not SECRET.is_file():raise SystemExit("Provision secret independently before startup")
    if not OWNER_KEY.is_file():raise SystemExit("Missing owner-scoped signing record key")
    print("FWAI P04 authenticated reference handoff ready: 0.0.0.0:18741; no external writes",flush=True)
    ThreadingHTTPServer(("0.0.0.0",18741),Handler).serve_forever()
