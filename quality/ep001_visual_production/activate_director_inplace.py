"""FWAI EP001 Director Cockpit inside Blender's EXISTING one persistent Blender session.

Uses current Scripting workspace. No Blender window created, no external assets
uploaded, no baked .blend overwritten, no speculative physical changes.
"""
import bpy,json,hashlib,os
from pathlib import Path
ROOT=Path.home()/"Documents"/"futureworks-ep001-production"
REF=ROOT/"reference"
E=ROOT/"evidence"
pre=Path.home()/"Documents"/"futureworks-p04-data"/"FWAI-M001_EP001_PREPRODUCTION"
book=json.loads((REF/"EP001_REAL_WORLD_REFERENCE_BIBLE.json").read_text())
manifest=json.loads((pre/"03_RUNWAY_PROMPTS"/"PRODUCTION_MANIFEST.json").read_text())
latest=Path(manifest["owner_master_visual_asset_on_El_Corredor"])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(latest)==book["owner_master_sha256"]==manifest["owner_latest_mech_master_sha256"]
assert bpy.app.background is False
assert not bpy.app.background,"Wrong Blender instance. Do not open a new GUI."
assert bpy.context.window and bpy.context.window.screen
assert bpy.context.scene.frame_end==72
# The creative reference is visible in a dedicated image editor, while the
# physics preview remains available in the same existing Blender viewport.
FILES={
 "QA":"S01_PHOTO_SAFE_FRAMING_AUDIT.png",
 "FIT":"S01_84_PERCENT_CAMERA_SAFETY_STUDY.png",
}
ASSETS={
 "QA":REF/FILES["QA"],
 "FIT":REF/FILES["FIT"],
 "S01":pre/"05_LOCAL_KEYFRAMES"/"S01"/"candidate_F_leg_grip_repair"/"FWAI_EP001_S01_MASKED_POSE_COMPOSITE_E.png",
 "MECH":latest,
 "CAR":pre/"02_CLEAN_CAR_REFERENCES"/"PRIMARY_NISMO_PASSENGER_3Q_500x293.png",
 "PROFILE":pre/"02_CLEAN_CAR_REFERENCES"/"SUPPORT_NISMO_PASSENGER_SIDE_PROFILE.png",
 "REAR":pre/"02_CLEAN_CAR_REFERENCES"/"SUPPORT_NISMO_REAR_3Q.png",
}
for k,p in ASSETS.items():
 if not p.is_file():raise RuntimeError("Missing pinned image "+k)
# Reuse existing Blender datablocks rather than duplicating data on rerun.
for k,path in ASSETS.items():
 name="FWAI EP001 / "+k
 image=bpy.data.images.get(name)
 if image is None:
    image=bpy.data.images.load(str(path),check_existing=True)
    image.name=name
 image.filepath=str(path)
 image.use_fake_user=True
# Large central Scripting area is intentionally a reference viewer.
screen=bpy.context.window.screen
view_areas=[a for a in screen.areas if a.type in {"IMAGE_EDITOR","TEXT_EDITOR"} and a.width>600]
if not view_areas:raise RuntimeError("Cannot find existing central editor; no window opened")
viewer=max(view_areas,key=lambda a:a.width*a.height)
viewer.type="IMAGE_EDITOR"
viewer.ui_type="IMAGE_EDITOR"
viewer.spaces.active.image=bpy.data.images["FWAI EP001 / QA"]
viewer.tag_redraw()
# Create reference and choreography as an internal text datablock too.
doc_name="FWAI EP001 / Production Directives"
doc=bpy.data.texts.get(doc_name) or bpy.data.texts.new(doc_name)
notes=[]
notes.append("FWAI-M001 EP001 — LOCKED PRODUCTION REFERENCE / 2026-11-23")
notes.append("LATEST MECH SHA256: "+book["owner_master_sha256"])
notes.append("PEARL-WHITE 370Z NISMO — REAL PHOTO BODY — DO NOT MORPH OR REPLACE")
notes.append("ONE STATIC WRAP WORKSHOP / 16:9 / 24fps / 30 seconds")
notes.append("PHOTO S01 candidate F is QA HOLD; cyan guide shows 7 percent safe margin.")
notes.append("VQ06 Blender mech and car geometry are physics/blockout ONLY, NOT final pixels.")
notes.append("Operator gestures: plant feet > shift hips/knees > reach > contact > film force > release.")
notes.append("Squeegee travels FROM center, not teleporting; adhesive front follows tool.")
for sh in book["shots"]:
 notes.append(sh["id"]+" / "+sh["seconds"]+"s / "+sh["action"])
 notes.append("CAMERA: "+sh["camera"])
 notes.append("AVOID: "+sh["must_avoid"])
