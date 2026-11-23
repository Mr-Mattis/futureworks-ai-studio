"""Create owner-friendly offline V5 review gallery and immutable SHA index.

This verifies technical delivery, NOT visual quality, rights, publication or
external upload approval. Nothing gets published or sent to a provider.
"""
from pathlib import Path
from PIL import Image
import hashlib,json,html
ROOT=Path.home()/"Documents"/"futureworks-p04-data"/"collection-v5-ai-civilization"
RECEIPTS=ROOT/"receipts.json"
journal=json.loads(RECEIPTS.read_text())
assert len(journal)==10,"Expected exactly ten design identities"
items=[]
for i in range(1,11):
    n=f"{i:02d}"
    item=journal[n]
    path=ROOT/f"FUT_{n}_1920x1080.png"
    assert item["state"]=="complete" and path.is_file(),f"Not ready: {n}"
    checksum=hashlib.sha256(path.read_bytes()).hexdigest()
    assert checksum==item["sha256"],f"SHA mismatch: {n}"
    with Image.open(path) as im:
        assert im.size==(1920,1080),f"Wrong image size: {n}"
        im.verify()
    items.append({"id":n,"design":item["title"],"filename":path.name,"sha256":checksum,"width":1920,"height":1080,"comfy_receipt":item["receipt"],"visual_review":"PENDING_OWNER","external_upload_authorized":False,"publish_authorized":False})
out=ROOT/"P04_V5_VERIFIED_ASSETS.json"
out.write_text(json.dumps({"phase":"P04","batch_id":"P04_V5_CIVILIAN_AI_001","asset_count":10,"model":"Realistic Vision V6.0 with RealESRGAN x4 super-resolution","assets":items,"owner_creative_approval":False,"external_upload_authorized":False,"publish_authorized":False},indent=2))
cards=[]
for a in items:
    label=html.escape(a["design"])
    filename=html.escape(a["filename"])
    n=a["id"]
    cards.append(f'''<article class="card"><h2>{n} — {label}</h2><a href="{filename}" target="_blank" title="Open full-resolution image"><img src="{filename}" loading="lazy" alt="{label}"></a>
    <p>1920 × 1080 · GPU generated · RealESRGAN</p><div class="radios">
    <label><input type="radio" name="v{n}" value="APPROVE"> Approve</label>
    <label><input type="radio" name="v{n}" value="REVISE"> Revise</label>
    <label><input type="radio" name="v{n}" value="HOLD" checked> Hold</label></div>
    <input class="note" id="note{n}" placeholder="Describe changes (scale, mechanics, materials, silhouette...)"></article>''')
site='''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Future Works AI Studio — V5 Creative Acceptance</title>
<style>body{background:#0c1421;color:#eaf4ff;font:16px/1.45 system-ui;margin:0}main{max-width:1500px;margin:auto;padding:24px}h1{margin-bottom:6px}
p{color:#adc5dc}.notice{background:#1b2c40;padding:16px;border-radius:10px;margin:20px 0;border:1px solid #335476}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,410px),1fr));gap:16px}.card{background:#1a2735;border:1px solid #314a63;border-radius:12px;padding:12px}
h2{font-size:18px;margin:0 0 10px}.card img{width:100%;aspect-ratio:16/9;object-fit:contain;border-radius:8px;background:black}
.card p{font-size:12px}.radios{display:flex;justify-content:space-between;gap:8px;margin:10px 0}.radios label{background:#293e52;padding:6px;border-radius:5px}
input.note,textarea{box-sizing:border-box;width:100%;border:1px solid #456178;background:#0c1522;color:white;padding:10px;border-radius:6px}textarea{min-height:190px}
button{padding:12px 16px;border:0;border-radius:7px;background:#55c7e5;color:#031827;font-weight:700;margin:10px 10px 10px 0;cursor:pointer}
</style></head><body><main><h1>Future Works AI Studio — P04 V5 Acceptance</h1>
<p>Ten fictional post-human/AI collaborative civilization designs · 1080p delivery · local only</p>
<div class="notice"><strong>Review the full images, not just thumbnails.</strong>
<p>Judge whether each design looks nonmilitary, plausibly engineered, genuinely futuristic, appropriately scaled, photorealistic, and mechanically credible.
Your choices stay on your PC until you copy them into our ChatGPT conversation. No provider uploads, purchases or publishing occur here.</p></div>
<div class="grid">'''+''.join(cards)+'''</div>
<div class="notice"><h2>One-message approval decision</h2><button onclick="build()">Generate review</button><button onclick="copy()">Copy decisions</button>
<textarea id="result" readonly></textarea><p id="feedback"></p></div></main>
<script>
function build(){const lines=['FWAI P04 V5 HUMAN VISUAL REVIEW','BATCH=P04_V5_CIVILIAN_AI_001'];for(let i=1;i<=10;i++){const n=String(i).padStart(2,'0');const choice=document.querySelector('input[name="v'+n+'"]:checked').value;const note=document.getElementById('note'+n).value.trim();lines.push('V5-'+n+'='+choice+(note?' | NOTE='+note:''))}lines.push('RUNWAY_UPLOAD=NOT_AUTHORIZED','PUBLISH=NOT_AUTHORIZED');document.getElementById('result').value=lines.join('\\n')}
async function copy(){build();try{await navigator.clipboard.writeText(document.getElementById('result').value);document.getElementById('feedback').textContent='Copied. Paste into ChatGPT to record the exact decisions.'}catch(e){document.getElementById('result').select();document.getElementById('feedback').textContent='Press Ctrl+C, then paste into ChatGPT.'}}
build();
</script></body></html>'''
(ROOT/"P04_V5_OFFLINE_VISUAL_APPROVAL.html").write_text(site,encoding="utf-8")
print("ALL_TEN_1080P_IMAGES_SHA256_VERIFIED")
print("Review:",ROOT/"P04_V5_OFFLINE_VISUAL_APPROVAL.html")
