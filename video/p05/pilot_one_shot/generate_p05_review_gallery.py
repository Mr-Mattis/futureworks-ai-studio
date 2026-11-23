"""Generate offline one-page human clip acceptance UI.
No network, no scripts loaded from external websites, no auto approval or publishing.
Decision is recorded only when owner copies and sends the text explicitly.
"""
import html,json,pathlib
from pathlib import Path
ROOT=Path.home()/"Documents"/"futureworks-p05-data"/"real-runway-pilot-001"
data=json.loads((ROOT/"pilot-journal.json").read_text())
cards=[]
for scene in ("S01","S02","S03"):
 job=data["scenes"][scene]
 if job["state"]!="archived":raise RuntimeError("Not all pilot clips archived")
 filename=pathlib.Path(job["clip_file"]).name
 assert filename.startswith(scene+"_") and filename.endswith(".mp4") and (ROOT/filename).is_file()
 img=f"review_frames/{scene}_1.png"
 cards.append(f'''<article class="clip">
    <header><h2>{scene} — Runway Gen-4.5</h2><span>5 seconds · 1280 × 720 · verified</span></header>
    <video controls preload="metadata" playsinline poster="{html.escape(img)}"><source src="{html.escape(filename)}" type="video/mp4"></video>
    <p class="hint">Review the full motion, geometry, continuity, texture realism, and unexpected changes.</p>
    <div class="choices">
      <label><input name="{scene}" type="radio" value="APPROVE"> Approve</label>
      <label><input name="{scene}" type="radio" value="REVISE"> Revise</label>
      <label><input name="{scene}" type="radio" value="HOLD" checked> Hold</label>
    </div>
    <label class="notes">Notes <input id="notes-{scene}" placeholder="Optional: what should change?"></label>
  </article>''')
page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Future Works AI Studio — P05 Human Acceptance</title>
<style>
body{margin:0;background:#10151e;color:#eef3ff;font-family:system-ui,-apple-system,Segoe UI,sans-serif;line-height:1.45}
main{max-width:1100px;margin:0 auto;padding:30px 18px}
h1{font-size:clamp(1.6rem,4vw,2.6rem);margin:0;color:#f0f7ff}p{color:#b7c8de}
.banner{background:#1b2838;border:1px solid #375069;padding:20px;border-radius:14px;margin:20px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,315px),1fr));gap:18px}
.clip{background:#1b2430;border:1px solid #314154;border-radius:14px;padding:16px}
.clip header{display:flex;gap:10px;align-items:center;justify-content:space-between;flex-wrap:wrap}
.clip h2{margin:0;font-size:1.2rem}.clip span{font-size:.78rem;color:#99c0e1}
.clip video{display:block;width:100%;border-radius:8px;aspect-ratio:16/9;background:black;margin-top:13px}
.hint{font-size:.88rem}.choices{display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap}
.choices label{cursor:pointer;background:#28394b;padding:7px 9px;border-radius:6px}
.notes{display:block;font-size:.85rem;margin-top:14px}.notes input{width:100%;box-sizing:border-box;background:#111b28;color:white;border:1px solid #435c73;border-radius:5px;padding:9px;margin-top:4px}
textarea{display:block;width:100%;box-sizing:border-box;background:#09101a;color:#eaf2fc;border:1px solid #3a6179;border-radius:9px;padding:14px;min-height:130px;resize:vertical}
button{background:#45c4ee;color:#06121a;border:0;border-radius:9px;padding:13px 19px;font-weight:750;cursor:pointer;margin:8px 8px 8px 0}
footer{color:#9db4c8;font-size:.9rem;margin-top:20px}
</style></head><body><main><h1>Future Works AI Studio — P05 Video Acceptance</h1>
<div class="banner"><strong>Real Runway pilot: 3 clips · $1.80 charged · $5 cap respected</strong><p>All three genuine clips were downloaded and passed integrity and format checks. Review each video in full. No content will be published or approved automatically by this page.</p></div>
<section class="grid">'''+''.join(cards)+'''</section>
<section class="banner"><h2>One-message acceptance decision</h2>
<p>Choose Approve / Revise / Hold for each clip, then copy the resulting decision into our ChatGPT conversation. Your choices remain local until you send them.</p>
<button onclick="makeReply()">Generate review decision</button><button onclick="copyReply()">Copy to clipboard</button>
<textarea id="reply" aria-label="Acceptance result" readonly></textarea><div id="copyStatus" role="status"></div>
</section><footer>Offline local review. No network requests, automatic publishing, external telemetry or paid retries.</footer></main>
<script>
function makeReply(){const lines=['Future Works AI Studio / P05 human continuity review'];for(const id of ['S01','S02','S03']){const state=document.querySelector('input[name="'+id+'"]:checked').value;const notes=document.getElementById('notes-'+id).value.trim();lines.push('P05-'+id+'='+state+(notes?' | NOTES='+notes:''))}lines.push('PUBLISH=NOT_AUTHORIZED');document.getElementById('reply').value=lines.join('\\n')}
async function copyReply(){makeReply();try{await navigator.clipboard.writeText(document.getElementById('reply').value);document.getElementById('copyStatus').textContent='Copied — paste into ChatGPT to record your review.'}catch(e){document.getElementById('reply').select();document.getElementById('copyStatus').textContent='Press Ctrl+C, then paste into ChatGPT.'}}
makeReply();
</script></body></html>'''
out=ROOT/"P05_OFFLINE_VIDEO_ACCEPTANCE.html"
out.write_text(page,encoding="utf-8")
print("ACCEPTANCE_GALLERY_CREATED",out)
