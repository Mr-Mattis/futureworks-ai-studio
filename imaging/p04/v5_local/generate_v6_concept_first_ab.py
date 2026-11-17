"""V6 concept-first A/B: sci-fi geometry via SD1.5 -> low-denoise Realistic Vision -> ESRGAN.
Local GPU only. Two concepts; no paid calls or external uploads. Human QA required.
"""
import hashlib,json,time,urllib.request,urllib.parse,uuid
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
HOME=Path.home()
COMFY=HOME/"Documents"/"futureworks-p04-comfyui"
ROOT=HOME/"Documents"/"futureworks-p04-data"/"collection-v6-concept-first"
ROOT.mkdir(parents=True,exist_ok=True)
API="http://127.0.0.1:8188"
BASIC="v1-5-pruned-emaonly.safetensors"
REAL="Realistic_Vision_V6.0_NV_B1_fp16.safetensors"
VAE="vae-ft-mse-840000-ema-pruned.safetensors"
UPSCALE="RealESRGAN_x4plus.safetensors"
SHAS={
COMFY/"models"/"checkpoints"/BASIC:"6ce0161689b3853acaa03779ec93eafe75a02f4ced659bee03f50797806fa2fa",
COMFY/"models"/"checkpoints"/REAL:"c48bfd159cd7a6507b128685e963c398fa72399cefafaf603781df50ce836cc7",
COMFY/"models"/"vae"/VAE:"735e4c3a447a3255760d7f86845f09f937809baa529c17370d83e4c3758f3c75",
COMFY/"models"/"upscale_models"/UPSCALE:"37f9a931c215f040aa6d50f711f2cb115f713c46df1d0d6469a8bd7bfe9a60bb"}
DESIGNS=[
("01","ORBITAL LATTICE WEAVER",
 "A 40-meter futuristic orbital lattice weaving machine, huge hexagonal open truss, six precision fabrication arms and radiator wings, construction robotics on orbit around Earth, tiny two-meter service hatch for scale, elegant nonmilitary human-AI engineered shape, high detail sci-fi industrial machine concept, cinematic realistic hard surface 3D render",
 "Orbital lattice fabrication robot 40-meter hexagonal tension truss and articulated multi-axis construction arms, tiny human-size pressure maintenance hatch, precise machined titanium brackets, visible fasteners, thermal radiators, cable routing, minor scratches, realistic metal surface patina, film still, ultra photoreal industrial aerospace documentary"),
("02","SWARM CIVIC INFRASTRUCTURE DEPOT",
 "A seven-meter futuristic autonomous swarm robot depot, distinct towering hexagonal modular docking hive, hundreds of tiny repair robots connected to structural repair armatures, human-scale walkway and trees for scale, sunlit advanced eco city, novel nonmilitary human-AI engineered machinery, high detail sci-fi hard surface 3D render",
 "Real industrial photo of unique seven-meter branching hexagonal docking hive for small autonomous maintenance robots, visible charging bays, precise servo brackets and connector pins, textured ceramic metal alloys, weathered panel edges, realistic late-afternoon city lighting, nearby two-meter maintenance worker silhouette for scale, technologically advanced sustainable civic plaza")
]
NEG="human face, close up portrait, person alone, animal, fish, ordinary building, empty corridor, appliance, washing machine, military, tank, army, camouflage, fighter jet, gun, weapon, painting, illustration, CGI toy, deformed components, blurry, watermark, words"
J=ROOT/"receipts.json"
def sha(blob):return hashlib.sha256(blob).hexdigest()
def api(path,body=None,binary=False):
 data=json.dumps(body).encode() if body is not None else None
 req=urllib.request.Request(API+path,data=data,headers={"Content-Type":"application/json"},method="POST" if body is not None else "GET")
 with urllib.request.urlopen(req,timeout=180) as r:return r.read() if binary else json.load(r)
def save(j):
 t=J.with_suffix(".tmp");t.write_text(json.dumps(j,indent=2));t.replace(J)
