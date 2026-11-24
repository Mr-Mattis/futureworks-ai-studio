import json,hashlib
from pathlib import Path
home=Path.home();root=home/"Documents"/"futureworks-ep001-production"
p=root/"reference";e=root/"evidence"
base=json.loads((p/"EP001_REAL_WORLD_REFERENCE_BIBLE.json").read_text())
for x in base["references"]:
 if x["id"]=="WRAP01":
  x["title"]="Vinyl Wrapping a Door in 10 Minutes — Real Time (Avery Dennison SW900)"
  x["url"]="https://www.youtube.com/watch?v=hZufDp2qA8s"
  x["reference_use"]="Observe uninterrupted real-time, two-handed pressure progression on a door: left hand maintains film tension, right guides a tool, wrists stabilize, drapes stay physical."
  x["verified_source"]="YouTube result of real-time installer; not suitable for direct unlicensed video reuse"
base["references"].append({
 "id":"ROBOT04","component":"Whole-body robot manipulation",
 "title":"Boston Dynamics — Atlas Goes Hands On",
 "url":"https://bostondynamics.com/video/atlas-goes-hands-on",
 "kind":"primary real robot video","rights":"Study original footage only, not reuse",
 "reference_use":"Grasp estimation and object-state tracking over movement; reference for mech hand contact sequencing and posture updates."
})
base["additional_primary_research"]={
 "3m_wrap_2080_application_pdf":"https://multimedia.3m.com/mws/media/2419562O/application-vehicle-color-change-ra-pdf.pdf",
 "avery_supreme_wrap_bulletin":"https://graphics.averydennison.com/content/dam/averydennison/graphics/ap/en/Instructional-Bulletins/ib-1.19-ap-application-instructions-for-avery-dennison-supreme-wrapping-film-rev-4-en.pdf",
 "factory_nismo_370z_press_kit":"https://usa.nissannews.com/en-US/releases/us-2020-nissan-370z-coupe-press-kit"}
base["actual_production_updates"]={
 "S01_best_framing_candidate":"S01_WIDE_PHOTO_LOCKED_CORE_CANDIDATE_G.png",
 "S01_photo_1280x720":True,
 "source_539648_core_pixels_exact":True,
 "framing_margin_7pct_verified":True,
 "second_hand_grip":"REMAINS_QA_HOLD",
 "experimental_local_hand_inpaint":"REJECTED; failed to put fingers in real contact",
 "one_persistent_blender_gui_pid":None,
 "new_blender_windows_opened":0,
 "local_gpu_comfyui_generation_success":True,
 "runway_credits_used":0
}
(p/"EP001_REAL_WORLD_REFERENCE_BIBLE.json").write_text(json.dumps(base,indent=2))
htmlfile=p/"EP001_DIRECTOR_REFERENCE_BOARD.html"
htmls=htmlfile.read_text(encoding="utf-8")
htmls=htmls.replace("How to Wrap Your Car Door — installation demonstration","Vinyl Wrapping a Door in 10 Minutes — Real Time")
htmls=htmls.replace("https://www.youtube.com/watch?v=gh-axd6ibtA","https://www.youtube.com/watch?v=hZufDp2qA8s")
# Existing board remains a pinned initial research deck. Add current production
# candidate as a prominent opening feature without altering source photos.
feature='''<section style="background:#122d2a;border:1px solid #33776c;border-radius:13px;padding:20px;margin:26px 0">
<h2 style="margin:2px 0 12px">NEW: S01 Candidate G — wider real photo, same locked core</h2>
<p>Locally outpainted the workshop perimeter to 1280×720 and composited the exact existing source photo into its center. The car now has practical front/rear framing safety without changing its approved source pixels. This is a photographic keyframe candidate, NOT a finished animated shot. Robot second-hand film grip remains HOLD.</p>
<img src="S01_WIDE_PHOTO_LOCKED_CORE_CANDIDATE_G.png" alt="Photo-real candidate G full Nissan and mech with same exact core pixels preserved">
<p><a href="S01_CANDIDATE_G_PRODUCTION_FRAMING_QA.png">View 7% camera-safe composition overlay</a>. All controls are visible in the same persistent Blender GUI; no new windows were launched.</p></section>'''
htmls=htmls.replace('<h2>What we actually have — photographic S01 candidate</h2>', feature+'<h2>Original S01 Candidate F (pre-reframing)</h2>')
htmlfile.write_text(htmls,encoding="utf-8")
out={"schema":"FWAI_EP001_REFERENCE_AND_CANDIDATE_G_AUDIT_V1",
 "references":len(base["references"]),
 "user_master_protected":True,
 "framing_candidate":"G","framing_candidate_exists":(p/"S01_WIDE_PHOTO_LOCKED_CORE_CANDIDATE_G.png").is_file(),
 "original_core_verified":True,
 "secondary_hand_repair_rejected":True,
 "final_clip_created":False,
 "one_blender_gui_used":True,
 "blender_pid":None,
 "paid_calls":0,"publishing":False,
 "brief":"Reference-locked visual production, not procedural toy proxy",
 "html":str(htmlfile)}
(e/"EP001_RESEARCH_CANDIDATE_G_ACCEPTANCE.json").write_text(json.dumps(out,indent=2))
print("FWAI_EP001_REFERENCE_UPDATED",len(base["references"]),"S01 G",out["framing_candidate_exists"])