notes.append("SOURCE LINKS")
for src in book["references"]:
 notes.append(src["id"]+"  "+src["title"]+"  "+src["url"])
textdata="\n".join(notes)+"\n"
if doc.as_string()!=textdata:
 doc.clear()
 doc.write(textdata)
doc.use_fake_user=True
# Director panel operators - they only change which existing image datablock
# is shown in the central editor; neither vehicle nor user images are altered.
def _show(key):
 if key not in ASSETS:raise ValueError("Unknown reference key")
 sc=bpy.context.window.screen
 ar=max((a for a in sc.areas if a.type in {"IMAGE_EDITOR","TEXT_EDITOR"} and a.width>600),
        key=lambda a:a.width*a.height)
 ar.type="IMAGE_EDITOR";ar.ui_type="IMAGE_EDITOR"
 ar.spaces.active.image=bpy.data.images["FWAI EP001 / "+key]
 ar.tag_redraw()
 return "Showing "+key+" — no asset mutation"

class FWAI_OT_ep001_view(bpy.types.Operator):
 bl_idname="fwai.ep001_view"
 bl_label="EP001 Show Source"
 refkey:bpy.props.StringProperty(default="QA")
 def execute(self,context):
  try:report=_show(self.refkey)
  except (ValueError,RuntimeError) as e:
   self.report({"WARNING"},str(e));return {"CANCELLED"}
  self.report({"INFO"},report)
  return {"FINISHED"}

class FWAI_PT_ep001_director(bpy.types.Panel):
 bl_idname="FWAI_PT_ep001_director"
 bl_label="EP001 / PHOTO-REAL DIRECTOR"
 bl_space_type="VIEW_3D"
 bl_region_type="UI"
 bl_category="Future Works"
 def draw(self,context):
  layout=self.layout
  col=layout.column(align=True)
  col.label(text="EXISTING GUI / NO NEW WINDOWS",icon="LOCKED")
  col.label(text="Mechanical 3D = blockout only")
  for a,b in (("QA","S01 | 7% Framing Audit"),("FIT","S01 | 84% Camera Study"),
              ("S01","S01 | Original Photo"),("MECH","FWAI-M001 | Approved"),
              ("CAR","370Z | Front 3/4"),("PROFILE","370Z | Passenger Profile"),
              ("REAR","370Z | Rear 3/4")):
   op=col.operator("fwai.ep001_view",text=b,icon="IMAGE_DATA")
   op.refkey=a
  col.separator()
  col.label(text="Vehicle/body remains unchanged",icon="CHECKMARK")
  col.label(text="Wrap industry refs in local HTML")
  col.label(text="EP001 cinematic quality: HOLD",icon="ERROR")

for klass in (FWAI_PT_ep001_director,FWAI_OT_ep001_view):
 if hasattr(bpy.types,klass.__name__):
  bpy.utils.unregister_class(getattr(bpy.types,klass.__name__))
for klass in (FWAI_OT_ep001_view,FWAI_PT_ep001_director):
 bpy.utils.register_class(klass)
bpy.context.scene["FWAI_EP001_LATEST_MASTER_SHA256"]=sha(latest)
bpy.context.scene["FWAI_EP001_CREATIVE_QA"]="HOLD"
bpy.context.scene["FWAI_EP001_REFERENCE_COUNT"]=len(book["references"])
bpy.context.scene["FWAI_EP001_ACTIVE_SINGLE_GUI_PID"]=os.getpid()
# No source scene save; this is an in-memory live cockpit.
result={"pid":os.getpid(),"window_count":len(bpy.context.window_manager.windows),
 "current_blend_source_preserved":bpy.data.filepath,
 "screen":screen.name,"central_editor":viewer.type,
 "reference_image":viewer.spaces.active.image.name,
 "approved_master_hash":sha(latest),
 "external_paid_calls":0,"new_blender_windows_spawned":0,
 "photo_reference_count":len(ASSETS),"research_urls":len(book["references"]),
 "registered_panel":hasattr(bpy.types,"FWAI_PT_ep001_director"),
 "creative_approved":False}
E.mkdir(exist_ok=True,parents=True)
(E/"EP001_LIVE_DIRECTOR_GUI_PROOF.json").write_text(json.dumps(result,indent=2))
print("FWAI_EP001_DIRECTOR_LIVE_INPLACE",result)
