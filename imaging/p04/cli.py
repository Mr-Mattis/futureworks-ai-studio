"""P04 local ComfyUI CLI (Windows ROCm or isolated Linux AMD backend).

All outputs stay in a non-production directory; no API keys/paid clients.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import time
from engine import Comfy, ImagePipeline, MANIFEST, Rejected, verify_model


def run(args):
    client = Comfy(args.comfy_url)
    health = client.health()
    names = [str(d.get("name", "")) for d in health.get("devices", [])]
    if not any("AMD" in name or "Radeon" in name for name in names):
        raise Rejected("Real AMD GPU acceleration could not be verified")
    if args.probe_only:
        print(json.dumps({"status": "GPU_REPORTED", "devices": names}, indent=2))
        return 0
    digest = verify_model(Path(args.model_file))
    pipeline = ImagePipeline(args.database, args.output, client)
    ids = pipeline.prepare(MANIFEST, run_id=args.run_id, model_sha=digest)
    for image_id in ids:
        prior = next(r for r in pipeline.dashboard(args.run_id)["images"]
                     if r["image_id"] == image_id)
        if prior["state"] == "complete":
            print(image_id + " already verified", flush=True)
            continue
        if prior["state"] in ("submitting", "needs_review"):
            raise Rejected(image_id + " may have unknown provider-side receipt: human reconciliation required")
        if prior["state"] == "queued":
            prompt_id = pipeline.submit_one(image_id)
            print(image_id + " queued " + str(prompt_id), flush=True)
        deadline = time.monotonic() + args.timeout
        while time.monotonic() < deadline:
            result = pipeline.poll_one(image_id)
            if result == "complete":
                print(image_id + " downloaded and indexed", flush=True)
                break
            time.sleep(args.poll_interval)
        else:
            raise Rejected(image_id + " timed out; existing Comfy prompt must be inspected before retry")
    handoff = pipeline.visual_handoff(args.run_id)
    print(json.dumps({"status": "READY_FOR_VISUAL_DIRECTOR_REVIEW",
                      "image_count": len(handoff["assets"]),
                      "handoff_file": str(Path(args.output).resolve() /
                                          ("VISUAL_DIRECTOR_HANDOFF_" + args.run_id + ".json")),
                      "authorization": handoff["authorization"],
                      "paid_provider_calls": 0}, indent=2))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--comfy-url", default="http://127.0.0.1:8188")
    ap.add_argument("--model-file", required=False)
    ap.add_argument("--database", required=False)
    ap.add_argument("--output", required=False)
    ap.add_argument("--run-id", default="P04_SAMPLE_001")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--poll-interval", type=float, default=3.0)
    ap.add_argument("--probe-only", action="store_true")
    args = ap.parse_args()
    if args.timeout < 10 or args.timeout > 3600 or args.poll_interval < .1:
        ap.error("Controlled time bounds required")
    if not args.probe_only and not all([args.model_file, args.database, args.output]):
        ap.error("model-file, database and output are required for generation")
    try:
        return run(args)
    except (Rejected, OSError, ValueError) as exc:
        print(json.dumps({"status": "REJECTED", "reason": str(exc)[:300]}),
              file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
