"""Owner-authorized FWAI-T001 local-only material look-development on Radeon GPU.

Uses exact owner-approved geometry/mechanical hashes; two independent material
variants. No environment scene, external upload, paid API, publishing or
production n8n writes. Atomic before-submit receipt prevents blind resubmission.
"""
from pathlib import Path
import hashlib,json,uuid,time,urllib.request,urllib.parse,shutil
from PIL import Image,ImageOps,ImageDraw
HOME=Path.home()
ROOT=HOME/"Documents"/"futureworks-p04-data"/"p04-06-material-lookdev"
COMFY=HOME/"Documents"/"futureworks-p04-comfyui"
API="http://127.0.0.1:8188"
J=ROOT/"gpu-receipts.json"
MODEL="Realistic_Vision_V6.0_NV_B1_fp16.safetensors"
VAE="vae-ft-mse-840000-ema-pruned.safetensors"
UPSCALE="RealESRGAN_x4plus.safetensors"
SHAS={
 COMFY/"models"/"checkpoints"/MODEL:"c48bfd159cd7a6507b128685e963c398fa72399cefafaf603781df50ce836cc7",
 COMFY/"models"/"vae"/VAE:"735e4c3a447a3255760d7f86845f09f937809baa529c17370d83e4c3758f3c75",
 COMFY/"models"/"upscale_models"/UPSCALE:"37f9a931c215f040aa6d50f711f2cb115f713c46df1d0d6469a8bd7bfe9a60bb",
}
APPROVED_G="7bc0379c02632018e78dfbea6eab467071ec0ffe9f97b3c9522c1634bf51b77e"
APPROVED_M="07dc8ea721e2d2d69d47585bc67268c31a2ceb9d96e0724a5ffc55fd17465c5f"
VARIANTS=[
 ("graphite_alloy",0.29,26011801,"dark graphite bead-blasted titanium structural truss, brushed metallic gray mechanical panels, precision visible screws and joints, slight metallic grease at actuators, intricate engineering micro-details and realistic wear"),
 ("ceramic_titanium",0.36,26011802,"satin silver titanium and matte pearl ceramic composite exterior panels, precisely machined dark joints, tiny visible connector bolts, industrial surface wear only near load joints, physically credible brushed metal finish")
]
PROMPT=("RAW real-life industrial product photography, physically tangible original civilian ORBITAL CONSTRUCTION PLATFORM machine, photographed from perpendicular straight top-down engineering inspection camera against completely plain neutral seamless charcoal background, subject alone in frame, preserve EXACT entire original six-sided open hexagonal truss ring with six attached articulated twin-link fabrication arms, exact geometry from provided image, six metal-jointed fabrication arm assemblies, authentic material engineering, realistic load-bearing steel structures, bolts, access panels, independent protected electrical cable conduits, central human-scale circular maintenance airlock, subtle natural physical reflections, impeccable fine precision manufacturing, realistic metallic microtextures, credible metal scratches, high resolution macro details throughout, plain neutral backdrop, believable studio softbox reflections, tangible full-scale industrial hardware, focus-stacked product photo, sharp, no scale distortion. ")
NEG=("painted artwork, sci fi illustration, concept art, fantasy, toy, miniature, 3d video game render, military, weapon, camouflage, army, fighter, planet Earth, space stars, spaceship battlefield, orbit panorama, landscape, forest, terrain, building, sky, human face, portrait, person, random arms, missing arms, extra arms, malformed mechanical geometry, melted truss, plastic looking, hazy, bloom, fog, blurry, noise artifacts, watermark, captions, letters, logos")
def sha(b):return hashlib.sha256(b).hexdigest()
def req(path,payload=None,binary=False):
 data=json.dumps(payload).encode() if payload is not None else None
 request=urllib.request.Request(API+path,data=data,headers={"Content-Type":"application/json"},method="POST" if data is not None else "GET")
 with urllib.request.urlopen(request,timeout=120) as response:return response.read() if binary else json.load(response)
def save(j):
 tmp=J.with_name(J.name+".tmp");tmp.write_text(json.dumps(j,indent=2));tmp.replace(J)
def node_graph(source,denoise,seed,material):
 return {
 "1":{"class_type":"LoadImage","inputs":{"image":source}},
 "2":{"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":MODEL}},
 "3":{"class_type":"VAELoader","inputs":{"vae_name":VAE}},
 "4":{"class_type":"CLIPTextEncode","inputs":{"text":PROMPT+material,"clip":["2",1]}},
 "5":{"class_type":"CLIPTextEncode","inputs":{"text":NEG,"clip":["2",1]}},
 "6":{"class_type":"VAEEncode","inputs":{"pixels":["1",0],"vae":["3",0]}},
 "7":{"class_type":"KSampler","inputs":{"seed":seed,"steps":26,"cfg":5.5,"sampler_name":"dpmpp_2m","scheduler":"karras",
 "denoise":denoise,"model":["2",0],"positive":["4",0],"negative":["5",0],"latent_image":["6",0]}},
 "8":{"class_type":"VAEDecode","inputs":{"samples":["7",0],"vae":["3",0]}},
 "9":{"class_type":"UpscaleModelLoader","inputs":{"model_name":UPSCALE}},
 "10":{"class_type":"ImageUpscaleWithModel","inputs":{"upscale_model":["9",0],"image":["8",0]}},
 "11":{"class_type":"ImageScale","inputs":{"image":["10",0],"upscale_method":"lanczos","width":1920,"height":1080,"crop":"center"}},
 "12":{"class_type":"SaveImage","inputs":{"filename_prefix":"FWAI_T001_MATERIAL_"+source.split('.')[0],"images":["11",0]}}}
