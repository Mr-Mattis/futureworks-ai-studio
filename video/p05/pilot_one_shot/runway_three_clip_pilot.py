#!/usr/bin/env python3
"""Future Works one-time user-authorized Runway 3-clip pilot.

Run in WSL, NOT the production n8n service.
Source and scope pinned below. Default mode is read-only PREPARE.
--submit charges up to exactly 180 credits for three 5-second Gen-4.5 clips,
no automatic POST retries. --poll only checks already submitted receipts.
"""
from __future__ import annotations
import argparse,base64,datetime,hashlib,json,os,pathlib,subprocess,sys,time,urllib.request,urllib.error,uuid
ROOT=pathlib.Path("/mnt/c/Users/yashi/Documents/futureworks-p04-data/images")
OUT=pathlib.Path("/mnt/c/Users/yashi/Documents/futureworks-p05-data/real-runway-pilot-001")
BUNDLE=ROOT/"VISUAL_DIRECTOR_HANDOFF_P04_GPU_001.json"
MANIFEST=pathlib.Path.home()/"futureworks-studio/futureworks-p04-quality-v3/contracts/production-manifest/v1.0.0/example.valid.json"
KEY=pathlib.Path.home()/".config/futureworks-ai-studio/secrets/runway_api_key"
BASE="https://api.dev.runwayml.com"
VERSION="2024-11-06"
MODEL="gen4.5"
RATIO="1280:720"
DURATION=5
MAX_TOTAL_CREDITS=500
EXPECTED_TOTAL_CREDITS=3*DURATION*12
# The three distinct originals authorized by the owner for the $5 pilot.
PINNED={
"S01":("P04_P04_GPU_001_01","e889931fdc0f335a298f17bec805b266b84ac24aa774296f9ff08ab2f11d4f53"),
"S02":("P04_P04_GPU_001_03","823332cd603610e128fd36c08af9eca035747632eba6f860b2aee63461e4e958"),
"S03":("P04_P04_GPU_001_05","47f888da609871e13d73d941d63a0790d4d4b027293cbcc259ba4503c8668af7")}
PROMPTS={
"S01":"Photorealistic cinematic macro tracking shot across the fictional graphite titanium computer-machine. Slowly glide to reveal precise machined panels, tiny hex bolts, brushed metal, authentic surface wear, micro-scratches, cyan LED reflections. Preserve the shape and color of the supplied frame; believable manufacturing detail and subtle parallax. No text, no logos, no morphing.",
"S02":"Slow cinematic dolly around the same fictional transforming robot assembly. Clear realistic actuators, bearings, weathered machined metal joints, internal wiring, panel seams and physically plausible mechanisms. Preserve the reference design, keep every mechanical limb stable, delicate environmental dust and cinematic lighting. No text or logos, no invented limbs.",
"S03":"High-end realistic film shot of the fictional robotics chassis in its industrial environment. Controlled forward camera move, detailed interlocking metal panels, exposed servos and internal motor housings, worn metal edges, precise cyan lighting, mild airborne particles. Keep the machine geometry consistent with the original frame. No text, logos, flicker or new objects."}
OWNER_APPROVAL={
"source":"owner conversation authorization 2026-11-16",
"manifest_creative_approved":True,
"rights_confirmed_by_owner":True,
"external_provider":"Runway Developer API",
"external_upload_scope":"exactly the 3 pinned original P04 image SHA256 references S01-S03",
"model":MODEL,"clip_count":3,"duration_seconds_each":5,
"maximum_credits":500,"maximum_dollars_usd":"5.00",
"no_paid_retries":True,"publish_authorized":False,
"production_activation_authorized":False,
}
def sha(b):return hashlib.sha256(b).hexdigest()
def iso():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+".temp")
    with temp.open("x") as f:
        json.dump(obj,f,indent=2,sort_keys=True)
        f.flush();os.fsync(f.fileno())
    temp.replace(path)
