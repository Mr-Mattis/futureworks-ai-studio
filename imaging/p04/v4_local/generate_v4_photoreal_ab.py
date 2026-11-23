"""FWAI P04 V4 photorealism A/B proof, local-only. No paid APIs.

A: generate a new photo-real mechanical rover concept.
B: img2img revise the original V3 rover composition.
Both use independently SHA256-verified Realistic Vision v6 fp16 and MIT VAE,
then local RealESRGAN upscale to delivery 1920x1080. Both are owner-review
candidates, never automatically approved/promoted.
"""
import hashlib,json,time,urllib.request,urllib.parse,uuid,shutil
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
HOME=Path.home()
COMFY=HOME/"Documents"/"futureworks-p04-comfyui"
ROOT=HOME/"Documents"/"futureworks-p04-data"/"collection-v4-photoreal-ab"
ROOT.mkdir(parents=True,exist_ok=True)
API="http://127.0.0.1:8188"
MODEL="Realistic_Vision_V6.0_NV_B1_fp16.safetensors"
VAE="vae-ft-mse-840000-ema-pruned.safetensors"
UPSCALE="RealESRGAN_x4plus.safetensors"
FILES={
 COMFY/"models"/"checkpoints"/MODEL:"c48bfd159cd7a6507b128685e963c398fa72399cefafaf603781df50ce836cc7",
 COMFY/"models"/"vae"/VAE:"735e4c3a447a3255760d7f86845f09f937809baa529c17370d83e4c3758f3c75",
 COMFY/"models"/"upscale_models"/UPSCALE:"37f9a931c215f040aa6d50f711f2cb115f713c46df1d0d6469a8bd7bfe9a60bb"}
PROMPT=("RAW documentary industrial photograph of a credible futuristic robotic lunar exploration rover, real-world heavy-duty four-wheel suspension and tank tread tire blocks individually visible, close sharply detailed hydraulic pistons, steel bolts and hex fasteners, steel panel junctions with visible weld seams and rubber gaskets, physically plausible exposed servomotors and protected cable runs, weathered bead-blasted aluminum, graphite composite and stainless steel, dust accumulated in seams, scratches, oxidized edges, subtle grease streaks on joints, physically correct reflections, natural overcast directional lighting and contact shadows, cinematic atmospheric depth, gritty photojournalistic industrial engineering prototype photograph, 50mm lens f/8, ultra detailed texture, accurate proportions, single coherent machine, landscape framing, desaturated realistic color grading")
NEG=("cartoon, digital art, concept painting, illustration, hand drawing, anime, stylized, CGI, video game render, low-poly, airbrushed metal, plastic toy, fantasy, physically impossible geometry, fused wheels, malformed tires, vague panels, redundant limbs, extra wheels, blurry, low resolution, overexposed, watermark, words, logo, text")
J=ROOT/"receipts.json"
def sha(b):return hashlib.sha256(b).hexdigest()
def write(j):
    tmp=J.with_suffix(".part");tmp.write_text(json.dumps(j,indent=2));tmp.replace(J)
def req(path,payload=None,binary=False):
    body=json.dumps(payload).encode() if payload is not None else None
    r=urllib.request.Request(API+path,data=body,headers={"Content-Type":"application/json"},method="POST" if body is not None else "GET")
    with urllib.request.urlopen(r,timeout=180) as f:return f.read() if binary else json.load(f)
def graph(mode,filename):
    n={
      "1":{"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":MODEL}},
      "2":{"class_type":"CLIPTextEncode","inputs":{"text":PROMPT,"clip":["1",1]}},
      "3":{"class_type":"CLIPTextEncode","inputs":{"text":NEG,"clip":["1",1]}},
      "4":{"class_type":"VAELoader","inputs":{"vae_name":VAE}}
    }
    if mode=="A":
        n["5"]={"class_type":"EmptyLatentImage","inputs":{"width":768,"height":512,"batch_size":1}}
    else:
        n["9"]={"class_type":"LoadImage","inputs":{"image":filename}}
        n["10"]={"class_type":"VAEEncode","inputs":{"pixels":["9",0],"vae":["4",0]}}
    n["6"]={"class_type":"KSampler","inputs":{"seed":26111655+(1 if mode=="A" else 2),
       "steps":34,"cfg":6.5,"sampler_name":"dpmpp_2m","scheduler":"karras",
       "denoise":1.0 if mode=="A" else .5,
       "model":["1",0],"positive":["2",0],"negative":["3",0],
       "latent_image":["5",0] if mode=="A" else ["10",0]}}
    n["7"]={"class_type":"VAEDecode","inputs":{"samples":["6",0],"vae":["4",0]}}
    n["8"]={"class_type":"SaveImage","inputs":{"filename_prefix":"FWAI_V4_PHOTO_"+mode,"images":["7",0]}}
    return n