def process(name,denoise,seed,material,j):
 source=ROOT/f"FWAI-T001_MATERIAL_SOURCE_{name}_896x512.png"
 if not source.is_file():raise RuntimeError("Missing deterministic source")
 digest=sha(source.read_bytes())
 input_name="FWAI_T001_MATERIAL_"+name+"_"+digest[:16]+".png"
 target=COMFY/"input"/input_name
 if target.exists():
  if sha(target.read_bytes())!=digest:raise RuntimeError("Comfy input collision")
 else:shutil.copyfile(source,target)
 row=j.setdefault(name,{"state":"planned","seed":seed,"denoise":denoise,"source_sha256":digest,
   "model":MODEL,"geometry_sha256":APPROVED_G,"mechanical_sha256":APPROVED_M,
   "environment":None,"external_upload":False,"paid_calls":0,"human_approval":"PENDING"})
 finish=ROOT/f"FWAI-T001_MATERIAL_{name}_1920x1080.png"
 if row["state"]=="complete":
  if sha(finish.read_bytes())!=row["output_sha256"]:raise RuntimeError("Output changed")
  print(name,"already completed with SHA verification",flush=True);return
 if row["state"]=="planned":
  row["state"]="submitting";save(j)
  receipt=req("/prompt",{"prompt":node_graph(input_name,denoise,seed,material),
     "client_id":"FWAI_P04_06_LOCAL_MATERIAL_ONLY"})["prompt_id"]
  uuid.UUID(receipt);row["prompt_id"]=receipt;row["state"]="submitted";save(j)
  print(name,"submitted",receipt,flush=True)
 if row["state"]!="submitted":raise RuntimeError("Ambiguous receipt. Manual recovery required.")
 for _ in range(220):
  history=req("/history/"+row["prompt_id"]).get(row["prompt_id"])
  if history:
   if history.get("status",{}).get("status_str")=="error":raise RuntimeError("Comfy reported failed task")
   images=history.get("outputs",{}).get("12",{}).get("images",[])
   if len(images)==1:
    a=images[0]
    q=urllib.parse.urlencode({"filename":a["filename"],"subfolder":a["subfolder"],"type":"output"})
    data=req("/view?"+q,binary=True)
    part=finish.with_suffix(".pending");part.write_bytes(data)
    with Image.open(part) as image:
     if image.size!=(1920,1080):raise RuntimeError("Final dimension failure")
     image.verify()
    part.replace(finish)
    row.update({"state":"complete","output_sha256":sha(data),"output_bytes":len(data),
      "resolution":[1920,1080]})
    save(j);print(name,"COMPLETE_1920x1080",flush=True);return
  time.sleep(3)
 raise TimeoutError("Comfy task ongoing; no blind retries")
if __name__=="__main__":
 assert sha((HOME/"Documents"/"futureworks-p04-data"/"p04-06-modular-preview"/"FWAI-T001_geometry_spec.json").read_bytes())==APPROVED_G
 assert sha((HOME/"Documents"/"futureworks-p04-data"/"p04-06-modular-preview"/"FWAI-T001_mechanical_detail.json").read_bytes())==APPROVED_M
 for file,digest in SHAS.items():
  if not file.is_file():raise RuntimeError("Missing pinned model "+file.name)
  with file.open("rb") as f:
   if hashlib.file_digest(f,"sha256").hexdigest()!=digest:raise RuntimeError("Model altered "+file.name)
 if not req("/system_stats").get("devices"):raise RuntimeError("No local GPU")
 j=json.loads(J.read_text()) if J.is_file() else {}
 for args in VARIANTS:process(*args,j)
 result=Image.new("RGB",(1440,880),(13,18,24));d=ImageDraw.Draw(result)
 for idx,(name,_,_,_) in enumerate(VARIANTS):
  with Image.open(ROOT/f"FWAI-T001_MATERIAL_{name}_1920x1080.png") as img:
   scaled=ImageOps.contain(img.convert("RGB"),(1400,395),method=Image.Resampling.LANCZOS)
   result.paste(scaled,(20+(1400-scaled.width)//2,idx*435+10+(395-scaled.height)//2))
  d.text((30,idx*435+408),name+" | FWAI-T001 | real-life material test, no environment",fill="white")
 result.save(ROOT/"FWAI-T001_MATERIAL_AB_CONTACT_SHEET.png")
 print("TWO_LOCAL_GPU_MATERIAL_VARIANTS_READY_FOR_OWNER_REVIEW",flush=True)