def graph(n,concept,photo):
 seed=260117100+int(n)*1111
 return {
 "1":{"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":BASIC}},
 "2":{"class_type":"CLIPTextEncode","inputs":{"text":concept,"clip":["1",1]}},
 "3":{"class_type":"CLIPTextEncode","inputs":{"text":NEG,"clip":["1",1]}},
 "4":{"class_type":"EmptyLatentImage","inputs":{"width":768,"height":512,"batch_size":1}},
 "5":{"class_type":"KSampler","inputs":{"model":["1",0],"positive":["2",0],"negative":["3",0],"latent_image":["4",0],"seed":seed,"steps":30,"cfg":7,"sampler_name":"euler","scheduler":"normal","denoise":1}},
 "6":{"class_type":"VAEDecode","inputs":{"samples":["5",0],"vae":["1",2]}},
 "7":{"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":REAL}},
 "8":{"class_type":"VAELoader","inputs":{"vae_name":VAE}},
 "9":{"class_type":"CLIPTextEncode","inputs":{"text":photo,"clip":["7",1]}},
 "10":{"class_type":"CLIPTextEncode","inputs":{"text":NEG,"clip":["7",1]}},
 "11":{"class_type":"VAEEncode","inputs":{"pixels":["6",0],"vae":["8",0]}},
 "12":{"class_type":"KSampler","inputs":{"model":["7",0],"positive":["9",0],"negative":["10",0],"latent_image":["11",0],"seed":seed+5,"steps":24,"cfg":6.5,"sampler_name":"dpmpp_2m","scheduler":"karras","denoise":0.34}},
 "13":{"class_type":"VAEDecode","inputs":{"samples":["12",0],"vae":["8",0]}},
 "14":{"class_type":"UpscaleModelLoader","inputs":{"model_name":UPSCALE}},
 "15":{"class_type":"ImageUpscaleWithModel","inputs":{"upscale_model":["14",0],"image":["13",0]}},
 "16":{"class_type":"ImageScale","inputs":{"image":["15",0],"upscale_method":"lanczos","width":1920,"height":1080,"crop":"center"}},
 "17":{"class_type":"SaveImage","inputs":{"filename_prefix":"FWAI_V6_PHOTOREAL_"+n,"images":["16",0]}},
 "18":{"class_type":"SaveImage","inputs":{"filename_prefix":"FWAI_V6_CONCEPT_"+n,"images":["6",0]}}
 }
def save_image(img,target,size):
 q=urllib.parse.urlencode({"filename":img["filename"],"subfolder":img["subfolder"],"type":"output"})
 raw=api("/view?"+q,binary=True)
 temp=target.with_suffix(".part");temp.write_bytes(raw)
 with Image.open(temp) as im:
  if im.size!=size:raise RuntimeError("Unexpected image size")
  im.verify()
 temp.replace(target)
 return sha(raw)
def process(n,title,concept,photo,j):
 row=j.setdefault(n,{"title":title,"state":"planned","seed":260117100+int(n)*1111,"concept_prompt":concept,"photo_prompt":photo})
 final=ROOT/(f"V6_{n}_1920x1080.png")
 original=ROOT/(f"V6_{n}_CONCEPT_768x512.png")
 if row["state"]=="complete":
  if sha(final.read_bytes())!=row["sha256"] or sha(original.read_bytes())!=row["concept_sha256"]:raise RuntimeError("prior image changed")
  print(n,"previous verified",flush=True);return
 if row["state"]=="planned":
  row["state"]="submitting";save(j)
  receipt=api("/prompt",{"prompt":graph(n,concept,photo),"client_id":"FWAI_V6_A_B_CONCEPT_FIRST"})["prompt_id"]
  uuid.UUID(receipt);row["task_id"]=receipt;row["state"]="submitted";save(j)
  print(n,"submitted",flush=True)
 if row["state"]!="submitted":raise RuntimeError("ambiguous submission, do not retry")
 for _ in range(340):
  h=api("/history/"+row["task_id"]).get(row["task_id"])
  if h:
   if h.get("status",{}).get("status_str")=="error":raise RuntimeError("Comfy error "+n)
   a=h.get("outputs",{}).get("18",{}).get("images",[])
   b=h.get("outputs",{}).get("17",{}).get("images",[])
   if len(a)==1 and len(b)==1:
    concept_sha=save_image(a[0],original,(768,512))
    photo_sha=save_image(b[0],final,(1920,1080))
    row.update({"state":"complete","sha256":photo_sha,"concept_sha256":concept_sha,"review":"PENDING_OWNER","external_upload_authorized":False})
    save(j);print(n,"COMPLETE",flush=True);return
  time.sleep(3)
 raise TimeoutError("No blind retry")
if __name__=="__main__":
 for file,digest in SHAS.items():
  if not file.is_file():raise RuntimeError("Model missing "+file.name)
  with file.open("rb") as f:
   if hashlib.file_digest(f,"sha256").hexdigest()!=digest:raise RuntimeError("Model checksum invalid "+file.name)
 if not api("/system_stats").get("devices"):raise RuntimeError("Comfy offline")
 j=json.loads(J.read_text()) if J.exists() else {}
 for args in DESIGNS:process(*args,j)
 sheet=Image.new("RGB",(1440,900),(24,29,35));d=ImageDraw.Draw(sheet)
 for i,(n,title,_,_) in enumerate(DESIGNS):
  for k,suffix in enumerate(("CONCEPT_768x512","1920x1080")):
   with Image.open(ROOT/(f"V6_{n}_{suffix}.png")) as im:
    thumb=ImageOps.fit(im.convert("RGB"),(700,380),method=Image.Resampling.LANCZOS)
    x=k*720+10;y=i*440+10
    sheet.paste(thumb,(x,y));d.text((x+10,y+390),f"{n} / {title} / "+("CONCEPT" if k==0 else "PHOTOREAL 1080P"),fill="white")
 sheet.save(ROOT/"V6_CONCEPT_FIRST_AB_CONTACT_SHEET.png")
 print("TWO_CONCEPT_FIRST_VARIANTS_READY",flush=True)
