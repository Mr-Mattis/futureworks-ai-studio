"""FWAI local V3 RealESRGAN super-resolution, offline external providers.
ComfyUI already running with licensed 4x super-resolution model.
"""
import hashlib,json,time,urllib.request,urllib.parse,uuid,shutil
from pathlib import Path
from PIL import Image
HOME=Path.home()
ROOT=HOME/"Documents"/"futureworks-p04-data"/"collection-v3"
COMFY=HOME/"Documents"/"futureworks-p04-comfyui"
INPUT=COMFY/"input"
MODEL=COMFY/"models"/"upscale_models"/"RealESRGAN_x4plus.safetensors"
EXPECTED_MODEL="37f9a931c215f040aa6d50f711f2cb115f713c46df1d0d6469a8bd7bfe9a60bb"
LOG=ROOT/"upscale-receipts.json"
BASE="http://127.0.0.1:8188"
def sha(b):return hashlib.sha256(b).hexdigest()
def req(path,data=None,binary=False):
    payload=json.dumps(data).encode() if data is not None else None
    r=urllib.request.Request(BASE+path,data=payload,headers={"Content-Type":"application/json"},method="POST" if payload is not None else "GET")
    with urllib.request.urlopen(r,timeout=180) as f:return f.read() if binary else json.load(f)
def write(j):
    t=LOG.with_suffix(".part");t.write_text(json.dumps(j,indent=2));t.replace(LOG)
def workflow(source,n):
    return {
    "1":{"class_type":"LoadImage","inputs":{"image":source}},
    "2":{"class_type":"UpscaleModelLoader","inputs":{"model_name":"RealESRGAN_x4plus.safetensors"}},
    "3":{"class_type":"ImageUpscaleWithModel","inputs":{"upscale_model":["2",0],"image":["1",0]}},
    "4":{"class_type":"ImageScale","inputs":{"image":["3",0],"upscale_method":"lanczos","width":1920,"height":1080,"crop":"center"}},
    "5":{"class_type":"SaveImage","inputs":{"filename_prefix":"FWAI_V3_ESRGAN_"+n,"images":["4",0]}}
    }
def run(n,j):
    raw_src=ROOT/("V3_"+n+"_768x512.png")
    original=raw_src.read_bytes()
    source_sha=sha(original)
    dest=ROOT/("V3_"+n+"_1920x1080_ESRGAN.png")
    row=j.setdefault(n,{"source_sha256":source_sha,"state":"planned","upscaler_sha256":EXPECTED_MODEL})
    if row["source_sha256"]!=source_sha:raise RuntimeError("source image changed "+n)
    if row["state"]=="complete":
        if not dest.is_file() or sha(dest.read_bytes())!=row["sha256"]:raise RuntimeError("output corrupted "+n)
        print(n,"already verified",flush=True);return
    filename="FWAI_V3_INPUT_"+n+"_"+source_sha[:12]+".png"
    input_path=INPUT/filename
    if input_path.exists():
        if sha(input_path.read_bytes())!=source_sha:raise RuntimeError("Comfy input collision")
    else: input_path.write_bytes(original)
    if row["state"]=="planned":
        row["state"]="submitting";write(j)
        receipt=req("/prompt",{"prompt":workflow(filename,n),"client_id":"FWAI_V3_UPSCALE"})["prompt_id"]
        uuid.UUID(receipt);row["receipt"]=receipt;row["state"]="submitted";write(j)
        print(n,"submitted",flush=True)
    if row["state"]!="submitted":raise RuntimeError("unknown state: no automatic retry")
    for _ in range(300):
        hist=req("/history/"+row["receipt"]).get(row["receipt"])
        if hist:
            if hist.get("status",{}).get("status_str")=="error":raise RuntimeError("Comfy upscale failed "+n)
            imgs=hist.get("outputs",{}).get("5",{}).get("images",[])
            if len(imgs)==1:
                item=imgs[0]
                q=urllib.parse.urlencode({"filename":item["filename"],"subfolder":item["subfolder"],"type":"output"})
                blob=req("/view?"+q,binary=True)
                t=dest.with_suffix(".part")
                t.write_bytes(blob)
                with Image.open(t) as im:
                    if im.size!=(1920,1080):raise RuntimeError("not 1080p")
                    im.verify()
                t.replace(dest)
                row.update({"state":"complete","sha256":sha(blob),"width":1920,"height":1080,"method":"RealESRGAN_x4plus + Lanczos"})
                write(j);print(n,"COMPLETE",flush=True);return
        time.sleep(3)
    raise TimeoutError("manual reconciliation required "+n)
if __name__=="__main__":
    if not MODEL.is_file():raise RuntimeError("upscale model missing")
    with MODEL.open("rb") as f:
        if hashlib.file_digest(f,"sha256").hexdigest()!=EXPECTED_MODEL:raise RuntimeError("upscale model SHA changed")
    m=req("/object_info/UpscaleModelLoader")
    if "UpscaleModelLoader" not in m:raise RuntimeError("UpscaleModelLoader not registered: check Spandrel installation / restart")
    j=json.loads(LOG.read_text()) if LOG.is_file() else {}
    for i in range(1,11):run(str(i).zfill(2),j)
    print("ALL_COMPLETE",sum(v["state"]=="complete" for v in j.values()),flush=True)
