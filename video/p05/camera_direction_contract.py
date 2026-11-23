"""Deterministic Future Works camera-direction vocabulary.

Consumes the official 90-term camera JSON catalog without guessing any
camera codes. Produces structured shot specifications for Visual Director,
Cinematographer and P05 video agents. All output is a PLAN (not a call).
"""
from __future__ import annotations
from dataclasses import dataclass
import json,re
from pathlib import Path

CATEGORY_PREFIX={
    "movement":("MOV","Camera movements",30),
    "angle":("ANG","Camera angles and orientation",20),
    "framing":("FRM","Shot sizes and composition",22),
    "optics":("OPT","Lens, focus and temporal controls",18),
}
class CameraSpecRejected(ValueError):pass

def load_catalog(source):
    data=json.loads(Path(source).read_text(encoding="utf-8"))
    if data.get("version")!="1.0" or data.get("brand")!="Future Works AI Studio":
        raise CameraSpecRejected("Unrecognized camera vocabulary/version")
    items=data.get("catalog")
    if not isinstance(items,list) or len(items)!=90:
        raise CameraSpecRejected("Catalog must contain exactly 90 versioned terms")
    index={}
    for item in items:
        if not isinstance(item,dict) or not all(isinstance(item.get(k),str) and item[k].strip()
                   for k in ("id","category","name","definition","agent_instruction_example","usage")):
            raise CameraSpecRejected("Incomplete camera terminology")
        code=item["id"]
        if code in index or not re.fullmatch(r"(MOV|ANG|FRM|OPT)-\d{3}",code):
            raise CameraSpecRejected("Duplicate or malformed camera ID")
        index[code]=item
    for kind,(prefix,category,count) in CATEGORY_PREFIX.items():
        expected={f"{prefix}-{i:03d}" for i in range(1,count+1)}
        actual={k for k,v in index.items() if v["category"]==category}
        if actual!=expected:raise CameraSpecRejected("Missing, extra or wrong category term: "+kind)
    return index

def compile_camera_direction(catalog,*,movement,angle,framing,optics,
                             duration_seconds,subject,scene_id):
    if not isinstance(scene_id,str) or not re.fullmatch(r"S\d{2}",scene_id):
        raise CameraSpecRejected("Invalid scene id")
    if not isinstance(subject,str) or not 3<=len(subject.strip())<=300:
        raise CameraSpecRejected("Concrete subject description required")
    if not isinstance(duration_seconds,(int,float)) or isinstance(duration_seconds,bool) or not 1<=duration_seconds<=30:
        raise CameraSpecRejected("Duration must be 1–30 seconds")
    selections={"movement":movement,"angle":angle,"framing":framing,"optics":optics}
    definitions={}
    for kind,code in selections.items():
        prefix,category,_=CATEGORY_PREFIX[kind]
        if not isinstance(code,str) or not code.startswith(prefix+"-") or code not in catalog:
            raise CameraSpecRejected("Unknown "+kind+" ID; never invent camera codes")
        item=catalog[code]
        if item["category"]!=category:raise CameraSpecRejected("Wrong camera category")
        definitions[kind]={"id":code,"name":item["name"],"definition":item["definition"],
                           "guide":item["agent_instruction_example"]}
    # Preserve source definitions; examples are explanatory only, not blindly
    # appended because example durations and directions can conflict with this shot.
    prompt=("CINEMATOGRAPHY CONTRACT — scene "+scene_id+". "+
            "Subject: "+subject.strip()+". "+
            "Duration: "+str(duration_seconds)+" seconds. "+
            "Camera movement: "+definitions["movement"]["name"]+" — "+definitions["movement"]["definition"]+". "+
            "Viewing angle: "+definitions["angle"]["name"]+" — "+definitions["angle"]["definition"]+". "+
            "Shot composition: "+definitions["framing"]["name"]+" — "+definitions["framing"]["definition"]+". "+
            "Optical treatment: "+definitions["optics"]["name"]+" — "+definitions["optics"]["definition"]+". "+
            "Prioritize stable geometry, plausible parallax, clear scale cues, consistent material texture; do not morph the subject.")
    return {"schema":"FWAI_CAMERA_DIRECTION_1","scene_id":scene_id,
            "duration_seconds":duration_seconds,"subject":subject.strip(),
            "camera":definitions,"instruction":prompt,
            "camera_codes":selections,"provider_calls_authorized":False}

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("catalog")
    a=p.parse_args()
    index=load_catalog(a.catalog)
    sample=compile_camera_direction(index,movement="MOV-009",angle="ANG-010",
        framing="FRM-003",optics="OPT-002",duration_seconds=5,scene_id="S01",
        subject="autonomous nonmilitary orbital construction robot beside a human-scale maintenance platform")
    print(json.dumps(sample,indent=2))
