"""P05 three-scene *real-reference* Runway request planning, NO PAID CALLS.

Consumes the actual 10-image ComfyUI Visual Director handoff, rehashes
source PNGs, forms three executable-schema Runway requests, and persists
immutable work intents. Image uploads, paid task creation, publication and
human approval are deliberately unavailable.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

from engine import Rejected, RunwayWire, VideoStore, make_scene_requests


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reference-bundle",required=True)
    ap.add_argument("--run-id",required=True)
    ap.add_argument("--database",required=True)
    ap.add_argument("--output-directory",required=True)
    ap.add_argument("--dry-run-only",action="store_true",required=True)
    args=ap.parse_args()
    if not args.dry_run_only:
        raise SystemExit("No provider calls are enabled in this development CLI")
    requests=make_scene_requests(args.reference_bundle)
    requests[0]["mode"]="text_to_video"
    api_payloads=[]
    for req in requests:
        if req["mode"]=="text_to_video":
            prepared=RunwayWire.prepare(req)
        else:
            # We verify required image refs, but do not invent a Runway upload
            # URI. Only generate a safe unsubmitted placeholder in the report.
            prepared={"endpoint":"/v1/image_to_video",
                      "version":RunwayWire.prepare(dict(req,mode="text_to_video"))["version"],
                      "requires_real_uploaded_image_uri":True,
                      "source_image_sha256":req["reference_sha256"]}
        api_payloads.append(prepared)
    store=VideoStore(args.database,args.output_directory)
    state=store.plan(args.run_id,requests)
    report={
        "status":"three_real_P04_reference_scene_intents_stored",
        "mode":"NO_PROVIDER_REQUESTS_DRY_RUN_ONLY",
        "run_id":args.run_id,
        "scenes":[{"scene_id":x["scene_id"],"reference_sha256":x["reference_sha256"],
                   "reference_asset_id":x["reference_asset_id"],
                   "provider_mode":x["mode"],"model":x["model"],
                   "duration":x["duration"],"adapter":api_payloads[i],
                   "actual_provider_submitted":False}
                  for i,x in enumerate(requests)],
        "job_count":state["clip_count"],
        "actual_paid_generation_calls":0,
        "actual_runway_clips":0,
        "approval_state":"blocked",
        "actual_spend_usd":0,
        "authorization":state["authorization"],
        "P05_locked_exit":"OPEN",
    }
    print(json.dumps(report,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
