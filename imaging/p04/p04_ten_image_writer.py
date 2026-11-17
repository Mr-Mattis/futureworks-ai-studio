"""P04 ten-design authenticated local ComfyUI batch writer.

Restricted to one owner-requested, ten-image, local-only, zero-cost V5 run.
n8n protected Custom Auth bearer required. Atomic creation and no retries.
Windows ComfyUI stays loopback-only; launch Windows worker through local WSL
interop, never exposes ComfyUI or API secrets to the Internet.
"""
from __future__ import annotations
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from datetime import datetime,timezone
import hashlib,hmac,json,os,subprocess
HOME=Path.home()
ROOT=Path("/mnt/c/Users/yashi/Documents/futureworks-p04-data/collection-v5-ai-civilization")
TOKEN=HOME/".config/futureworks-ai-studio/secrets/p04_n8n_gateway_token"
SCRIPT=Path("/mnt/c/Users/yashi/Documents/futureworks-p04-data/generate_future_collection_v5.py")
RECEIPT=ROOT/"n8n-batch-acceptance.json"
JOURNAL=ROOT/"receipts.json"
ALLOWED={"operation":"create_local_photoreal_10","batch_id":"P04_V5_CIVILIAN_AI_001","image_count":10,"external_provider_calls_allowed":False,"publication_allowed":False}

def accepted():
    if not RECEIPT.exists():return {"status":"not_started","completed":0}
    record=json.loads(RECEIPT.read_text())
    if record.get("scope")!=ALLOWED:raise ValueError("Batch receipt changed")
    complete=0
    items=[]
    if JOURNAL.exists():
        records=json.loads(JOURNAL.read_text())
        for name,row in sorted(records.items()):
            if row.get("state")=="complete":
                f=ROOT/("FUT_"+name+"_1920x1080.png")
                if not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest()!=row.get("sha256"):
                    raise ValueError("Generated media checksum invalid")
                complete+=1
            items.append({"design_id":name,"state":row.get("state"),"sha256":row.get("sha256") if row.get("state")=="complete" else None})
    return {"status":"completed_pending_owner_visual_review" if complete==10 else "submitted_or_processing","completed":complete,"expected":10,
           "entries":items,"external_provider_calls":0,"published":False,"review":"HOLD","batch_id":ALLOWED["batch_id"]}

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def send(self,status,body):
        raw=json.dumps(body,separators=(",",":")).encode()
        self.send_response(status)
        self.send_header("Content-Type","application/json")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(raw)));self.end_headers();self.wfile.write(raw)
    def auth(self):
        if not TOKEN.is_file() or TOKEN.is_symlink():return False
        return hmac.compare_digest(self.headers.get("Authorization",""),"Bearer "+TOKEN.read_text().strip())
    def do_GET(self):
        if self.path=="/healthz":return self.send(200,{"status":"alive","provider_calls":0})
        if self.path!="/v1/batch/status":return self.send(404,{"error":"not_found"})
        if not self.auth():return self.send(401,{"error":"unauthorized"})
        try:self.send(200,accepted())
        except Exception:self.send(503,{"error":"evidence_rejected"})
    def do_POST(self):
        if self.path!="/v1/batch/start":return self.send(404,{"error":"not_found"})
        if not self.auth():return self.send(401,{"error":"unauthorized"})
        try:
            content_length=self.headers.get("Content-Length","")
            if not content_length.isdigit() or not 1<=int(content_length)<=512:
                return self.send(422,{"error":"bad_body"})
            payload=json.loads(self.rfile.read(int(content_length)))
            if payload!=ALLOWED:return self.send(422,{"error":"scope_rejected"})
            if RECEIPT.exists():return self.send(200,{**accepted(),"idempotent_replay":True})
            if not SCRIPT.is_file():return self.send(503,{"error":"worker_unavailable"})
            doc={"scope":ALLOWED,"state":"claimed_before_launch","created_at":datetime.now(timezone.utc).isoformat(),
                 "script_sha256":hashlib.sha256(SCRIPT.read_bytes()).hexdigest()}
            with RECEIPT.open("x") as f:
                json.dump(doc,f,indent=2);f.flush();os.fsync(f.fileno())
            # Blocking only for process creation, NEVER for image generation.
            py=r"C:\Users\yashi\Documents\futureworks-p04-comfyui\.venv\Scripts\python.exe"
            win_script=r"C:\Users\yashi\Documents\futureworks-p04-data\generate_future_collection_v5.py"
            log=r"C:\Users\yashi\Documents\futureworks-p04-data\collection-v5-ai-civilization\render.log"
            err=r"C:\Users\yashi\Documents\futureworks-p04-data\collection-v5-ai-civilization\render.err.log"
            command=f'Start-Process -FilePath \'{py}\' -ArgumentList \'{win_script}\' -WorkingDirectory \'C:\\Users\\yashi\\Documents\\futureworks-p04-data\' -RedirectStandardOutput \'{log}\' -RedirectStandardError \'{err}\' -PassThru | Select-Object -ExpandProperty Id'
            subprocess.Popen(["powershell.exe","-NoProfile","-Command",command],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
            # The durable receipt was claimed before spawn. A later status check
            # verifies the Windows worker started. Never POST a second job.
            self.send(202,{"status":"launched_once","batch_id":ALLOWED["batch_id"],"expected":10,"paid_calls":0,"production":False,"needs_owner_review":True})
        except FileExistsError:return self.send(200,{**accepted(),"idempotent_replay":True})
        except Exception:return self.send(503,{"error":"rejected_no_retry"})

if __name__=="__main__":
    ROOT.mkdir(parents=True,exist_ok=True)
    if not TOKEN.is_file():raise SystemExit("Protected n8n credential missing")
    print("P04 10-image local authenticated writer ready: 18743; Comfy loopback Windows only",flush=True)
    ThreadingHTTPServer(("0.0.0.0",18743),Handler).serve_forever()
