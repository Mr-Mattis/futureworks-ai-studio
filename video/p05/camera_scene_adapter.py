"""Future Works P05 — deterministic cinematography scene-plan adapter.

Bridges the immutable 90-term catalog into existing three-scene P05 intents.
Safe by default: creates plans, NEVER invokes any provider, uploads media,
changes approvals, or activates n8n. Adapted prompts express desired camera
behavior; they are not a guarantee of literal Runway camera controls.
"""
from __future__ import annotations
from pathlib import Path
import json
from camera_direction_contract import load_catalog,compile_camera_direction,CameraSpecRejected
from engine import STAGES,make_scene_requests

HERE=Path(__file__).resolve().parent
CATALOG=HERE/"catalog/Future_Works_Camera_Direction_Catalog_v1.json"

CAMERA_BY_SCENE={
  "S01":{"movement":"MOV-009","angle":"ANG-010","framing":"FRM-003","optics":"OPT-002",
         "subject":"fictional cooperative orbital construction robot beside a human-scale maintenance platform"},
  "S02":{"movement":"MOV-004","angle":"ANG-008","framing":"FRM-008","optics":"OPT-006",
         "subject":"machined robotic actuator with visible fasteners, weathered metal and correctly connected internal components"},
  "S03":{"movement":"MOV-011","angle":"ANG-010","framing":"FRM-003","optics":"OPT-002",
         "subject":"AI-designed civilian autonomous exploration machine moving through an advanced sustainable city"},
}

def planned_camera_scene_intents(bundle, *,catalog_path=CATALOG):
    catalog=load_catalog(catalog_path)
    original=make_scene_requests(bundle)
    if tuple(item["scene_id"] for item in original)!=STAGES:
        raise CameraSpecRejected("P05 three-scene reference order is no longer canonical")
    if set(CAMERA_BY_SCENE)!=set(STAGES):
        raise CameraSpecRejected("Missing scene camera profiles")
    outputs=[]
    for item in original:
        scene=item["scene_id"]
        spec=CAMERA_BY_SCENE[scene]
        direction=compile_camera_direction(catalog,scene_id=scene,duration_seconds=item["duration"],**spec)
        copied=dict(item)
        copied["cinematography"]=direction
        copied["camera_catalog_version"]="1.0"
        copied["promptText"]=item["promptText"]+" "+direction["instruction"]
        if len(copied["promptText"])>10000:
            raise CameraSpecRejected("Camera-enhanced scene prompt exceeds provider limit")
        copied["provider_submit"]=False
        copied["external_asset_upload"]=False
        copied["publish_authorized"]=False
        copied["requires_human_review"]=True
        outputs.append(copied)
    return outputs

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle")
    args=ap.parse_args()
    results=planned_camera_scene_intents(Path(args.bundle))
    print(json.dumps([{"scene_id":x["scene_id"],"camera_codes":x["cinematography"]["camera_codes"],
                       "camera_prompt":x["cinematography"]["instruction"],
                       "reference_sha256":x["reference_sha256"],"provider_submit":False}
                      for x in results],indent=2))