def upscale_graph(filename,mode):
    return {"1":{"class_type":"LoadImage","inputs":{"image":filename}},
            "2":{"class_type":"UpscaleModelLoader","inputs":{"model_name":UPSCALE}},
            "3":{"class_type":"ImageUpscaleWithModel","inputs":{"upscale_model":["2",0],"image":["1",0]}},
            "4":{"class_type":"ImageScale","inputs":{"image":["3",0],"upscale_method":"lanczos","width":1920,"height":1080,"crop":"center"}},
            "5":{"class_type":"SaveImage","inputs":{"filename_prefix":"FWAI_V4_PHOTO_1080P_"+mode,"images":["4",0]}}}
def process(key,graph_spec,output_node,expected,j):
    row=j.setdefault(key,{"state":"planned","model":MODEL,"vae":VAE})
    target=ROOT/(key+".png")
    if row["state"]=="complete":
        if not target.is_file() or sha(target.read_bytes())!=row["sha256"]:raise RuntimeError("immutable completed asset changed "+key)
        print(key,"already verified",flush=True);return
    if row["state"]=="planned":
        row["state"]="submitting";write(j)
        rid=req("/prompt",{"prompt":graph_spec,"client_id":"FWAI_P04_V4_PHOTO_AB"})["prompt_id"]
        uuid.UUID(rid);row["task_id"]=rid;row["state"]="submitted";write(j)
        print(key,"submitted",flush=True)
    if row["state"]!="submitted":raise RuntimeError("ambiguous receipt, manual reconciliation "+key)
    for _ in range(250):
        result=req("/history/"+row["task_id"]).get(row["task_id"])
        if result:
            if result.get("status",{}).get("status_str")=="error":raise RuntimeError("Comfy V4 job failed "+key)
            outputs=result.get("outputs",{}).get(output_node,{}).get("images",[])
            if len(outputs)==1:
                e=outputs[0]
                q=urllib.parse.urlencode({"filename":e["filename"],"subfolder":e["subfolder"],"type":"output"})
                raw=req("/view?"+q,binary=True)
                part=target.with_suffix(".part")
                part.write_bytes(raw)
                with Image.open(part) as im:
                    if im.size!=expected:raise RuntimeError("image resolution mismatch "+key)
                    im.verify()
                part.replace(target)
                row.update({"state":"complete","sha256":sha(raw),"resolution":list(expected)})
                write(j);print(key,"COMPLETE",flush=True);return
        time.sleep(3)
    raise TimeoutError("Do not requeue unknown task "+key)
def localcopy(source,key):
    name="FWAI_V4_INPUT_"+key+"_"+sha(source.read_bytes())[:12]+".png"
    dest=COMFY/"input"/name
    if dest.exists() and sha(dest.read_bytes())!=sha(source.read_bytes()):raise RuntimeError("Comfy input collision")
    if not dest.exists():shutil.copyfile(source,dest)
    return name
def main():
    for path,digest in FILES.items():
        if not path.is_file():raise RuntimeError("Missing pinned model "+path.name)
        with path.open("rb") as f:
            if hashlib.file_digest(f,"sha256").hexdigest()!=digest:raise RuntimeError("Model SHA mismatch "+path.name)
    if not req("/system_stats").get("devices"):raise RuntimeError("Comfy unavailable")
    j=json.loads(J.read_text()) if J.exists() else {}
    reference=HOME/"Documents"/"futureworks-p04-data"/"collection-v3"/"V3_04_768x512.png"
    for mode in ("A","B"):
        filename=localcopy(reference,"V3_04") if mode=="B" else None
        process("V4_"+mode+"_NATIVE",graph(mode,filename),"8",(768,512),j)
        source=ROOT/("V4_"+mode+"_NATIVE.png")
        name=localcopy(source,mode)
        process("V4_"+mode+"_ESRGAN_1080P",upscale_graph(name,mode),"5",(1920,1080),j)
    comparison=Image.new("RGB",(1280,420),(17,23,28))
    d=ImageDraw.Draw(comparison)
    for i,mode in enumerate(("A","B")):
        with Image.open(ROOT/("V4_"+mode+"_ESRGAN_1080P.png")) as image:
            comparison.paste(ImageOps.fit(image.convert("RGB"),(625,352),method=Image.Resampling.LANCZOS),(i*640+7,8))
        d.text((i*640+12,372),f"V4 {mode} / Realistic Vision + RealESRGAN / PHOTO TEST",fill="white")
    comparison.save(ROOT/"V4_PHOTOREAL_AB_CONTACT_SHEET.png")
    print("V4_PHOTO_AB_TWO_IMAGES_READY_FOR_OWNER_REVIEW",flush=True)
if __name__=="__main__":main()
