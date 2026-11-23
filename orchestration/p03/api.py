"""Authorized local HTTP bridge for P03 development ONLY.

POST /v1/intake: validate immutable brief; create durable seven-stage work.
POST /v1/drive: automatic orchestration from the accepted brief.
GET /v1/dashboard?project_id=...&run_id=...: zero-cost progress report.
All endpoints require strong bearer token. Bind to loopback unless explicitly
configured otherwise; never import production worker or providers.

The default model is ReplayModel (synthetic integration replay). Fresh Ollama
inference requires a separate P03_LIVE_LOCAL_OLLAMA=1 development flag.
"""
from __future__ import annotations

import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from engine import REPO, Rejected, Studio
from model import OllamaModel, ReplayModel

PLAN = REPO / "agents/executive_producer/reconciliation/execution-54.json"
MANIFEST = REPO / "contracts/production-manifest/v1.0.0/example.valid.json"
MAX_BODY = 8192


def service(database, bearer_secret, *, live_model=False, demo_enabled=False):
    if not isinstance(bearer_secret, str) or len(bearer_secret) < 32:
        raise Rejected("P03 development bearer token must be >= 32 characters")
    studio = Studio(database)
    plan = json.loads(PLAN.read_text())["handoff"]["candidate"]
    model = OllamaModel() if live_model else ReplayModel()
    ref = __import__("hashlib").sha256(MANIFEST.read_bytes()).hexdigest()

    class Handler(BaseHTTPRequestHandler):
        server_version = "FWAI-P03-DEV/1.0"

        def log_message(self, fmt, *args):
            # Never log bearer tokens, full user content, paths or request body.
            return

        def _authorized(self):
            claimed = self.headers.get("Authorization", "")
            expected = "Bearer " + bearer_secret
            if not hmac.compare_digest(claimed, expected):
                self._send(401, {"error": "UNAUTHORIZED"})
                return False
            return True

        def _send(self, status, data):
            raw = json.dumps(data, sort_keys=True, allow_nan=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def _read(self):
            try:
                n = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc:
                raise Rejected("Malformed content length") from exc
            if not 0 < n <= MAX_BODY:
                raise Rejected("Invalid intake size")
            if self.headers.get("Content-Type", "").split(";")[0].lower() != "application/json":
                raise Rejected("JSON content type required")
            def reject_pairs(pairs):
                output = {}
                for k, v in pairs:
                    if k in output:
                        raise Rejected("Duplicate JSON keys forbidden")
                    output[k] = v
                return output
            data = json.loads(self.rfile.read(n), object_pairs_hook=reject_pairs,
                              parse_constant=lambda x: (_ for _ in ()).throw(
                                  Rejected("Non-finite number")))
            if not isinstance(data, dict):
                raise Rejected("Object required")
            return data

        @staticmethod
        def _identity(req):
            allowed = {"project_id", "run_id"}
            if not allowed.issubset(req):
                raise Rejected("Missing run identity")
            return req["project_id"], req["run_id"]

        def do_POST(self):
            # One-shot synthetic intake for a controlled real n8n transport test.
            # Not authentication, not a general API; disabled by default and
            # hard-pinned to a single immutable no-provider replay. Stop after test.
            if urlparse(self.path).path == "/v1/demo-once":
                if not demo_enabled:
                    self._send(404, {"error": "DEMO_DISABLED"})
                    return
                try:
                    request = self._read()
                    expected = {
                        "project_id": "FWAI-EP-0001",
                        "run_id": "P03-DEV-N8N-ONE-SHOT-001",
                        "manifest_sha256": ref,
                        "brief": "The PC That Became a Robot — clearly fictional concept.",
                    }
                    if request != expected or any(type(request[k]) is not str for k in expected):
                        raise Rejected("Only the frozen one-shot development fixture is accepted")
                    receipt = studio.submit(MANIFEST, plan, expected["run_id"], expected["brief"])
                    report = studio.drive(expected["project_id"], expected["run_id"], ReplayModel())
                    self._send(200, {"mode": "one_shot_synthetic_replay",
                                     "receipt": receipt, "dashboard": report})
                except (Rejected, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
                    self._send(400, {"error": type(exc).__name__, "detail": str(exc)[:160]})
                return
            if not self._authorized():
                return
            try:
                request = self._read()
                path = urlparse(self.path).path
                if path == "/v1/intake":
                    if set(request) != {"project_id", "run_id", "manifest_sha256", "brief"}:
                        raise Rejected("Unexpected intake fields")
                    if request["project_id"] != "FWAI-EP-0001" or request["manifest_sha256"] != ref:
                        raise Rejected("Unknown frozen project or exact manifest hash")
                    result = studio.submit(MANIFEST, plan, request["run_id"], request["brief"])
                    self._send(200, result)
                elif path == "/v1/drive":
                    if set(request) != {"project_id", "run_id"}:
                        raise Rejected("Unexpected drive fields")
                    project, run_id = self._identity(request)
                    result = studio.drive(project, run_id, model)
                    self._send(200, result)
                elif path == "/v1/reserve-mock":
                    if set(request) != {"project_id", "run_id", "operation_key"}:
                        raise Rejected("Unexpected mock reservation fields")
                    project, run_id = self._identity(request)
                    result = studio.reserve_mock(project, run_id, request["operation_key"])
                    self._send(200, {"status": result, "provider_submission_performed": False})
                else:
                    self._send(404, {"error": "UNKNOWN_ROUTE"})
            except (Rejected, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
                self._send(400, {"error": type(exc).__name__, "detail": str(exc)[:160]})

        def do_GET(self):
            if not self._authorized():
                return
            try:
                url = urlparse(self.path)
                query = parse_qs(url.query)
                if url.path == "/v1/dashboard":
                    if set(query) != {"project_id", "run_id"}:
                        raise Rejected("Missing or unexpected query")
                    result = studio.dashboard(query["project_id"][0], query["run_id"][0])
                elif url.path == "/v1/health":
                    result = {"status": "dev_only", "production_enabled": False,
                              "paid_provider_enabled": False, "publish_enabled": False}
                else:
                    self._send(404, {"error": "UNKNOWN_ROUTE"})
                    return
                self._send(200, result)
            except (Rejected, ValueError, KeyError, TypeError) as exc:
                self._send(400, {"error": type(exc).__name__, "detail": str(exc)[:160]})

    return Handler


def main():
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--database", type=Path, required=True)
    p.add_argument("--bind", default="127.0.0.1")
    p.add_argument("--port", type=int, default=18731)
    args = p.parse_args()
    bearer = os.environ.get("P03_DEV_TOKEN", "")
    if not (1 <= args.port <= 65535):
        raise SystemExit("Invalid port")
    if args.bind != "127.0.0.1" and os.getenv("P03_ALLOW_PRIVATE_BIND") != "1":
        raise SystemExit("Non-loopback dev bind requires explicit opt-in")
    handler = service(args.database, bearer,
                      live_model=os.getenv("P03_LIVE_LOCAL_OLLAMA") == "1",
                      demo_enabled=os.getenv("P03_ALLOW_ONE_SHOT_DEMO") == "1")
    ThreadingHTTPServer((args.bind, args.port), handler).serve_forever()


if __name__ == "__main__":
    main()
