"""P04.06 automatic metadata-to-Visual-Director planning handoff.

Reads actual ten SHA-verified local ComfyUI PNG files; sends only safe
asset metadata (not pixels) to local Ollama for Visual Director shot
planning. Does NOT claim visual inspection, approve images or make media.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request

REPO=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO/"agents/p02_roles"))
import role_validation as roles
from engine import MANIFEST, Rejected, compact, png_dimensions, sha

ALLOWED_OLLAMA=("http://127.0.0.1:11434/api/chat",
                "http://localhost:11434/api/chat",
                "http://host.docker.internal:11434/api/chat")


def inspect_handoff(path):
    path=Path(path).resolve()
    payload=json.loads(path.read_text())
    if set(payload) != {"schema_version","project_id","run_id","status",
                        "assets","assets_count","authorization",
                        "dispatch_performed","paid_provider_calls"}:
        raise Rejected("Visual handoff has unknown/missing fields")
    if (payload["project_id"]!="FWAI-EP-0001" or payload["assets_count"]!=10
            or len(payload["assets"])!=10 or
            payload["status"]!="ready_for_visual_director"
            or payload["paid_provider_calls"]!=0 or payload["dispatch_performed"]
            or any(payload["authorization"].values())):
        raise Rejected("Visual handoff is not an authorized development reference set")
    images=[]
    for item in payload["assets"]:
        p=Path(item["local_path"]).resolve()
        if not p.is_relative_to(path.parent) or not p.is_file() or p.suffix.lower()!=".png":
            raise Rejected("Visual reference escaped or is missing")
        raw=p.read_bytes()
        png_dimensions(raw)
        if sha(raw)!=item["sha256"] or item["project_id"]!=payload["project_id"]:
            raise Rejected("Visual reference hash or project mismatch")
        if item["approval_state"]!="requires_visual_director_review":
            raise Rejected("Image approval was fabricated")
        if item["model_sha256"]!=
                "6ce0161689b3853acaa03779ec93eafe75a02f4ced659bee03f50797806fa2fa":
            raise Rejected("Model provenance changed")
        images.append({k:item[k] for k in (
            "asset_id","scene_id","sha256","seed","template",
            "reference_id","model_id","model_sha256")})
    if len({x["asset_id"] for x in images})!=10:
        raise Rejected("Duplicate image IDs")
    if {x["scene_id"] for x in images}!={"S01","S02","S03","S04","S05"}:
        raise Rejected("Incomplete scene coverage")
    return payload, images


def send_to_visual(handoff, *, ollama_url="http://127.0.0.1:11434/api/chat",
                   target=None, timeout=300):
    if ollama_url not in ALLOWED_OLLAMA:
        raise Rejected("Only localhost Ollama inference allowed")
    payload,images=inspect_handoff(handoff)
    manifest=json.loads(MANIFEST.read_text())
    ref={k:manifest[k] for k in ("schema_version","project_id","revision")}
    ref["sha256"]=hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    ctx={
        "scope":"episode","project_id":payload["project_id"],
        "input_manifest":ref,"run_id":payload["run_id"],
        "attempt":1,
        "role_input":{
            "project_id":payload["project_id"],
            "scene_ids":[s["scene_id"] for s in manifest["scenes"]],
            "visual_references":images,
            "script":"Fictional AI-concept graphite/cyan computer transformation. "
                     "Images are local AI-generated references, not verified engineering.",
            "scenes":[{"scene_id":s["scene_id"],
                       "duration_seconds":s["duration_seconds"]} for s in manifest["scenes"]],
            "budget_constraints":{"paid_generation_authorized":False},
        },
    }
    schema=roles.schema("visual_director")
    system=(roles.registry()["visual_director"]["output_instructions"]+
        "\nP04.06 controlled local metadata-only Visual Director intake. You have "
        "NOT seen the pixels and must NOT claim to have viewed or quality-approved "
        "the generated images. Output only valid JSON matching the output_schema. "
        "Plan at least ten shots: one for each distinct reference asset_id, each "
        "with exact scene_id and reference_asset_id. "
        "Keep provenance explicit, do not invent new images/engineering tests, "
        "do not authorize spending/publishing/identity use. "
        "Unresolved assets must include actual visual inspection/rights checks.")
    request={
        "model":"qwen3.6:latest", "stream":False, "think":False, "format":schema,
        "options":{"temperature":0,"num_predict":4000,"num_ctx":16384},
        "messages":[
            {"role":"system","content":system},
            {"role":"user","content":json.dumps(
                {"role_input":ctx["role_input"],"output_schema":schema})}
        ],
    }
    call=urllib.request.Request(ollama_url,data=compact(request).encode(),
                                headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(call,timeout=timeout) as result:
            raw=result.read(4*1024*1024)
        candidate=json.loads(json.loads(raw)["message"]["content"])
    except (urllib.error.URLError,TimeoutError,KeyError,ValueError) as exc:
        raise Rejected("Visual Director local inference unavailable or malformed") from exc
    checked=roles.checked_output("visual_director",candidate,ctx)
    references={x["asset_id"]:x["scene_id"] for x in images}
    shots=checked.get("shots",[])
    if len(shots)<10 or {s.get("reference_asset_id") for s in shots} != set(references):
        raise Rejected("Visual Director did not consume all ten image references")
    if any(s.get("scene_id") != references.get(s.get("reference_asset_id")) for s in shots):
        raise Rejected("Visual Director changed image-to-scene lineage")
    result=roles.envelope("visual_director",checked,ctx,manifest_path=MANIFEST)
    result["p04_reference_assets"]=images
    result["p04_visual_media_status"]="metadata_only; pixel/rights review pending"
    if target is not None:
        dest=Path(target).resolve()
        if not dest.is_relative_to(Path(handoff).resolve().parent):
            raise Rejected("Visual Director result must stay in local development output")
        dest.write_text(json.dumps(result,indent=2))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--handoff",required=True)
    parser.add_argument("--output",required=True)
    parser.add_argument("--ollama-url",default="http://127.0.0.1:11434/api/chat")
    args=parser.parse_args()
    try:
        result=send_to_visual(args.handoff,target=args.output,ollama_url=args.ollama_url)
        print(json.dumps({"status":"BLOCKED_VISUAL_DIRECTOR_PLAN_RECEIVED",
                          "assets":len(result["p04_reference_assets"]),
                          "shots":len(result["output"]["shots"]),
                          "authorization":result["authorization"]}))
        return 0
    except (Rejected,ValueError,OSError) as exc:
        print(json.dumps({"status":"REJECTED","reason":str(exc)[:200]}),file=sys.stderr)
        return 1


if __name__=="__main__":
    raise SystemExit(main())
