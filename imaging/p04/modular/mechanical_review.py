"""Offline reusable P04.06 mechanical detail acceptance page."""
from pathlib import Path
import json
import html
import sys

def create(root):
    root=Path(root)
    receipt=json.loads((root/"FWAI-T001_mechanical_detail_receipt.json").read_text())
    detail=json.loads((root/receipt["detail_file"]).read_text())
    if receipt["owner_mechanical_approval"]!="PENDING":
        raise ValueError("Mechanical acceptance is not pending")
    fields=[]
    for a in detail["arms"]:
        fields.append(f'''<article><h3>{html.escape(a['id'])} — {html.escape(a['truss_anchor_id'])}</h3>
          <p><strong>Link spans:</strong> {a['proximal_link_length_m']:.3f} m + {a['distal_link_length_m']:.3f} m</p>
          <p><strong>Drive:</strong> replaceable shoulder/elbow joints, fabrication tool</p>
          <p><strong>Power:</strong> isolated bus → shielded service loop → tool</p>
          <p><strong>Service:</strong> arm locked + power isolated before cartridge exchange</p></article>''')
    digest=receipt["detail_sha256"]
    page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>FWAI P04.06 Mechanical Detail Review</title><style>
body{margin:0;background:#0c1620;color:#eef7fb;font-family:system-ui,sans-serif;line-height:1.5}
main{max-width:1250px;margin:0 auto;padding:26px}h1{margin-bottom:4px}p{color:#b4cbd8}
.banner,article{background:#1a2a3a;border:1px solid #3a566d;border-radius:12px;padding:16px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:13px;margin:18px 0}
article h3{margin:0;font-size:1.06rem;color:#8de1ef}
label{display:block;margin:8px 0}input[type=text],textarea{background:#09131e;color:white;border:1px solid #567083;border-radius:6px;padding:10px;box-sizing:border-box;width:100%}
textarea{height:130px}button{border:0;border-radius:8px;background:#7ae0ff;color:#061824;padding:11px 15px;margin:10px 6px 10px 0;font-weight:700;cursor:pointer}
small{color:#d2b987}
</style></head><body><main><h1>P04.06 — Mechanical Detail Review</h1>
<p>FWAI-T001 · 40 m truss-ring diameter · six fabrication arms · 2 m airlock</p>
<section class="banner"><strong>TECHNOLOGY GEOMETRY: APPROVED.</strong>
<p>This review addresses conceptual joint locations, link sizes, power isolation, actuator interfaces, maintainability, and physical scale.</p>
<small>Engineering safety, load calculations, spacecraft dynamics, heat rejection, kinematic collision simulation and real manufacturing feasibility have NOT been validated. No imagery, material rendering, environment rendering or external uploads have been authorized.</small></section>
<section class="grid">'''+''.join(fields)+'''</section>
<section class="banner"><h2>Mechanical-detail acceptance</h2>
<label><input type="radio" name="choice" value="APPROVE"> Approve conceptual mechanical-detail specification</label>
<label><input type="radio" name="choice" value="REVISE"> Revise conceptual mechanical-detail specification</label>
<label><input type="radio" name="choice" value="HOLD" checked> Hold</label>
<label>Revision notes <input type="text" id="notes" placeholder="e.g. power cable should follow a protected internal raceway"></label>
<button onclick="build()">Generate decision</button><button onclick="copy()">Copy decision</button>
<textarea id="response" readonly></textarea><p id="feedback"></p></section></main>
<script>
function build(){const c=document.querySelector('input[name="choice"]:checked').value;
const n=document.getElementById('notes').value.trim();
document.getElementById('response').value=[
'FWAI P04.06 MECHANICAL DETAIL REVIEW',
'DESIGN=FWAI-T001',
'MECHANICAL_DETAIL_SHA256='''+digest+'''',
'P04.06-MECHANICAL='+c+(n?' | NOTES='+n:''),
'GEOMETRY=OWNER_APPROVED',
'PHYSICS_OR_FEASIBILITY=NOT_CERTIFIED',
'MATERIAL_RENDER=NOT_AUTHORIZED','ENVIRONMENT_RENDER=NOT_AUTHORIZED',
'EXTERNAL_UPLOAD=NOT_AUTHORIZED','PUBLISH=NOT_AUTHORIZED'
].join('\\n')}
async function copy(){build();try{await navigator.clipboard.writeText(document.getElementById('response').value);
document.getElementById('feedback').textContent='Copied; paste into ChatGPT.'}
catch(e){document.getElementById('response').select();document.getElementById('feedback').textContent='Press Ctrl+C to copy.'}}
build();
</script></body></html>'''
    target=root/"P04_06_MECHANICAL_DETAIL_REVIEW.html"
    target.write_text(page,encoding="utf-8")
    return target

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("Use: python3 mechanical_review.py FOLDER")
    print(create(sys.argv[1]))
