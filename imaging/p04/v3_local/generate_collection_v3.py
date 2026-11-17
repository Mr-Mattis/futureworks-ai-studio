"""Future Works P04 quality recovery: LOCAL ONLY.
Ten unique 768x512 SD1.5 generations at proven sampler settings.
Exactly one Comfy submission per identity, durable receipts, hash-index.
Pillow delivery is resize only, not neural super resolution.
"""
import hashlib,json,time,urllib.request,urllib.parse,uuid
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter, ImageDraw
ROOT=Path.home()/"Documents"/"futureworks-p04-data"/"collection-v3"
ROOT.mkdir(parents=True,exist_ok=True)
J=ROOT/"receipts.json"
API="http://127.0.0.1:8188"
MODEL="v1-5-pruned-emaonly.safetensors"
DESIGNS=[
("01","manta ray orbital service drone with wide swept wings and six thrusters"),
("02","six legged lunar excavation robot with articulating drill arms"),
("03","deep sea humanoid salvage android with pressure resistant diving armor"),
("04","folding four wheel planetary research rover with articulated panels"),
("05","circular antigravity reconnaissance drone with central glowing sensor"),
("06","long legged robotic crane bird with metal solar sail wings"),
("07","eight legged asteroid mining spider robot with precision drills"),
("08","heavy quadruped arctic search and rescue robot with broad paws"),
("09","small modular floating robot surrounded by coordinated microdrones"),
("10","crescent shaped orbital telescope robot with articulated instruments")
]
NEG="low quality, blurry, deformed, malformed limbs, fused wheels, multiple heads, watermark, text, logo, lettering, duplicate objects"
def sha(raw):return hashlib.sha256(raw).hexdigest()
def api(path,payload=None,binary=False):
    raw=json.dumps(payload).encode() if payload is not None else None
    req=urllib.request.Request(API+path,data=raw,headers={"Content-Type":"application/json"},method="POST" if raw is not None else "GET")
    with urllib.request.urlopen(req,timeout=180) as r:return r.read() if binary else json.load(r)
def graph(n,concept):
    prompt="Photorealistic original sci-fi concept art of "+concept+", intricate realistic engineered metal detail, graphite titanium, electric cyan accents, dramatic cinematic studio lighting, full complete machine, carefully designed mechanical proportions, sharp focus, professional 3D product render, no typography, fictional technology"
    return {"1":{"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":MODEL}},"2":{"class_type":"CLIPTextEncode","inputs":{"text":prompt,"clip":["1",1]}},"3":{"class_type":"CLIPTextEncode","inputs":{"text":NEG,"clip":["1",1]}},"4":{"class_type":"EmptyLatentImage","inputs":{"width":768,"height":512,"batch_size":1}},"5":{"class_type":"KSampler","inputs":{"seed":771116000+int(n)*739,"steps":22,"cfg":6.5,"sampler_name":"euler","scheduler":"normal","denoise":1.0,"model":["1",0],"positive":["2",0],"negative":["3",0],"latent_image":["4",0]}},"6":{"class_type":"VAEDecode","inputs":{"samples":["5",0],"vae":["1",2]}},"7":{"class_type":"SaveImage","inputs":{"filename_prefix":"FWAI_P04_V3_"+n,"images":["6",0]}}}
def save(j):
    t=J.with_suffix(".part");t.write_text(json.dumps(j,indent=2));t.replace(J)
def run(n,concept,j):
    rec=j.setdefault(n,{"concept":concept,"state":"planned"})
    src=ROOT/("V3_"+n+"_768x512.png")
    if rec["state"]=="complete":
        if sha(src.read_bytes())!=rec["sha256"]:raise RuntimeError("asset hash mismatch "+n)
        print(n,"already complete",flush=True);return
    if rec["state"]=="planned":
        rec["state"]="submitting";save(j)
        receipt=api("/prompt",{"prompt":graph(n,concept),"client_id":"FWAI_P04_V3"})["prompt_id"]
        uuid.UUID(receipt);rec["receipt"]=receipt;rec["state"]="submitted";save(j)
        print(n,"submitted",flush=True)
    if rec["state"]!="submitted":raise RuntimeError("ambiguous receipt: manual review needed "+n)
    for i in range(300):
        hist=api("/history/"+rec["receipt"]).get(rec["receipt"])
        if hist:
            if hist.get("status",{}).get("status_str")=="error":raise RuntimeError("generation failed "+n)
            images=hist.get("outputs",{}).get("7",{}).get("images",[])
            if len(images)==1:
                item=images[0]
                params=urllib.parse.urlencode({"filename":item["filename"],"subfolder":item["subfolder"],"type":"output"})
                blob=api("/view?"+params,binary=True)
                temp=src.with_suffix(".part");temp.write_bytes(blob)
                with Image.open(temp) as im:
                    if im.size!=(768,512):raise RuntimeError("dimensions mismatch")
                    im.verify()
                temp.replace(src)
                rec.update({"state":"complete","sha256":sha(blob),"prompt_id":rec["receipt"],"width":768,"height":512,"seed":771116000+int(n)*739,"model":MODEL})
                save(j);print(n,"COMPLETE",flush=True);return
        time.sleep(2.5)
    raise TimeoutError("do not resubmit; reconcile "+n)
def sheet(j):
    pics=Image.new("RGB",(1600,460),(20,23,28));d=ImageDraw.Draw(pics)
    for i,(n,concept) in enumerate(DESIGNS):
        src=ROOT/("V3_"+n+"_768x512.png")
        if not src.exists():continue
        with Image.open(src) as im:
            thumb=ImageOps.fit(im.convert("RGB"),(308,192),method=Image.Resampling.LANCZOS)
            x=i%5*320+6;y=i//5*230+6
            pics.paste(thumb,(x,y));d.text((x,y+195),n+" "+concept[:32],fill="white")
            full=ImageOps.fit(im.convert("RGB"),(1920,1080),method=Image.Resampling.LANCZOS,centering=(.5,.5))
            dest=ROOT/("V3_"+n+"_1920x1080_PREVIEW.png")
            full.save(dest,optimize=True)
    pics.save(ROOT/"P04_V3_CONTACT_SHEET.png")
if __name__=="__main__":
    model_path=Path.home()/"Documents"/"futureworks-p04-comfyui"/"models"/"checkpoints"/MODEL
    if not model_path.is_file():raise RuntimeError("pinned checkpoint missing")
    with model_path.open("rb") as f: model_hash=hashlib.file_digest(f,"sha256").hexdigest()
    if model_hash!="6ce0161689b3853acaa03779ec93eafe75a02f4ced659bee03f50797806fa2fa":raise RuntimeError("checkpoint SHA mismatch")
    if not api("/system_stats").get("devices"):raise RuntimeError("Comfy offline")
    j=json.loads(J.read_text()) if J.exists() else {}
    for n,c in DESIGNS:run(n,c,j)
    sheet(j)
    print("DONE",len([x for x in j.values() if x["state"]=="complete"]),flush=True)
