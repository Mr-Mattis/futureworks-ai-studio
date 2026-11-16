"""P04 V2: ten distinct locally generated fictional AI designs.
Outputs outside git, never sends bytes to an external provider. 1080p output
is 1536x864 second diffusion pass then Lanczos resized to 1920x1080.
Journal records exact provider receipts; no blind resubmission.
"""
import hashlib,json,time,urllib.request,urllib.parse,uuid,sys
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
ROOT=Path(r"C:\Users\yashi\Documents\futureworks-p04-data\collection-v2")
ROOT.mkdir(parents=True,exist_ok=True)
JOURNAL=ROOT/"receipts.json"
API="http://127.0.0.1:8188"
MODEL="v1-5-pruned-emaonly.safetensors"
DESIGNS=[
("01","A sleek autonomous manta ray inspired orbital maintenance robot, broad swept wings, six precision microthrusters, dark graphite titanium and electric cyan energy veins, floating above an orbital hangar"),
("02","A six legged lunar excavation walker with excavator mantis forelimbs, modular drill shoulders, titanium segmented abdomen, blue optics and dust covered feet on a moon surface"),
("03","A humanoid deep sea salvage android with pressurized articulated armor, circular luminous blue chest viewport, algae free polished graphite plating, undersea station"),
("04","A compact four wheeled rover that unfolds into a towering origami-like research mecha, elegant symmetrical panels, cyan edge lights, Martian canyon"),
("05","A vertical ring-shaped antigravity drone with a suspended central sensor sphere and floating articulated manipulator arms, luminous cyan magnetic fields, high altitude sky dock"),
("06","A graceful long legged robotic crane bird with precision welding beak and folded solar sail wings, titanium graphite feathers, advanced shipyard at sunrise"),
("07","An eight armed asteroid mining spider robot with diamond geometry body, cyan laser mapping sensors and articulated drilling tools, asteroid cave"),
("08","A heavy quadruped arctic rescue robot with reinforced broad paws, heated cyan grille accents, oversized shoulder armor and deployable rescue sled, blizzard research base"),
("09","A miniature floating swarm queen robot with a hexagonal modular core and a halo of twelve coordinated micro-drones, glowing cyan optical lattices, clean futuristic robotics laboratory"),
("10","A futuristic autonomous orbital observatory robot shaped like a crescent arch with asymmetric telescope arms, graphite composite facets, cyan sensor arrays, starfield viewing platform")
]
NEG="text, letters, watermark, logo, trademark, existing franchise character, human celebrity, real brand, anatomy errors, extra limbs, blurry, lowres, noisy, repeated subjects"
def call(path,payload=None,binary=False):
    body=json.dumps(payload).encode() if payload is not None else None
    req=urllib.request.Request(API+path,data=body,headers={"Content-Type":"application/json"},method="POST" if body is not None else "GET")
    with urllib.request.urlopen(req,timeout=180) as r:return r.read() if binary else json.load(r)
def graph(n,description):
    prompt="Original fictional technology concept artwork, "+description+". Independent unique design, cinematic photorealistic 3D CGI concept illustration, meticulous physically based material rendering, volumetric lighting, ultra sharp precision details, cinematic wide frame, no labels, no typography. NOT a functioning engineering prototype."
    seed=880021000+int(n)*9173
    return {"1":{"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":MODEL}},
    "2":{"class_type":"CLIPTextEncode","inputs":{"text":prompt,"clip":["1",1]}},
    "3":{"class_type":"CLIPTextEncode","inputs":{"text":NEG,"clip":["1",1]}},
    "4":{"class_type":"EmptyLatentImage","inputs":{"width":1024,"height":576,"batch_size":1}},
    "5":{"class_type":"KSampler","inputs":{"seed":seed,"steps":28,"cfg":7,"sampler_name":"euler","scheduler":"normal","denoise":1,"model":["1",0],"positive":["2",0],"negative":["3",0],"latent_image":["4",0]}},
    "6":{"class_type":"LatentUpscale","inputs":{"samples":["5",0],"upscale_method":"nearest-exact","width":1536,"height":864,"crop":"disabled"}},
    "7":{"class_type":"KSampler","inputs":{"seed":seed+1,"steps":14,"cfg":6.5,"sampler_name":"euler","scheduler":"normal","denoise":0.30,"model":["1",0],"positive":["2",0],"negative":["3",0],"latent_image":["6",0]}},
    "8":{"class_type":"VAEDecode","inputs":{"samples":["7",0],"vae":["1",2]}},
    "9":{"class_type":"SaveImage","inputs":{"filename_prefix":"FWAI_P04_V2_"+n,"images":["8",0]}}}
