"""Isolated authenticated P05 camera-intent preview service.

Reads pinned 90-term catalog + original local P04 references. Read-only,
development only; no AI inference, new media uploads, or paid Runway requests.
"""
from __future__ import annotations
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import hmac,json,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from camera_scene_adapter import planned_camera_scene_intents,CATALOG
ROOT=Path("/mnt/c/Users/yashi/Documents/futureworks-p04-data/images")
BUNDLE=ROOT/"VISUAL_DIRECTOR_HANDOFF_P04_GPU_001.json"
TOKEN=Path.home()/".config/futureworks-ai-studio/secrets/p04_n8n_gateway_token"

def previews():
    plans=planned_camera_scene_intents(BUNDLE,catalog_path=CATALOG)
    if len(plans)!=3:raise ValueError("Exactly three scene plans expected")
    return {"schema":"FWAI_CAMERA_PLAN_PREVIEW_1","catalog_version":"1.0",
            "scene_count":3,"scenes":[{"scene_id":p["scene_id"],"camera_codes":p["cinematography"]["camera_codes"],
             "camera_instruction":p["cinematography"]["instruction"],"reference_sha256":p["reference_sha256"],
             "duration_seconds":p["duration"],"provider_submit":False,"publish_authorized":False} for p in plans],
            "paid_provider_calls":0,"production_activated":False,"publication_authorized":False}

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def send(self,status,obj):
        body=json.dumps(obj,separators=(",",":")).encode()
        self.send_response(status)
        self.send_header("Content-Type","application/json")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        if self.path=="/healthz":return self.send(200,{"status":"alive","paid_calls":0})
        if self.path!="/v1/camera/plans":return self.send(404,{"error":"not_found"})
        if not TOKEN.is_file():return self.send(503,{"error":"credential_unavailable"})
        auth=self.headers.get("Authorization","")
        if not hmac.compare_digest(auth,"Bearer "+TOKEN.read_text().strip()):
            return self.send(401,{"error":"unauthorized"})
        try:return self.send(200,previews())
        except Exception:return self.send(503,{"error":"preview_failed"})
    def do_POST(self):return self.send(405,{"error":"read_only"})

if __name__=="__main__":
    if not TOKEN.is_file():raise SystemExit("Isolated credential unavailable")
    print("P05 camera preview ready on 18742: GET only, authenticated, no paid operations",flush=True)
    ThreadingHTTPServer(("0.0.0.0",18742),Handler).serve_forever()
