"""Upgrade one already-generated P04 Visual Director file to an outer provenance bundle.

No model inference, new images, service calls or publication. Revalidates the
unchanged canonical P01.02 envelope and ten SHA-verified local PNG references
before a controlled atomic local-file rewrite.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
import uuid

from engine import MANIFEST, Rejected
from visual_bridge import REPO, inspect_handoff


def repack(handoff, plan_path):
    handoff=Path(handoff).resolve()
    plan_path=Path(plan_path).resolve()
    if plan_path.parent!=handoff.parent or plan_path.suffix!=".json":
        raise Rejected("Only isolated P04 metadata alongside image assets can be migrated")
    reference,imgs=inspect_handoff(handoff)
    source=json.loads(plan_path.read_text())
    if set(source)=={"checkpoint","agent_result","p04_reference_assets","p04_visual_media_status"}:
        return source
    expected=set(("schema_version","result_id","agent","scope","input_manifest",
                  "execution","output","validation","errors","blockers","authorization",
                  "p04_reference_assets","p04_visual_media_status"))
    if set(source)!=expected:
        raise Rejected("Refusing unexpected original Visual Director artifact")
    images=source.pop("p04_reference_assets")
    claim=source.pop("p04_visual_media_status")
    if (claim!="metadata_only; pixel/rights review pending" or
            len(images)!=10 or
            {i["asset_id"] for i in images}!={i["asset_id"] for i in imgs}):
        raise Rejected("Reference set or review status differs from actual images")
    shots=source["output"].get("shots",[])
    if ({s.get("reference_asset_id") for s in shots} !=
            {i["asset_id"] for i in imgs} or
            len(shots)!=10 or
            source["agent"]["role"]!="visual_director" or
            source["execution"]["status"]!="blocked" or
            any(source["authorization"].values())):
        raise Rejected("Canonical agent result did not preserve ten blocked references")
    spec=importlib.util.spec_from_file_location(
        "p04_bundle_p01_validator",
        REPO/"contracts/agent-result/v1.0.0/validate_agent_result.py")
    checker=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    errors=checker.validate(source,MANIFEST,REPO/"contracts/production-manifest/v1.0.0")
    if errors:
        raise Rejected("Locked P01 canonical contract mismatch: "+"; ".join(errors))
    bundle={
        "checkpoint":"P04.06",
        "agent_result":source,
        "p04_reference_assets":imgs,
        "p04_visual_media_status":claim,
    }
    stage=plan_path.with_name(plan_path.name+"."+uuid.uuid4().hex+".tmp")
    try:
        stage.write_text(json.dumps(bundle,indent=2))
        stage.replace(plan_path)
    finally:
        stage.unlink(missing_ok=True)
    return bundle


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--handoff",required=True)
    p.add_argument("--plan",required=True)
    args=p.parse_args()
    out=repack(args.handoff,args.plan)
    print(json.dumps({"status":"CANONICAL_P01_ROLE_ENVELOPE_VERIFIED",
                      "assets":len(out["p04_reference_assets"]),
                      "shots":len(out["agent_result"]["output"]["shots"]),
                      "authorization":out["agent_result"]["authorization"]}))