def savej(j): 
    tmp=JOURNAL.with_suffix(".tmp")
    tmp.write_text(json.dumps(j,indent=2));tmp.replace(JOURNAL)
def process(n,description,j):
    rec=j.setdefault(n,{"design":description,"stage":"planned"})
    path=ROOT/("FWAI_V2_"+n+"_1920x1080.png")
    if rec.get("stage")=="complete":
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==rec.get("sha256"):
            print(n,"already verified",flush=True);return
        raise RuntimeError("completed asset mismatch "+n)
    if rec.get("stage")=="planned":
        rec["stage"]="submitting";savej(j)
        try: rid=call("/prompt",{"prompt":graph(n,description),"client_id":"FWAI_P04_V2"})["prompt_id"]
        except Exception: raise RuntimeError("Ambiguous submission, inspect history for "+n)
        uuid.UUID(rid);rec["receipt"]=rid;rec["stage"]="submitted";savej(j)
        print(n,"submitted",rid,flush=True)
    if rec["stage"]!="submitted":raise RuntimeError("Non-retryable state "+n+" "+rec["stage"])
    rid=rec["receipt"]
    for _ in range(400):
        result=call("/history/"+rid).get(rid)
        if result:
            if result.get("status",{}).get("status_str")=="error":raise RuntimeError("Comfy error "+n)
            images=result.get("outputs",{}).get("9",{}).get("images",[])
            if len(images)==1:
                f=images[0]
                url="/view?"+urllib.parse.urlencode({"filename":f["filename"],"subfolder":f["subfolder"],"type":"output"})
                raw=call(url,binary=True)
                original=ROOT/("FWAI_V2_"+n+"_1536x864.png")
                if not original.exists():original.write_bytes(raw)
                elif hashlib.sha256(original.read_bytes()).digest()!=hashlib.sha256(raw).digest():raise RuntimeError("source collision")
                with Image.open(original) as im:
                    if im.size!=(1536,864):raise RuntimeError("unexpected render size "+str(im.size))
                    hi=im.convert("RGB").resize((1920,1080),Image.Resampling.LANCZOS)
                    tmp=path.with_suffix(".tmp.png");hi.save(tmp,optimize=True);tmp.replace(path)
                rec.update({"stage":"complete","native_resolution":"1536x864","delivery_resolution":"1920x1080","upscale_method":"Lanczos (not native 1080p)","seed":880021000+int(n)*9173,"model":MODEL,"source_sha256":hashlib.sha256(raw).hexdigest(),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"filename":path.name})
                savej(j);print(n,"COMPLETED 1920x1080",flush=True);return
        time.sleep(3)
    raise TimeoutError("not resubmitting; check provider history "+n)
def montage():
    if not all(j.get(n,{}).get("stage")=="complete" for n,_ in DESIGNS):return
    sheet=Image.new("RGB",(1600,1000),(20,25,30));draw=ImageDraw.Draw(sheet)
    for i,(n,d) in enumerate(DESIGNS):
        with Image.open(ROOT/("FWAI_V2_"+n+"_1920x1080.png")) as im:
            tile=im.convert("RGB").resize((312,176),Image.Resampling.LANCZOS)
            x=(i%5)*320+4;y=(i//5)*500+10
            # rows are spaced for readable labels and imagery
            y=(i//5)*250+10
            sheet.paste(tile,(x,y));draw.text((x+4,y+180),n+" "+d[:32],fill="white")
    sheet.crop((0,0,1600,500)).save(ROOT/"P04_V2_CONTACT_SHEET.png")
if __name__=="__main__":
    if not call("/system_stats").get("devices"):raise RuntimeError("Comfy backend missing")
    j=json.loads(JOURNAL.read_text()) if JOURNAL.exists() else {}
    count=int(sys.argv[1]) if len(sys.argv)>1 else 10
    for n,d in DESIGNS[:count]:process(n,d,j)
    montage()
    print("DONE completed",sum(v.get("stage")=="complete" for v in j.values()),flush=True)
