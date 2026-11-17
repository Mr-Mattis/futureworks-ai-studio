"""FWAI P04 V5 — exactly ten LOCAL photographic future-civilization designs.

Designed with user-approved creative direction. Isolated ComfyUI on Windows:
no Runway uploads, no paid provider, no publication. This is NEW art and MUST
receive human visual and commercial-rights approval before any external use.
"""
import hashlib,json,time,urllib.request,urllib.parse,uuid,sys,os
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps

HOME=Path.home()
COMFY=HOME/"Documents"/"futureworks-p04-comfyui"
ROOT=HOME/"Documents"/"futureworks-p04-data"/"collection-v5-ai-civilization"
ROOT.mkdir(parents=True,exist_ok=True)
JOURNAL=ROOT/"receipts.json"
BASE="http://127.0.0.1:8188"
MODEL="Realistic_Vision_V6.0_NV_B1_fp16.safetensors"
VAE="vae-ft-mse-840000-ema-pruned.safetensors"
UPSCALER="RealESRGAN_x4plus.safetensors"
EXPECTED={
 COMFY/"models"/"checkpoints"/MODEL:"c48bfd159cd7a6507b128685e963c398fa72399cefafaf603781df50ce836cc7",
 COMFY/"models"/"vae"/VAE:"735e4c3a447a3255760d7f86845f09f937809baa529c17370d83e4c3758f3c75",
 COMFY/"models"/"upscale_models"/UPSCALER:"37f9a931c215f040aa6d50f711f2cb115f713c46df1d0d6469a8bd7bfe9a60bb"}
DESIGNS=[
("01","Orbital lattice weaver","40-meter wide autonomous orbital megastructure assembly platform, open graceful hexagonal tension truss and six extendable arc-shaped additive fabrication manipulators, slender human-size pressure maintenance airlock, illuminated ceramic radiator vanes, satellite-mounted workshop, panoramic space vista"),
("02","Pelagic ecosystem restorer","15-meter floating ocean reef restoration machine, flexible manta-like sensor sails, circular porous bio-ceramic frame, gentle underwater coral nursery appendages, tiny two-meter service boat for human scale, realistic exposed hydraulic and water-resistant cable routing, blue open sea"),
("03","Desert atmospheric water harvester","12-meter tall self-deploying atmospheric moisture condensing sculpture, umbrella-shaped responsive membrane collectors, slender ceramic composite towers and microfluidic plumbing, worker-scale maintenance stairs and service hatch, dusty desert settlement at sunrise"),
("04","Mantle geoscience walker","9-meter civilian deep-crust geological analysis machine with four articulated climbing appendages and heavily insulated sensor probes, visible high-temperature ceramics and mineral sample cassette, meter-scale access hatch, volcanic subterranean survey station"),
("05","Skyborne biome conservatory","25-meter aerial conservation platform carrying a translucent closed-loop living greenhouse, three buoyant aerodynamic adaptive membranes and bio-material tensile structure, visible plants and human-scale access corridor, cloud-filled future agricultural valley"),
("06","Lunar regolith foundry","20-meter distributed moon habitat construction foundry with vaulted sintering tracks and architecturally slender self-assembling gantry robotics, open material sorting chambers and 2-meter human-pressure airlock, regolith powder and thermal shades, nonmilitary lunar colony"),
("07","Swarm infrastructure atelier","7-meter self-repairing city infrastructure depot shaped like a vertical branching lattice of docking cells, hundreds of small robotic fabrication assistants arranged in orderly charging bays, clear human-scale street walkway and solar canopy, clean advanced civic plaza"),
("08","Microgravity biomedical fabricator","6-meter peaceful orbital autonomous medical biomanufacturing capsule, graceful paired sterile transparent tissue-scaffold chambers, authentic sealed micro-robot manipulators and pressure bulkheads, small crew window for scale, hospital research spacecraft"),
("09","Interplanetary debris curator","35-meter robotic orbital salvage collector with fluid geometric programmable lattice-net hoop and five precision low-force grapple arms, tiny 2-meter maintenance platform and visible thermal radiators, elegant utilitarian engineering, sunlit orbit above blue planet"),
("10","Adaptive civic mobility pavilion","18-meter next-generation autonomous civilian urban transit machine, airy flowing ceramic composite load-bearing arch structure, transparent passenger compartment with human-size doors, magnetically coordinated modular wheel-free support system rendered as speculative, vibrant green sustainable future city")
]
PREFIX=("Ultra photorealistic documentary industrial product photograph of advanced HUMAN and AI co-engineered NONMILITARY civilian technology after centuries of scientific collaboration. "
        "Single coherent complete original machine, full subject in frame, clear real-world scale cues, uniquely purposeful silhouette, mature manufacturable tolerances, "
        "precise visible panel joints, embedded hex fasteners, authentic cable routes, actuators and sensor mechanisms, differentiated anodized aluminum and ceramic-matrix composites, "
        "subtle mission-appropriate weathering, surface wear and dirt in functional seams, physically accurate specular highlights and believable contact shadows. "
        "Shot on medium-format digital camera, 50mm lens at f/8, natural restrained cinematic color science, sharp clear microtexture, realistic scale and perspective, no stylistic illustration. ")
NEG=("military, weapon, tank, turret, armored personnel carrier, camouflage, rifle, fighter jet, army truck, gun, combat, tactical decals, "
     "cartoon, painting, matte concept art, sci-fi illustration, digital painting, clay, model kit, miniature toy, blurry, melted parts, extra limbs, "
     "deformed mechanical geometry, generic rover, random greebles, impossible perspective, logos, captions, watermark, text, letters, hazy glow")
