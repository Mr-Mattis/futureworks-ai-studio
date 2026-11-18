"""FWAI P04.06 — verify local material renders and export isolated alpha cutouts.

Source geometry remains owner-approved and SHA-pinned. The cutout alpha mask
is projected from the deterministic geometry-bound source to avoid remaking
the machine. This is not an environment or a new material generation.
"""
import hashlib,json,os
from pathlib import Path
from PIL import Image,ImageOps,ImageFilter,ImageDraw
import numpy as np

ROOT=Path.home()/"Documents"/"futureworks-p04-data"/"p04-06-material-lookdev"
J=json.loads((ROOT/"gpu-receipts.json").read_text())
SOURCE=json.loads((ROOT/"MATERIAL_SOURCE_RECEIPT.json").read_text())
OWNER_APPROVED_G="7bc0379c02632018e78dfbea6eab467071ec0ffe9f97b3c9522c1634bf51b77e"
OWNER_APPROVED_M="07dc8ea721e2d2d69d47585bc67268c31a2ceb9d96e0724a5ffc55fd17465c5f"
assert SOURCE["approved_geometry_sha256"]==OWNER_APPROVED_G
assert SOURCE["approved_mechanical_sha256"]==OWNER_APPROVED_M
assert set(J)=={"graphite_alloy","ceramic_titanium"}
def sha(b):return hashlib.sha256(b).hexdigest()
entries=[]
for name in ("graphite_alloy","ceramic_titanium"):
 src=ROOT/f"FWAI-T001_MATERIAL_SOURCE_{name}_896x512.png"
 orig=next(x for x in SOURCE["source_assets"] if x["type"]==name)
 assert sha(src.read_bytes())==orig["sha256"]
 target=ROOT/f"FWAI-T001_MATERIAL_{name}_1920x1080.png"
 row=J[name]
 assert row["state"]=="complete" and sha(target.read_bytes())==row["output_sha256"]
 assert row["geometry_sha256"]==OWNER_APPROVED_G and row["mechanical_sha256"]==OWNER_APPROVED_M
 assert row["environment"] is None and row["external_upload"] is False and row["paid_calls"]==0
 with Image.open(src) as img:
  im=np.asarray(img.convert("RGB")).astype("int16")
  diff=np.max(abs(im-np.array([22,27,34],dtype="int16")),axis=2)
  matte=Image.fromarray(np.where(diff>12,255,0).astype("uint8"),mode="L")
  matte=ImageOps.fit(matte,(1920,1080),method=Image.Resampling.BICUBIC)
  matte=matte.filter(ImageFilter.GaussianBlur(.65))
 with Image.open(target) as render:
  assert render.size==(1920,1080)
  cutout=render.convert("RGBA")
  cutout.putalpha(matte)
  cutout_file=ROOT/f"FWAI-T001_MATERIAL_{name}_CUTOUT_1920x1080.png"
  cutout.save(cutout_file,optimize=True)
  rgb=render.convert("RGB")
  source_scaled=np.asarray(Image.open(src).convert("RGB").resize((1920,1080)),dtype="float32")
  pixel_delta=np.asarray(rgb,dtype="float32")-source_scaled
  rms=float(np.sqrt(np.mean(pixel_delta**2)))
 entries.append({"variant":name,"gpu_prompt_id":row["prompt_id"],
   "denoise":row["denoise"],"source_sha256":orig["sha256"],
   "render_file":target.name,"render_sha256":row["output_sha256"],
   "cutout_file":cutout_file.name,"cutout_sha256":sha(cutout_file.read_bytes()),
   "dimensions":[1920,1080],"alpha_foreground_fraction":round(float(np.mean(np.asarray(matte)>127)),4),
   "rms_source_pixel_difference":round(float(rms),2),
   "human_material_review":"PENDING","mechanical_geometry_similarity":"REQUIRES_VISUAL_REVIEW"})
report={"schema":"FWAI_P04_06_MATERIAL_A_B_RECEIPT_1",
        "design_id":"FWAI-T001","geometry_sha256":OWNER_APPROVED_G,
        "mechanical_sha256":OWNER_APPROVED_M,
        "method":"deterministic geometry-bound 2.5D material source -> local ComfyUI low-denoise img2img -> neural super-resolution -> local matte",
        "rendered_on":"El_Corredor local AMD Radeon GPU",
        "variant_count":len(entries),"assets":entries,
        "subject_stage":"MATERIAL_LOOKDEV",
        "environment_generation":False,"external_upload_authorized":False,
        "paid_provider_calls":0,"publishing_authorized":False,
        "owner_material_approval":"PENDING",
        "certified_physical_engineering":False,
        "quality_observation":"Technically coherent isolated top-view material previews. Photographic depth and tangible three-dimensional realism are not yet demonstrated; approval is not inferred."}
