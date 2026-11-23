"""VQ03.05 — locally enhance an isolated mech-region preview, preserve the car pixels.
ComfyUI SD1.5 fallback with provenance, no external calls, no automatic retries.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter,ImageChops
import json,hashlib,time,urllib.request,urllib.parse,uuid
HOME=Path.home();ROOT=HOME/"Documents"/"futureworks-vq03"
OUT=ROOT/"proof-v5"
COMFY=HOME/"Documents"/"futureworks-p04-comfyui"
API="http://127.0.0.1:8188"
receipt=OUT/"VQ03_COMFY_RECEIPT.json"
source=OUT/"VQ03_B_CROUCH.png"
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def req(path,data=None,raw=False):
    blob=json.dumps(data).encode() if data is not None else None
    r=urllib.request.Request(API+path,data=blob,headers={"Content-Type":"application/json"} if blob else {},method="POST" if blob else "GET")
    with urllib.request.urlopen(r,timeout=90) as ans:return ans.read() if raw else json.load(ans)
def prepare():
    with Image.open(source) as im:
        assert im.size==(1280,720)
        small=im.convert("RGB").resize((1024,576),Image.Resampling.LANCZOS)
        small.save(OUT/"VQ03_COMFY_INPUT.png")
    mask=Image.new("L",(1024,576),0);draw=ImageDraw.Draw(mask)
    # Restrict all AI changes to mech silhouette only; car, film and workshop remain original.
    draw.rounded_rectangle((74,120,296,475),radius=15,fill=255)
    mask=mask.filter(ImageFilter.GaussianBlur(4))
    mask.save(OUT/"VQ03_COMFY_MASK.png")
    for name,path in (("FWAI_VQ03_V5_B_INPUT.png",OUT/"VQ03_COMFY_INPUT.png"),("FWAI_VQ03_V5_B_MASK.png",OUT/"VQ03_COMFY_MASK.png")):
        dest=COMFY/"input"/name
        if dest.exists() and sha(dest)!=sha(path):raise RuntimeError("Input collision "+name)
        if not dest.exists():dest.write_bytes(path.read_bytes())
    return sha(source),sha(OUT/"VQ03_COMFY_INPUT.png"),sha(OUT/"VQ03_COMFY_MASK.png")
def graph():
    prompt=("One tall industrial mech working beside a pearl white performance coupe. "
            "Purple obsidian-plum precise machined armor, cyan visor, titanium mechanical joints, "
            "photographic surface texture, preserve robot articulated limb silhouette exactly, "
            "feet planted, no new legs or objects. Automotive studio photography.")
    neg="multiple robots, missing limb, detached feet, floating, duplicate legs, gray blobs, bad geometry, blurry, illustration, text"
    return {
      "1":{"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":"v1-5-pruned-emaonly.safetensors"}},
      "2":{"class_type":"CLIPTextEncode","inputs":{"text":prompt,"clip":["1",1]}},
      "3":{"class_type":"CLIPTextEncode","inputs":{"text":neg,"clip":["1",1]}},
      "4":{"class_type":"LoadImage","inputs":{"image":"FWAI_VQ03_V5_B_INPUT.png"}},
      "5":{"class_type":"VAEEncode","inputs":{"pixels":["4",0],"vae":["1",2]}},
      "6":{"class_type":"KSampler","inputs":{"model":["1",0],"positive":["2",0],"negative":["3",0],"latent_image":["5",0],
        "seed":6503112301,"steps":14,"cfg":5.0,"sampler_name":"euler","scheduler":"normal","denoise":.18}},
      "7":{"class_type":"VAEDecode","inputs":{"samples":["6",0],"vae":["1",2]}},
      "8":{"class_type":"SaveImage","inputs":{"images":["7",0],"filename_prefix":"FWAI_VQ03_LOCAL_GEOMETRY_REFINEMENT"}}}
def composite(r):
    with Image.open(OUT/"VQ03_COMFY_INPUT.png") as orig,Image.open(OUT/"VQ03_COMFY_RAW.png") as edit,Image.open(OUT/"VQ03_COMFY_MASK.png") as mask:
        a=orig.convert("RGB");b=edit.convert("RGB");m=mask.convert("L")
        out=Image.composite(b,a,m)
        rawpixel=a.load();pixel=out.load();mp=m.load()
        changed=sum(1 for y in range(576) for x in range(1024) if mp[x,y]==0 and rawpixel[x,y]!=pixel[x,y])
        assert changed==0
        out=out.resize((1280,720),Image.Resampling.LANCZOS)
        path=OUT/"VQ03_B_LOCAL_COMFY_PREVIEW.png";out.save(path)
        sheet=Image.new("RGB",(2560,720))
        with Image.open(source) as source_im:sheet.paste(source_im.convert("RGB"),(0,0))
        sheet.paste(out,(1280,0));sheet.save(OUT/"VQ03_COMFY_BEFORE_AFTER.png")
    r.update(status="complete",output=path.name,output_sha256=sha(path),outside_mask_changes=changed,
       photorealism_approved=False,vinyl_simulation_approved=False,paid_calls=0)
    receipt.write_text(json.dumps(r,indent=2))
    print("FWAI_VQ03_05_COMFY_TECHNICAL_PASS",path,flush=True)
def main():
    sh,im,m=prepare()
    if receipt.exists():
        r=json.loads(receipt.read_text())
        if (r["source_sha256"],r["input_sha256"],r["mask_sha256"])!=(sh,im,m):raise RuntimeError("Receipt inputs changed")
        if r["status"]=="complete":
            assert sha(OUT/r["output"])==r["output_sha256"]
            print("FWAI_VQ03_05_CACHED_VERIFIED");return
        if r["status"]!="submitted":raise RuntimeError("Ambiguous provider state, no blind retry: "+r["status"])
    else:
        r={"schema":"FWAI_VQ03_LOCAL_COMFY_POC_V1","status":"planned","source_sha256":sh,"input_sha256":im,
        "mask_sha256":m,"paid_calls":0,"publish":False}
        receipt.write_text(json.dumps(r,indent=2))
    if r["status"]=="planned":
        if req("/queue").get("queue_running") or req("/queue").get("queue_pending"):raise RuntimeError("Comfy GPU queue busy")
        r["status"]="submitting";receipt.write_text(json.dumps(r,indent=2))
        try:
            response=req("/prompt",{"prompt":graph(),"client_id":"FWAI_VQ03_OWNER_AUTH_LOCAL_ONLY"})
        except Exception:
            r["status"]="ambiguous";receipt.write_text(json.dumps(r,indent=2));raise
        if response.get("node_errors"):
            r["status"]="rejected";r["node_errors"]=response["node_errors"];receipt.write_text(json.dumps(r,indent=2))
            raise RuntimeError("Comfy rejected graph")
        uuid.UUID(response["prompt_id"])
        r.update(status="submitted",task_id=response["prompt_id"]);receipt.write_text(json.dumps(r,indent=2))
    for i in range(120):
        result=req("/history/"+r["task_id"]).get(r["task_id"])
        if result:
            if result.get("status",{}).get("status_str")=="error":
                r["status"]="failed";receipt.write_text(json.dumps(r,indent=2));raise RuntimeError("GPU task failed")
            imgs=result.get("outputs",{}).get("8",{}).get("images",[])
            if len(imgs)==1:
                f=imgs[0]
                qry=urllib.parse.urlencode({"filename":f["filename"],"subfolder":f.get("subfolder",""),"type":f.get("type","output")})
                (OUT/"VQ03_COMFY_RAW.png").write_bytes(req("/view?"+qry,raw=True))
                composite(r);return
        time.sleep(3)
    raise TimeoutError("GPU task not finished; persistent receipt, no blind retries")
if __name__=="__main__":main()
