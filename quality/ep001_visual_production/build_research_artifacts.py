"""Future Works EP001: primary-source reference board + 7% composition audit.
Local artifacts only. Does not modify owner's approved photos or the Blender scene.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,html
root=Path.home()/"Documents"/"futureworks-ep001-production"
ref=root/"reference";ref.mkdir(parents=True,exist_ok=True)
pre=Path.home()/"Documents"/"futureworks-p04-data"/"FWAI-M001_EP001_PREPRODUCTION"
manifest=json.loads((pre/"03_RUNWAY_PROMPTS"/"PRODUCTION_MANIFEST.json").read_text())
img=pre/"05_LOCAL_KEYFRAMES"/"S01"/"candidate_F_leg_grip_repair"/"FWAI_EP001_S01_MASKED_POSE_COMPOSITE_E.png"
approved=Path(manifest["owner_master_visual_asset_on_El_Corredor"])
car=pre/manifest["car_primary_reference"]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(approved)==manifest["owner_latest_mech_master_sha256"]
frame=Image.open(img).convert("RGB")
W,H=frame.size
assert W/H>1.7 and W/H<1.8
# Photo pixels are unaltered; both reviews are clearly labelled studies.
overlay=frame.copy()
draw=ImageDraw.Draw(overlay,"RGBA")
safe=.07
sx=int(W*safe);sy=int(H*safe)
draw.rectangle((sx,sy,W-sx,H-sy),outline=(40,233,238,255),width=3)
draw.line([(W//2,sy),(W//2,H-sy)],fill=(60,220,238,80),width=2)
draw.line([(sx,H//2),(W-sx,H//2)],fill=(60,220,238,80),width=2)
draw.rectangle((0,0,W,38),fill=(5,16,27,225))
draw.text((14,11),"S01 FRAMING AUDIT | 7% picture-safe zone | NOT FINAL",fill=(236,244,253,255))
draw.rectangle((0,H-32,W,H),fill=(5,16,27,235))
draw.text((15,H-24),"ISSUE: front/rear safe margin + second hand grip. Keep locked workshop/photo plate.",fill=(255,206,125,255))
overlay_path=ref/"S01_PHOTO_SAFE_FRAMING_AUDIT.png"
overlay.save(overlay_path)
# Spatial framing only: an intentionally nonproduction border proves what camera coverage needs.
safefit=Image.new("RGB",(W,H),(25,31,38))
scale=.84
sm=frame.resize((round(W*scale),round(H*scale)),Image.Resampling.LANCZOS)
safefit.paste(sm,((W-sm.width)//2,(H-sm.height)//2))
df=ImageDraw.Draw(safefit)
df.rectangle((sx,sy,W-sx,H-sy),outline=(65,210,240),width=2)
df.rectangle((0,0,W,38),fill=(5,16,27))
df.text((15,12),"S01 COMPOSITION / 84% STUDY | BORDER REQUIRES TRUE OUTPAINT",fill=(244,244,244))
fit_path=ref/"S01_84_PERCENT_CAMERA_SAFETY_STUDY.png"
safefit.save(fit_path)
sources=[
 {"id":"CAR01","component":"Nissan 370Z NISMO body","title":"Nissan 2020 370Z NISMO press kit — factory geometry and trims","url":"https://usa.nissannews.com/en-US/releases/us-2020-nissan-370z-coupe-press-kit","kind":"factory specification","reference_use":"Full 170.5in body, 73.6in width, 19in forged wheels, vertical door handle, red NISMO sill/chin, pearl-white unchanged.","rights":"fact reference only; do not reproduce Nissan promotional photos without rights"},
 {"id":"CAR02","component":"Nissan photographic control","title":"Wikimedia 370Z Nismo photo by crash71100, CC0","url":"https://commons.wikimedia.org/wiki/File:Nissan_370Z_Nismo_(49014731402).jpg","kind":"photo (CC0)","reference_use":"Body silhouette and lens-reflection comparison; cross-check exact model year and angle.","rights":"CC0 according to Commons; original author crash71100"},
 {"id":"CAR03","component":"2015 NISMO side mesh acquisition","title":"Sketchfab — 2015 370Z Nismo Z34 by Ddiaz Design","url":"https://sketchfab.com/3d-models/2015-nissan-370z-nismo-z34-b66ac30ac64a4f1aa034fce37745abe3","kind":"possible 3D asset (license unresolved)","reference_use":"Evaluate photo-accurate body before any production import; verify commercial use and license manually.","rights":"NOT CLEARED for commercial use; do not download/publish yet"},
 {"id":"WRAP01","component":"Real car door wrap","title":"How to Wrap Your Car Door — installation demonstration","url":"https://www.youtube.com/watch?v=gh-axd6ibtA","kind":"real instructional video","reference_use":"Two-hand pull, adhesive progression, 45-degree squeegee path, controlled tension, trim along body line.","rights":"view/reference only, do not reuse footage"},
 {"id":"WRAP02","component":"Film installation mechanics","title":"Avery Dennison — Installation and How-To Videos","url":"https://graphics.averydennison.com/en/home/resources-and-learning/installation-how-to-videos.html","kind":"manufacturer video library","reference_use":"Learn glassing, shrinking, relief cuts, air release and clean recess finishing. Choose cast vinyl demonstration, not PPF-specific physics.","rights":"reference only, footage belongs to owner"},
 {"id":"WRAP03","component":"Dry wrap film","title":"3M — 2080 Vehicle Color Change application bulletin","url":"https://multimedia.3m.com/mws/media/2419562O/application-vehicle-color-change-ra-pdf.pdf","kind":"manufacturer installation bulletin","reference_use":"Controlled conforming with heat, felt squeegee, correct safe tool behavior. Do not interpolate arbitrary temperatures.","rights":"reference only, bulletin not bundled"},
 {"id":"WRAP04","component":"Heat forming and edge handling","title":"Avery Dennison Supreme Wrapping Film application instructions","url":"https://graphics.averydennison.com/content/dam/averydennison/graphics/ap/en/Instructional-Bulletins/ib-1.19-ap-application-instructions-for-avery-dennison-supreme-wrapping-film-rev-4-en.pdf","kind":"manufacturer instructions","reference_use":"Heat softening and set, hold/stretch release, edge/recess adhesion; temperature values depend on exact film.","rights":"reference only, not bundled"},
 {"id":"ROBOT01","component":"Whole-body weight shifting","title":"Boston Dynamics — Training a Humanoid Robot for Hard Work","url":"https://bostondynamics.com/blog/training-a-humanoid-robot-for-hard-work","kind":"primary robot motion analysis","reference_use":"Coordinate knee and hip flexion with torso/pelvis translation, foot planting and manipulator reach, avoid sliding and hinged-doll poses.","rights":"reference only, use our own FWAI-M001 geometry"},
 {"id":"ROBOT02","component":"Precision manipulation and grip","title":"Boston Dynamics — Atlas Gets a Grip","url":"https://bostondynamics.com/video/atlas-gets-a-grip/","kind":"real robot manipulation footage","reference_use":"Grip sequencing, coordinated hands, contact confirmation before transfer, staged release and recovery.","rights":"reference only, do not republish their footage"},
 {"id":"ROBOT03","component":"Dexterity and range","title":"Boston Dynamics — Large Behavior Models and Atlas Find New Footing","url":"https://bostondynamics.com/blog/large-behavior-models-atlas-find-new-footing/","kind":"robotics motion engineering","reference_use":"Reference trajectories, center of mass, contact constraints, low squat and articulated reach.","rights":"reference only"},
]
for s in sources:assert s["url"].startswith("https://")
shots=[
 {"id":"S01","seconds":"00–05","action":"Register at passenger door; true two-hand vinyl tension; knees/hips settle together; both bumpers 7% clear","camera":"stabilized 35–45mm equivalent 3/4 passenger, full car/mech, workshop locked","references":["CAR01","CAR02","WRAP01","ROBOT01"],"must_avoid":"front bumper crop, car body morph, mech off scale, fake grip"},
 {"id":"S02","seconds":"05–10","action":"Lift and lay film from upper tack: left hand tension, right hand positions free lower edge; wrinkle pattern obeys forces","camera":"shoulder-to-door medium, retain true door handle and rocker line","references":["WRAP01","WRAP02","ROBOT02"],"must_avoid":"film teleport, floating fingers, giant loose panel over wheel"},
 {"id":"S03","seconds":"10–15","action":"Forearm squeegee extends; one continuous center-to-edge stroke pushes adhesion front and small bubble wave","camera":"85mm-equivalent macro of tool contact, reflected workshop strip lights","references":["WRAP01","WRAP02","WRAP03"],"must_avoid":"squeegee passes through metal, instant global flattening"},
 {"id":"S04","seconds":"15–20","action":"Retract squeegee; deploy enclosed electric heat tool; free palm shapes film into actual handle recess","camera":"tight 85–105mm macro; single door geometry","references":["WRAP04","WRAP03","ROBOT02"],"must_avoid":"open flame, melting parts, whole-car heat glow"},
 {"id":"S05","seconds":"20–25","action":"Retract heat tool; safe knifeless-tape trim line; excess material peeled off continuously","camera":"macro locked 100mm equivalent with visible offcut path","references":["WRAP03","WRAP04"],"must_avoid":"blade cutting paint, disappearing waste"},
 {"id":"S06","seconds":"25–30","action":"Hands retreat; step clear and straighten posture; satin charcoal only on passenger door; finished all-car hero","camera":"45–50mm natural dolly-out with original front/rear clear and floor reflection consistent","references":["CAR01","ROBOT01"],"must_avoid":"widebody change before separate approval, swapped wheels, wrapped fenders"}
]
data={"schema":"FWAI_EP001_PRIMARY_SOURCE_REFERENCE_BIBLE_V1",
"owner_master_sha256":sha(approved),"primary_car_source_sha256":sha(car),
"photographic_candidate_f_sha256":sha(img),
"edition":"2026-11-23","authority":"User-approved exact mech and primary car photo outweigh external refs",
"source_media_reuse_policy":"Only use media with actual production rights; copyrighted internet videos are study links, not source footage to remix.",
"references":sources,"shots":shots,
"visual_rules":{"character_height_m":1.9558,"camera_safe_border_fraction":.07,
 "vehicle":"pearl-white 370Z NISMO with red chin/sill stripes and forged rims",
 "vehicle_static":True,"background_static":"one unchanged indoor wrap workshop",
 "material":"charcoal satin cast vinyl, adhered area smooth, free area tension folds",
 "motion":"weight shifts precede reaching; hinge joints, planted shoes, two opposed hands; material never spontaneously disappears",
 "post":"controlled 24fps, restrained optical motion, no hyperactive camera, no toon texture"},
"creative_review":"All local shots currently HOLD until visually reviewed",
"paid_runway_upload_authorized":False,"new_blender_gui_authorized":False}
(ref/"EP001_REAL_WORLD_REFERENCE_BIBLE.json").write_text(json.dumps(data,indent=2))
# Production visual reference page. Links, not unlicensed copies.
cards=[]
for s in sources:
 cards.append(f'<article class="card"><div class="small">{html.escape(s["id"])} · {html.escape(s["component"])}</div><h3><a target="_blank" rel="noopener noreferrer" href="{html.escape(s["url"])}">{html.escape(s["title"])}</a></h3><p>{html.escape(s["reference_use"])}</p><span>{html.escape(s["rights"])}</span></article>')
rows=[]
for sh in shots:
 refs=", ".join(sh["references"])
 rows.append(f'<tr><th>{sh["id"]}<small>{sh["seconds"]} sec</small></th><td><strong>{html.escape(sh["action"])}</strong><br>{html.escape(sh["camera"])}</td><td>{html.escape(refs)}</td><td>{html.escape(sh["must_avoid"])}</td></tr>')
htmlout='''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>FWAI EP001 | Practical Reference Director</title><style>
:root{color-scheme:dark}*{box-sizing:border-box}body{font:16px/1.55 Segoe UI,Arial,sans-serif;margin:0;background:#090f1b;color:#eef5ff}main{max-width:1440px;margin:0 auto;padding:34px}header p{max-width:900px;color:#c1d0e3}h1{font-size:clamp(2.5rem,5vw,4.9rem);line-height:1.04;letter-spacing:-.04em;margin:18px 0}h2{margin-top:40px;font-size:2rem}h3{margin:4px 0 12px;font-size:1.2rem}p{color:#bacce2}.small{font-weight:bold;font-size:.77rem;letter-spacing:.09em;color:#9ebedd}.callout{background:#223322;border-left:5px solid #83cdaa;padding:15px 20px}.warn{background:#3a271c;border-color:#fac07b}.columns{display:grid;grid-template-columns:1fr 1fr;gap:20px}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.card{background:#172338;border:1px solid #344d69;border-radius:13px;padding:17px}.card span{color:#b6a17f;font-size:.83rem}a{color:#9ce3ff}img{width:100%;height:auto;border-radius:10px;border:1px solid #405472}figure{margin:0}figcaption{color:#b8cce3;font-size:.87rem;padding:10px 0}table{width:100%;border-collapse:collapse}td,th{border-bottom:1px solid #33495d;text-align:left;vertical-align:top;padding:12px}th{color:#a0d7ef}th small{display:block;font-weight:normal}footer{margin:40px 0 0;color:#93a7bd;border-top:1px solid #345;padding-top:20px}@media(max-width:900px){.columns,.cards{grid-template-columns:1fr}main{padding:18px}}</style></head><body><main>
<header><div class="small">FUTURE WORKS AI STUDIO · EP001 · REAL-WORLD REFERENCE-LED FILM</div><h1>No more guessing.<br>One scene. Real craft.</h1>
<p>Project source of truth: exact owner-approved mech, pearl-white Nissan 370Z NISMO, same indoor workshop; 30 seconds, six 5-second physical actions. Original photos are untouched. Web images and videos are technical references, not footage we can simply reuse.</p></header>
<section class="callout"><strong>Priority:</strong> the approved owner character identity and current Nissan reference override all external examples. The expensive realistic 3D vehicle model is NOT purchased or downloaded. The exact car remains locked for this episode; widebody is a future separate variation.</section>
<h2>What we actually have — photographic S01 candidate</h2><div class="columns">
<figure><img src="S01_PHOTO_SAFE_FRAMING_AUDIT.png" alt="Candidate F photo with 7 percent safe frame lines"><figcaption>S01 camera safe zone over actual candidate F. Cyan boundary is the allowed critical-subject region. Bumpers approach edge; the left-hand vinyl grip remains wrong. Status: HOLD.</figcaption></figure>
<figure><img src="S01_84_PERCENT_CAMERA_SAFETY_STUDY.png" alt="Composition-only scaled photo with no actual outpaint"><figcaption>84% whole-photo scale demonstrates what physical margin is required. Dark border is a visualization ONLY, not a finished shot: must outpaint/fill the consistent workshop behind it.</figcaption></figure></div>
<h2>Reference anatomy: actual sources and intended production use</h2><div class="cards">'''+ "\n".join(cards)+'''</div>
<h2>Shot choreography mapped to real craft</h2><table><thead><tr><th>Shot</th><th>Physical action + lens</th><th>References</th><th>Failure to reject</th></tr></thead><tbody>'''+ "\n".join(rows)+'''</tbody></table>
<section class="callout warn"><strong>Release HOLD:</strong> the Blender cartoon-style mech/car remains an engineering/collision proxy; it cannot meet photorealism through better lighting alone. Do not fake approval from test results. We must promote licensed, accurate 370Z geometry or keep the real photographic vehicle plate; match the owner mech render, not the toy proxy.</section>
<footer>Research source URLs and per-shot rules are stored locally in EP001_REAL_WORLD_REFERENCE_BIBLE.json. Video links remain with their rights holders; do not upload user footage to Runway or purchase assets without separate authorization.</footer>
</main></body></html>'''
(ref/"EP001_DIRECTOR_REFERENCE_BOARD.html").write_text(htmlout,encoding="utf-8")
print("FWAI_REFERENCE_RESEARCH_DONE",len(sources),"sources",len(shots),"shots",W,H, "files",overlay_path,fit_path)