def sha(data):return hashlib.sha256(data).hexdigest()
def persist(j):
 t=JOURNAL.with_suffix(".pending");t.write_text(json.dumps(j,indent=2));t.replace(JOURNAL)
def request(path,payload=None,binary=False):
 body=json.dumps(payload).encode() if payload is not None else None
 req=urllib.request.Request(BASE+path,data=body,headers={"Content-Type":"application/json"},method="POST" if body is not None else "GET")
 with urllib.request.urlopen(req,timeout=180) as r:return r.read() if binary else json.load(r)
def graph(n,concept):
 prompt=PREFIX+concept+". Finished functional intelligent machine, no weapons."
 return {
 "1":{"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":MODEL}},
 "2":{"class_type":"CLIPTextEncode","inputs":{"text":prompt,"clip":["1",1]}},
 "3":{"class_type":"CLIPTextEncode","inputs":{"text":NEG,"clip":["1",1]}},
 "4":{"class_type":"VAELoader","inputs":{"vae_name":VAE}},
 "5":{"class_type":"EmptyLatentImage","inputs":{"width":768,"height":512,"batch_size":1}},
 "6":{"class_type":"KSampler","inputs":{"seed":2026111700+int(n)*163,"steps":32,"cfg":6.5,"sampler_name":"dpmpp_2m","scheduler":"karras","denoise":1,
     "model":["1",0],"positive":["2",0],"negative":["3",0],"latent_image":["5",0]}},
 "7":{"class_type":"VAEDecode","inputs":{"samples":["6",0],"vae":["4",0]}},
 "8":{"class_type":"UpscaleModelLoader","inputs":{"model_name":UPSCALER}},
 "9":{"class_type":"ImageUpscaleWithModel","inputs":{"upscale_model":["8",0],"image":["7",0]}},
 "10":{"class_type":"ImageScale","inputs":{"image":["9",0],"upscale_method":"lanczos","width":1920,"height":1080,"crop":"center"}},
 "11":{"class_type":"SaveImage","inputs":{"filename_prefix":"FWAI_V5_AI_CIVILIZATION_"+n,"images":["10",0]}}}
def process(n,title,concept,journal):
 row=journal.setdefault(n,{"title":title,"prompt":PREFIX+concept,"seed":2026111700+int(n)*163,"state":"planned","model":MODEL})
 target=ROOT/("FUT_"+n+"_1920x1080.png")
 if row["state"]=="complete":
  if not target.is_file() or sha(target.read_bytes())!=row.get("sha256"):raise RuntimeError("Completed asset checksum mismatch "+n)
  print(n,"previous verified",flush=True);return
 if row["state"]=="planned":
  row["state"]="submitting";persist(journal)
  receipt=request("/prompt",{"prompt":graph(n,concept),"client_id":"FWAI_P04_V5_10_DESIGNS"})["prompt_id"]
  uuid.UUID(receipt);row["receipt"]=receipt;row["state"]="submitted";persist(journal)
  print(n,"submitted",receipt,flush=True)
 if row["state"]!="submitted":raise RuntimeError("Submission state ambiguous, manual reconciliation required "+n)
 for _ in range(350):
  response=request("/history/"+row["receipt"]).get(row["receipt"])
  if response:
   if response.get("status",{}).get("status_str")=="error":raise RuntimeError("Comfy reported rendering error "+n)
   images=response.get("outputs",{}).get("11",{}).get("images",[])
   if len(images)==1:
    f=images[0]
    qs=urllib.parse.urlencode({"filename":f["filename"],"subfolder":f["subfolder"],"type":"output"})
    raw=request("/view?"+qs,binary=True)
    part=target.with_suffix(".pending")
    part.write_bytes(raw)
    with Image.open(part) as im:
     if im.size!=(1920,1080):raise RuntimeError("Unexpected output dimension")
     im.verify()
    part.replace(target)
    row.update({"state":"complete","sha256":sha(raw),"bytes":len(raw),"dimensions":[1920,1080],"source":"ComfyUI actual GPU","review":"PENDING_OWNER","license_review":"PENDING_FINAL","external_upload_authorized":False})
    persist(journal)
    print(n,"COMPLETE 1920x1080",flush=True)
    return
  time.sleep(3)
 raise TimeoutError("Provider task not done; never blind re-submit "+n)
def montage(j):
 m=Image.new("RGB",(1800,770),(20,24,29));d=ImageDraw.Draw(m)
 for i,(n,title,_) in enumerate(DESIGNS):
  img=ROOT/("FUT_"+n+"_1920x1080.png")
  if not img.exists():continue
  with Image.open(img) as im:
   thumb=ImageOps.fit(im.convert("RGB"),(350,197),method=Image.Resampling.LANCZOS)
   x=i%5*360+5;y=i//5*375+5;m.paste(thumb,(x,y));d.text((x+5,y+201),n+" "+title[:31],fill="white")
 m.save(ROOT/"P04_V5_FUTURE_CIVILIZATION_1080P_CONTACT_SHEET.png")
if __name__=="__main__":
 for path,h in EXPECTED.items():
  if not path.is_file():raise RuntimeError("Missing pinned model "+path.name)
  with path.open("rb") as src:
   if hashlib.file_digest(src,"sha256").hexdigest()!=h:raise RuntimeError("Model SHA mismatch "+path.name)
 if not request("/system_stats").get("devices"):raise RuntimeError("GPU backend unavailable")
 j=json.loads(JOURNAL.read_text()) if JOURNAL.exists() else {}
 for row in DESIGNS:process(*row,j)
 montage(j)
 print("COMPLETE_COUNT",sum(v["state"]=="complete" for v in j.values()),flush=True)
