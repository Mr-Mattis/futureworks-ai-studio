"""P04 token-gated development-only image API for n8n ComfyUI orchestration.

Requires a real locally available AMD ComfyUI server. No paid services,
production worker, credentials in source, or identity generation.
"""
from __future__ import annotations
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading
import urllib.parse

from engine import Comfy, ImagePipeline, MANIFEST, MODEL, Rejected, verify_model

MAX_REQUEST = 8192
PROJECT = "FWAI-EP-0001"


def make_handler(database, output_root, model_file, secret, *, comfy=None):
    if not isinstance(secret, str) or len(secret) < 32:
        raise Rejected("P04 development requires strong independent bearer")
    service = ImagePipeline(database, output_root, comfy or Comfy())
    lock = threading.Lock()
    active = set()
    model_sha = verify_model(model_file)

    def process(run_id):
        try:
            ids = service.prepare(MANIFEST, run_id=run_id, model_sha=model_sha)
            for image_id in ids:
                state = next(row["state"] for row in
                             service.dashboard(run_id)["images"]
                             if row["image_id"] == image_id)
                if state == "queued":
                    service.submit_one(image_id)
                if state in ("submitting", "needs_review"):
                    return
                for _ in range(300):
                    current = service.poll_one(image_id)
                    if current == "complete":
                        break
                    threading.Event().wait(3.0)
                else:
                    return
            service.visual_handoff(run_id)
        except Exception:
            # Durable failed/submitting state remains for explicit review.
            # Never auto-retry potentially accepted Comfy prompts.
            pass
        finally:
            with lock:
                active.discard(run_id)

    class Handler(BaseHTTPRequestHandler):
        server_version = "FWAI-P04-DEV/1.0"

        def log_message(self, fmt, *args):
            return  # Never log tokens or full prompts.

        def respond(self, status, body):
            raw = json.dumps(body, sort_keys=True, allow_nan=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def authorized(self):
            value = self.headers.get("Authorization", "")
            if not hmac.compare_digest(value, "Bearer " + secret):
                self.respond(401, {"error":"UNAUTHORIZED"})
                return False
            return True

        def read_json(self):
            try:
                size = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc:
                raise Rejected("Invalid length") from exc
            if not (1 <= size <= MAX_REQUEST):
                raise Rejected("Invalid request size")
            if self.headers.get("Content-Type","").split(";")[0] != "application/json":
                raise Rejected("Expected application/json")
            def pairs(items):
                result = {}
                for k,v in items:
                    if k in result:
                        raise Rejected("Duplicate key")
                    result[k] = v
                return result
            value = json.loads(self.rfile.read(size), object_pairs_hook=pairs,
                               parse_constant=lambda x: (_ for _ in ()).throw(
                                   Rejected("Invalid JSON constant")))
            if not isinstance(value, dict):
                raise Rejected("Object required")
            return value

        def do_POST(self):
            if not self.authorized():
                return
            try:
                if urllib.parse.urlsplit(self.path).path != "/v1/start":
                    self.respond(404, {"error":"UNKNOWN_ROUTE"})
                    return
                request = self.read_json()
                if set(request) != {"project_id","run_id","manifest_sha256"} or (
                        request.get("project_id") != PROJECT or
                        request.get("manifest_sha256") !=
                        "cf2bbd17b2170755fef18de1be5ea4c08694ee894c8167c70ed322aa9906fe87"):
                    raise Rejected("Only frozen approved P01 concept accepted")
                run_id = request.get("run_id")
                ids = service.prepare(MANIFEST, run_id=run_id, model_sha=model_sha)
                with lock:
                    if run_id not in active:
                        active.add(run_id)
                        threading.Thread(target=process,args=(run_id,),
                                         daemon=True,name="fwai-p04-local-comfy-monitor").start()
                self.respond(202, {"state":"accepted_for_async_generation",
                                   "project_id":PROJECT,"run_id":run_id,
                                   "image_count":len(ids),"paid_provider_calls":0,
                                   "authorization":{"production_approved":False,
                                                    "spend_authorized":False,
                                                    "publish_authorized":False}})
            except (Rejected, ValueError, TypeError, OSError) as exc:
                self.respond(400, {"error":type(exc).__name__,
                                   "detail":str(exc)[:160]})

        def do_GET(self):
            if not self.authorized():
                return
            try:
                url = urllib.parse.urlsplit(self.path)
                if url.path == "/v1/health":
                    result = {"engine":"comfyui-local", "status":"development_only",
                              "model_sha256":model_sha, "paid_provider_calls":0,
                              "health":service.comfy.health()}
                elif url.path in ("/v1/status","/v1/visual-handoff"):
                    query = urllib.parse.parse_qs(url.query)
                    if set(query) != {"run_id"} or len(query["run_id"]) != 1:
                        raise Rejected("One exact run identifier required")
                    run_id = query["run_id"][0]
                    result = (service.dashboard(run_id) if url.path == "/v1/status"
                              else service.visual_handoff(run_id, save=False))
                else:
                    self.respond(404, {"error":"UNKNOWN_ROUTE"})
                    return
                self.respond(200, result)
            except (Rejected, ValueError, TypeError, OSError) as exc:
                self.respond(400, {"error":type(exc).__name__,
                                   "detail":str(exc)[:160]})

    return Handler


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database",required=True)
    parser.add_argument("--output",required=True)
    parser.add_argument("--model-file",required=True)
    parser.add_argument("--port",type=int,default=18741)
    parser.add_argument("--bind",default="127.0.0.1")
    parser.add_argument("--comfy-url",default="http://127.0.0.1:8188")
    args = parser.parse_args()
    if args.bind != "127.0.0.1" and os.getenv("P04_ALLOW_PRIVATE_BIND") != "1":
        raise SystemExit("Non-loopback binding requires explicit isolated opt-in")
    secret=os.getenv("P04_DEV_TOKEN","")
    handler=make_handler(args.database,args.output,args.model_file,secret,
                         comfy=Comfy(args.comfy_url))
    ThreadingHTTPServer((args.bind,args.port),handler).serve_forever()


if __name__ == "__main__":
    main()
