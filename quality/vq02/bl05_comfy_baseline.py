"""BL01 + P04: bounded local Blender pose guide -> ComfyUI inpaint -> pixel-locked QC.
One-shot local GPU proof. No paid APIs, no activation, no publishing, no destructive writes.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import hashlib, json, os, time, urllib.request, urllib.parse, uuid, sys
HOME=Path.home()
BASE=HOME/"Documents"/"futureworks-maintenance"
POC=BASE/"poc-bl05-gpu-baseline"
SHOT=HOME/"Documents"/"futureworks-p04-data"/"FWAI-M001_EP001_PREPRODUCTION"/"05_LOCAL_KEYFRAMES"/"S01"
SOURCE=SHOT/"candidate_D4_env_crop"/"FWAI_EP001_S01_LOCAL_REFERENCE_CANDIDATE_1024x576.png"
COMFY=HOME/"Documents"/"futureworks-p04-comfyui"
INPUT=COMFY/"input"
API="http://127.0.0.1:8188"
REC=POC/"BL01_P04_GPU_RECEIPT.json"
TARGET="BL05_P04_composite.png"
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def save(o):
    q=REC.with_suffix(".pending")
    q.write_text(json.dumps(o,indent=2))
    q.replace(REC)
def api(path,data=None,binary=False):
    raw=json.dumps(data).encode() if data is not None else None
    req=urllib.request.Request(API+path,data=raw,headers={"Content-Type":"application/json"} if raw else {},method="POST" if raw else "GET")
    with urllib.request.urlopen(req,timeout=90) as res:
        return res.read() if binary else json.load(res)
def prepare():
    with Image.open(SOURCE) as source, Image.open(POC/"BL01_mech_pose_overlay.png") as guide:
        assert source.size==guide.size==(1024,576)
        base=source.convert("RGBA")
        overlay=guide.convert("RGBA")
        # Blender guide is a structure proposal, not approved mech material appearance.
        overlay.putalpha(overlay.getchannel("A").point(lambda a:int(a*0.55)))
        blended=Image.alpha_composite(base,overlay).convert("RGB")
        blended.save(POC/"BL01_guided_input.png")
        mask=Image.new("L",(1024,576),0)
        painter=ImageDraw.Draw(mask)
        # Restricted to mech leg/foot region; protects door, vinyl, car, workshop.
        painter.polygon([(106,275),(245,273),(326,367),(342,535),(93,543)],fill=255)
        painter.polygon([(130,305),(102,410),(101,535),(245,538),(238,460),(221,345)],fill=255)
        mask=mask.filter(ImageFilter.GaussianBlur(4))
        mask.save(POC/"BL01_edit_mask.png")
    for name,src in (("FWAI_BL05_GUIDED_INPUT.png",POC/"BL01_guided_input.png"),
                     ("FWAI_BL05_EDIT_MASK.png",POC/"BL01_edit_mask.png")):
        dst=INPUT/name
        if dst.exists() and sha(dst)!=sha(src):
            raise RuntimeError("Input name collision; refusing overwrite: "+str(dst))
        if not dst.exists():dst.write_bytes(src.read_bytes())
    return sha(SOURCE),sha(POC/"BL01_guided_input.png"),sha(POC/"BL01_edit_mask.png")
def graph():
    prompt=("Photorealistic studio automotive workshop scene. Preserve white sports car, overhead-lit workshop, "
        "purple articulated industrial mech working beside passenger side, correct bent mechanical knees, "
        "jointed ankles, weight-bearing planted feet, realistically tensioned matte charcoal vinyl on vehicle door, "
        "consistent materials, perspective, lighting and proportions.")
    negative="blur, unfinished painting, flat gray blobs, broken legs, disconnected joints, extra appendages, cartoon, text"
    return {
      "1":{"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":"v1-5-pruned-emaonly.safetensors"}},
      "4":{"class_type":"CLIPTextEncode","inputs":{"text":prompt,"clip":["1",1]}},
      "5":{"class_type":"CLIPTextEncode","inputs":{"text":negative,"clip":["1",1]}},
      "6":{"class_type":"LoadImage","inputs":{"image":"FWAI_BL05_GUIDED_INPUT.png"}},
      "8":{"class_type":"VAEEncode","inputs":{"pixels":["6",0],"vae":["1",2]}},
      "13":{"class_type":"KSampler","inputs":{"model":["1",0],"positive":["4",0],"negative":["5",0],"latent_image":["8",0],
             "seed":2388112215,"steps":12,"cfg":6,"sampler_name":"euler","scheduler":"normal","denoise":0.22}},
      "14":{"class_type":"VAEDecode","inputs":{"samples":["13",0],"vae":["1",2]}},
      "15":{"class_type":"SaveImage","inputs":{"images":["14",0],"filename_prefix":"FWAI_BL05_SD15_GUIDED_LEGS"}}}
def compose(rec):
    raw=POC/"BL01_comfy_raw.png"
    with Image.open(raw) as changed,Image.open(SOURCE) as source,Image.open(POC/"BL01_edit_mask.png") as mask:
        if changed.size!=source.size: raise RuntimeError("GPU output dimensions unexpected")
        output=Image.composite(changed.convert("RGB"),source.convert("RGB"),mask.convert("L"))
        out=POC/TARGET
        output.save(out)
        # Strict invariance of every pixel OUTSIDE the mask, not unverifiable prompts.
        maskpix=mask.convert("L")
        orig=source.convert("RGB")
        diff=ImageChops.difference(orig,output)
        outside=ImageChops.multiply(diff,Image.merge("RGB",tuple(ImageChops.invert(maskpix) for _ in range(3))))
        # Blended feathered mask differs only where mask >0. Use exact zero mask guard.
        a=orig.load();b=output.load();m=maskpix.load()
        count=0
        for y in range(576):
            for x in range(1024):
                if m[x,y]==0 and a[x,y]!=b[x,y]:count+=1
        assert count==0,f"OUTSIDE_MASK_PIXELS_CHANGED:{count}"
        contact=Image.new("RGB",(1024*3,576),(18,22,27))
        contact.paste(orig,(0,0))
        with Image.open(POC/"BL01_guided_input.png") as guided:contact.paste(guided.convert("RGB"),(1024,0))
        contact.paste(output,(2048,0))
        contact.save(POC/"BL01_P04_review_triptych.png")
    rec.update(status="complete",output_file=TARGET,output_sha256=sha(POC/TARGET),
      outside_mask_modified_pixels=count,visual_approval=False,runway_calls=0,paid_calls=0,
      review_triptych="BL01_P04_review_triptych.png")
    save(rec)
    print("BL01_P04_INTEGRATION_PASS",out,"outside_mask_pixels_modified",count,flush=True)
def main():
    if not (POC/"BL01_pose_manifest.json").exists():raise RuntimeError("Blender pose guide missing")
    if not SOURCE.is_file():raise RuntimeError("Original source missing")
    src,guide,mask=prepare()
    if REC.exists():
        r=json.loads(REC.read_text())
        if r.get("source_sha256")!=src or r.get("guide_sha256")!=guide or r.get("mask_sha256")!=mask:
            raise RuntimeError("Previously submitted inputs changed; refuse")
        if r["status"]=="complete":
            assert (POC/TARGET).exists() and sha(POC/TARGET)==r["output_sha256"]
            print("BL01_P04_ALREADY_VERIFIED",POC/TARGET);return
        if r["status"]!="submitted":
            raise RuntimeError("Non-repeatable job in state "+r["status"])
    else:
        r={"schema":"FWAI_BL05_SD15_GPU_FALLBACK_V1","status":"planned","source_sha256":src,
           "guide_sha256":guide,"mask_sha256":mask,"blender_pose_sha256":sha(POC/"BL01_mech_pose_overlay.png"),
           "visual_approval":False,"paid_calls":0,"runway_calls":0}
        save(r)
    if r["status"]=="planned":
        stats=api("/system_stats")
        if not any("RX 9070 XT" in d.get("name","") for d in stats["devices"]):
            raise RuntimeError("Radeon GPU unavailable")
        q=api("/queue")
        if q.get("queue_running") or q.get("queue_pending"):raise RuntimeError("GPU queue busy; not submitting")
        r["status"]="submitting";save(r)
        try:response=api("/prompt",{"prompt":graph(),"client_id":"FWAI_BL01_P04_USER_AUTHORIZED_LOCAL_POC"})
        except Exception as exc:
            r.update(status="ambiguous",error=str(exc)[:250]);save(r);raise
        if response.get("node_errors"):
            r.update(status="rejected",node_errors=response["node_errors"]);save(r)
            raise RuntimeError("Comfy node validation rejected")
        uuid.UUID(response["prompt_id"])
        r.update(status="submitted",prompt_id=response["prompt_id"]);save(r)
        print("BL01_P04_SUBMITTED",r["prompt_id"],flush=True)
    for _ in range(240):
        h=api("/history/"+r["prompt_id"]).get(r["prompt_id"])
        if h:
            if h.get("status",{}).get("status_str")=="error":
                r.update(status="failed",error=str(h.get("status",{}).get("messages",[]))[-1000:]);save(r)
                raise RuntimeError("GPU task reported error")
            im=h.get("outputs",{}).get("15",{}).get("images",[])
            if len(im)==1:
                a=im[0]
                query=urllib.parse.urlencode({"filename":a["filename"],"subfolder":a.get("subfolder",""),"type":a.get("type","output")})
                (POC/"BL01_comfy_raw.png").write_bytes(api("/view?"+query,binary=True))
                compose(r)
                return
        time.sleep(3)
    raise TimeoutError("Task still running; receipt persisted; don't re-submit blindly")
if __name__=="__main__":main()