def api(method,route,body=None):
    key=KEY.read_text().strip()
    if not key or len(key)<16:raise RuntimeError("Runway key not configured")
    req=urllib.request.Request(BASE+route,
        data=(json.dumps(body,separators=(",",":")).encode() if body is not None else None),
        headers={"Authorization":"Bearer "+key,"X-Runway-Version":VERSION,"Content-Type":"application/json"},
        method=method)
    try:
        with urllib.request.urlopen(req,timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        # API details may contain a prompt fragment. Never print raw body/secret.
        raise RuntimeError("Runway API HTTP "+str(e.code)+" (no automatic retry)") from None
def balance():
    d=api("GET","/v1/organization")
    n=d.get("creditBalance")
    if not isinstance(n,(int,float)) or n<0:raise RuntimeError("Missing valid Runway credit balance")
    return int(n)
def input_assets():
    bundle=json.loads(BUNDLE.read_text())
    if bundle.get("status")!="ready_for_visual_director" or bundle.get("assets_count")!=10:
        raise RuntimeError("Unexpected original bundle")
    data=json.loads(MANIFEST.read_text())
    if data["project_id"]!=bundle["project_id"] or data["approval_state"]["status"]!="pending_review":
        raise RuntimeError("Changed canonical manifest / approval state")
    if data.get("content_type")!="AI_CONCEPT":raise RuntimeError("Unexpected production type")
    selected={}
    for scene,(name,digest) in PINNED.items():
        matches=[a for a in bundle["assets"] if a["scene_id"]==scene and a["asset_id"]==name]
        if len(matches)!=1 or matches[0]["sha256"]!=digest:raise RuntimeError("Bundle mismatch "+scene)
        file=ROOT/(name+".png")
        raw=file.read_bytes()
        if sha(raw)!=digest or not 512<=len(raw)<=5_000_000 or raw[:8]!=b"\x89PNG\r\n\x1a\n":
            raise RuntimeError("Source image not valid for Runway "+scene)
        selected[scene]={"file":str(file),"sha256":digest,"asset_id":name,"bytes":len(raw)}
    return selected
def begin():
    selected=input_assets()
    OUT.mkdir(parents=True,exist_ok=True)
    journal=OUT/"pilot-journal.json"
    evidence={"schema":"FWAI_P05_REAL_PILOT_1",
        "authorization":OWNER_APPROVAL,
        "original_manifest_sha256":sha(MANIFEST.read_bytes()),
        "original_bundle_sha256":sha(BUNDLE.read_bytes()),
        "created_at":iso(),"max_credits":MAX_TOTAL_CREDITS,
        "planned_credits":EXPECTED_TOTAL_CREDITS,
        "selected":selected,"scenes":{s:{"state":"planned"} for s in PINNED},
        "paid_submission_count":0}
    if journal.exists():
        old=json.loads(journal.read_text())
        if old["selected"]!=selected or old["authorization"]!=OWNER_APPROVAL:
            raise RuntimeError("Existing pilot identity conflict")
        return old
    save(journal,evidence)
    return evidence
def submit():
    from correct_approved_manifest import verify
    verify()  # Validate P01 schema + lineage + exact owner scope and source hashes BEFORE spending.
    state=begin()
    if state["paid_submission_count"]!=0 or any(x["state"]!="planned" for x in state["scenes"].values()):
        raise RuntimeError("Already submitted or attempted, use --poll; no resubmission")
    if EXPECTED_TOTAL_CREDITS>MAX_TOTAL_CREDITS:
        raise RuntimeError("Hard budget cap exceeded")
    first=balance()
    if first<EXPECTED_TOTAL_CREDITS:raise RuntimeError("Insufficient prepaid Runway credits")
    state["starting_credit_balance"]=first;save(OUT/"pilot-journal.json",state)
    print("PILOT AUTHENTICATED: 3 clips x 5s Gen-4.5; budget ceiling 500 credits, expected 180; balance",first,flush=True)
    for scene in PINNED:
        row=state["scenes"][scene]
        if row["state"]!="planned":raise RuntimeError("unexpected scene state")
        used=len([x for x in state["scenes"].values() if x["state"]!="planned"])
        if (used+1)*60>MAX_TOTAL_CREDITS:raise RuntimeError("remaining budget insufficient")
        current=balance()
        if current<60 or first-current>MAX_TOTAL_CREDITS-60:raise RuntimeError("budget guard: no further submissions")
        image_bytes=pathlib.Path(state["selected"][scene]["file"]).read_bytes()
        if sha(image_bytes)!=state["selected"][scene]["sha256"]:raise RuntimeError("image changed")
        payload={"model":MODEL,"duration":DURATION,"ratio":RATIO,"promptText":PROMPTS[scene],
                 "promptImage":"data:image/png;base64,"+base64.b64encode(image_bytes).decode()}
        row.update({"state":"submission_attempted","attempted_at":iso(),"balance_pre":current,
                    "request_metadata_sha256":sha(json.dumps({k:v for k,v in payload.items() if k!="promptImage"},sort_keys=True).encode())})
        state["paid_submission_count"]+=1
        save(OUT/"pilot-journal.json",state)
        print(scene,"starting one paid submission; no retry",flush=True)
        # Request can be billed even if the response is lost. Above state is saved BEFORE sending.
        response=api("POST","/v1/image_to_video",payload)
        uid=str(uuid.UUID(response["id"]))
        row.update({"state":"submitted","task_id":uid,"received_at":iso()})
        save(OUT/"pilot-journal.json",state)
        print(scene,"task created",uid,flush=True)
    print("ALL_THREE_SUBMITTED; run --poll for status",flush=True)
def poll():
    state=begin()
    if not state["paid_submission_count"]:
        print("NO_PAID_TASKS_SUBMITTED");return
    for scene,row in state["scenes"].items():
        if row["state"] in ("planned","submission_attempted","archived","failed","cancelled"):continue
        tid=row.get("task_id")
        if not tid:raise RuntimeError("No provider task receipt "+scene)
        resp=api("GET","/v1/tasks/"+tid)
        if resp.get("id")!=tid:raise RuntimeError("Runway task identity mismatch")
        status=resp.get("status")
        if status not in ("PENDING","THROTTLED","RUNNING","SUCCEEDED","FAILED","CANCELLED"):
            raise RuntimeError("Unknown task state")
        if status=="SUCCEEDED":
            outputs=resp.get("output")
            if not isinstance(outputs,list) or len(outputs)!=1 or not outputs[0].startswith("https://"):
                raise RuntimeError("Success with invalid output media URI")
            # Store signed output URI only in chmod-600 local journal for later secure archive.
            row.update({"state":"ready_to_archive","status":status,"output_url":outputs[0]})
        elif status in ("FAILED","CANCELLED"):
            row.update({"state":status.lower(),"status":status})
        else:row.update({"state":"submitted","status":status})
        row["last_polled"]=iso()
        save(OUT/"pilot-journal.json",state)
        print(scene,status,flush=True)
    print("BALANCE_AFTER",balance(),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("command",choices=["prepare","submit","poll"])
    args=p.parse_args()
    if args.command=="prepare":
        d=begin()
        print("PREPARED pinned originals:",", ".join(d["selected"]))
        print("3 clips at 12 credits/s x 5 seconds = 180 planned credits ($1.80), hard cap 500 credits ($5)")
        print("Manifest approved by owner in conversation, but independent immutable signed P04/n8n gate is NOT yet complete")
        print("LOCAL_UNSENT_ONLY; no media transfer or paid operations")
    elif args.command=="submit":submit()
    else:poll()
