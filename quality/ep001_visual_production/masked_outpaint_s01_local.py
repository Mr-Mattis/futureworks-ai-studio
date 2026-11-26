"""True masked-border outpaint with local FLUX3 Klein, source photo preserved.

Uses actual ComfyUI ImagePadForOutpaint mask (unlike earlier reference-only edit).
No external upload, no new Blender GUI, and never modifies original source.
"""
from pathlib import Path
import json,urllib.request
home=Path.home()
pre=home/"Documents"/"futureworks-p04-data"/"FWAI-M001_EP001_PREPRODUCTION"
src=pre/"05_LOCAL_KEYFRAMES"/"S01"/"candidate_F_leg_grip_repair"/"FWAI_EP001_S01_MASKED_POSE_COMPOSITE_E.png"
inputdir=home/"Documents"/"futureworks-p04-comfyui"/"input"
name="FWAI_EP001_S01_PHOTO_SOURCE_EXACT.png"
dest=inputdir/name
import hashlib
if not dest.exists():dest.write_bytes(src.read_bytes())
assert hashlib.sha256(dest.read_bytes()).hexdigest()==hashlib.sha256(src.read_bytes()).hexdigest()
prompt=("<ref_image_0> Extend the exact same high-resolution photorealistic industrial indoor vehicle wrap workshop by 128 pixels to left and right and 72 pixels top and bottom. "
"Continue the existing workshop wall panels, tool carts, concrete floor plane and long overhead LED tube lights with naturally consistent real camera perspective and matching shadow direction. "
"Keep exactly the same pearl-white Nissan 370Z NISMO passenger side, factory black wheels, red NISMO chin and sill accents, and violet-cyan mechanical installer. "
"No extra robot, no extra car, no change to the 370Z bumper or proportions. Preserve the central reference image's objects exactly, generate ONLY new background outside its original rectangular borders. "
"Professional photographed automotive cinematography, 35mm lens, continuous seamless gray workshop room extending beyond the cropped photo edges, crisp physically plausible details in the added margins, not soft blurry streaks.")
graph={
"1":{"class_type":"UNETLoader","inputs":{"unet_name":"flux3-image-klein-int8-convrot.safetensors","weight_dtype":"default"}},
"2":{"class_type":"CLIPLoader","inputs":{"clip_name":"qwen3vl_4b_int8_convrot.safetensors","type":"flux3","device":"default"}},
"3":{"class_type":"VAELoader","inputs":{"vae_name":"flux2-vae.safetensors"}},
"11":{"class_type":"LoadImage","inputs":{"image":name}},
"12":{"class_type":"ImagePadForOutpaint","inputs":{"image":["11",0],"left":128,"top":72,"right":128,"bottom":72,"feathering":32}},
"13":{"class_type":"VAEEncodeForInpaint","inputs":{"pixels":["12",0],"vae":["3",0],"mask":["12",1],"grow_mask_by":8}},
"4":{"class_type":"CLIPTextEncode","inputs":{"clip":["2",0],"text":prompt}},
"32":{"class_type":"ConditioningZeroOut","inputs":{"conditioning":["4",0]}},
"17":{"class_type":"ReferenceMultiLatent","inputs":{"positive":["4",0],"negative":["32",0],"vae":["3",0],"resolution":"keep resolution","images.image0":["11",0]}},
"7":{"class_type":"KSampler","inputs":{"model":["1",0],"positive":["17",0],"negative":["17",1],"latent_image":["13",0],"seed":2388112312,"steps":16,"cfg":1.0,"sampler_name":"euler","scheduler":"simple","denoise":1.0}},
"8":{"class_type":"VAEDecode","inputs":{"samples":["7",0],"vae":["3",0]}},
"9":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"FWAI_EP001_S01_MASKED_BORDER_OUTPAINT"}}
}
q=json.load(urllib.request.urlopen("http://127.0.0.1:8188/queue",timeout=6))
assert not q.get("queue_running") and not q.get("queue_pending"),"Respect existing GPU jobs"
req=urllib.request.Request("http://127.0.0.1:8188/prompt",method="POST",data=json.dumps({"prompt":graph,"client_id":"FWAI_EP001_MASKED_LOCAL"}).encode(),headers={"Content-Type":"application/json"})
try:resp=json.load(urllib.request.urlopen(req,timeout=20))
except urllib.error.HTTPError as ex:
 print("MASKED_OUTPAINT_VALIDATION_ERROR",ex.read().decode()[:4000]);raise
print("MASKED_OUTPAINT_SUBMITTED",resp)
ref=home/"Documents"/"futureworks-ep001-production"/"reference"
(ref/"S01_MASKED_BORDER_PROMPT.json").write_text(json.dumps({"request_id":resp.get("prompt_id"),"source_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),"output_expected":[1280,720],"runway_calls":0,"owner_approved":False},indent=2))