p=ROOT/"P04_06_MATERIAL_AB_VERIFIED_ASSETS.json"
p.write_text(json.dumps(report,indent=2),encoding="utf-8")

cards=[]
for a in entries:
 n=a["variant"]
 cards.append(f'''<article><h2>{n.replace("_"," ").title()}</h2>
 <a href="{a["render_file"]}" target="_blank"><img src="{a["render_file"]}" alt="1080p material sample"></a>
 <p>Inspect full-size metal reflectance, panel seams, joint bearings, equipment scale and realistic depth.</p>
 <a href="{a["cutout_file"]}" target="_blank">View isolated transparent subject PNG</a><div class="choice">
 <label><input name="{n}" type="radio" value="APPROVE"> Approve</label>
 <label><input name="{n}" type="radio" value="REVISE"> Revise</label>
 <label><input name="{n}" type="radio" value="HOLD" checked> Hold</label></div>
 <input id="note-{n}" placeholder="What should be improved?"></article>''')
html='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>FWAI P04.06 Local Material Lookdev</title>
<style>body{background:#0d1721;color:#eef8ff;margin:0;font:16px/1.5 system-ui}main{max-width:1300px;margin:auto;padding:24px}
h1{margin-bottom:6px}p{color:#c0ceda}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,520px),1fr));gap:16px}
article,.notice{border:1px solid #36536a;border-radius:12px;padding:16px;background:#1a2a3b}
article img{width:100%;aspect-ratio:16/9;object-fit:contain;background:#0c1119}
a{color:#85e5ff}.choice{display:flex;gap:12px;justify-content:space-between;margin:12px 0}
input[type=text],input:not([type]),textarea{width:100%;box-sizing:border-box;background:#0b1420;color:#eef8ff;padding:11px;border:1px solid #4c7188;border-radius:7px}
textarea{min-height:145px}button{padding:11px 16px;border-radius:8px;border:0;background:#79deff;color:#071725;font-weight:750;cursor:pointer}
</style></head><body><main><h1>FWAI-T001 — Local Material Look Development</h1>
<p>Geometry and mechanical detail owner-approved. Isolated subject materials generated locally on your Radeon GPU; no environment, external upload, spending or publishing.</p>
<div class="notice"><strong>Human quality gate: still pending.</strong><p>The images are early top-view material previews, not physically validated hardware photographs. They may still read as illustrated product concept imagery rather than a truly real-life object. Please assess silhouette preservation and actual tangibility—not just detail or resolution.</p></div>
<div class="grid">'''+''.join(cards)+'''</div>
<div class="notice"><h2>Your Material Acceptance Decision</h2><button onclick="make()">Generate decision</button> <button onclick="copy()">Copy decision</button>
<textarea id="out" readonly></textarea><p id="status"></p></div></main><script>
function make(){let x=['FWAI P04.06 MATERIAL RENDER REVIEW','DESIGN=FWAI-T001',
'GEOMETRY=OWNER_APPROVED','MECHANICAL=OWNER_APPROVED'];
for(const n of ['graphite_alloy','ceramic_titanium']){
 const status=document.querySelector('input[name="'+n+'"]:checked').value;
 const note=document.getElementById('note-'+n).value.trim();
 x.push('P04.06-MATERIAL-'+n.toUpperCase()+'='+status+(note?' | NOTES='+note:''));}
x.push('ENVIRONMENT_RENDER=NOT_AUTHORIZED','EXTERNAL_UPLOAD=NOT_AUTHORIZED','PUBLISH=NOT_AUTHORIZED');
document.getElementById('out').value=x.join('\\n')}
async function copy(){make();try{await navigator.clipboard.writeText(document.getElementById('out').value);document.getElementById('status').textContent='Copied. Paste into ChatGPT.'}catch(e){document.getElementById('out').select();document.getElementById('status').textContent='Press Ctrl+C, then paste.'}}
make();</script></body></html>'''
(ROOT/"P04_06_MATERIAL_REVIEW.html").write_text(html,encoding="utf-8")
print("P04_06_TWO_GPU_RENDERS_AND_CUTOUTS_SHA256_VERIFIED")
print(ROOT/"P04_06_MATERIAL_REVIEW.html")
