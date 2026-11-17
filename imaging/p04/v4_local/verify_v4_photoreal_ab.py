"""Offline V4 photoreal A/B output verifier. No paid network calls."""
import hashlib,json
from pathlib import Path
from PIL import Image
home=Path.home()
root=home/"Documents"/"futureworks-p04-data"/"collection-v4-photoreal-ab"
entries=json.loads((root/"receipts.json").read_text())
expected={
"V4_A_NATIVE":(768,512),"V4_A_ESRGAN_1080P":(1920,1080),
"V4_B_NATIVE":(768,512),"V4_B_ESRGAN_1080P":(1920,1080)}
items=[]
for key,size in expected.items():
  row=entries[key]
  file=root/(key+".png")
  if row["state"]!="complete" or not file.is_file():raise RuntimeError("Incomplete "+key)
  actual=hashlib.sha256(file.read_bytes()).hexdigest()
  if actual!=row["sha256"]:raise RuntimeError("Hash mismatch "+key)
  with Image.open(file) as im:
      if im.size!=size:raise RuntimeError("Size mismatch "+key)
      im.verify()
  items.append({"asset":key,"sha256":actual,"resolution":[*size],"immutable":True})
report={
 "phase":"P04","experiment":"V4_photoreal_mechanical_A_B",
 "models":{"base":"Realistic_Vision_V6.0_NV_B1_fp16.safetensors","base_sha256":"c48bfd159cd7a6507b128685e963c398fa72399cefafaf603781df50ce836cc7","base_license":"creativeml-openrail-m","vae_sha256":"735e4c3a447a3255760d7f86845f09f937809baa529c17370d83e4c3758f3c75","vae_license":"MIT","upscale_sha256":"37f9a931c215f040aa6d50f711f2cb115f713c46df1d0d6469a8bd7bfe9a60bb"},
 "A":"new text-to-image documentary photoreal rover details",
 "B":"img2img mechanical refinement of V3 rover using .5 denoise",
 "owner_visual_approval":"PENDING",
 "commercial_use_approval":"PENDING_FINAL_RIGHTS_CHECK",
 "paid_calls":0,"production_approved":False,"publish_authorized":False,"assets":items}
p=root/"P04_V4_PHOTOREAL_AB_VERIFICATION.json"
p.write_text(json.dumps(report,indent=2))
print("V4_FOUR_LOCAL_ASSET_SHA_DIMENSION_VERIFICATIONS_PASS")
print(p)
