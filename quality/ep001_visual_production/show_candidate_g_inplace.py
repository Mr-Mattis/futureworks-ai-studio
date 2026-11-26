"""Load locally composed photographic S01 Candidate G in the existing Blender UI.

Never opens a new Blender window or rewrites a .blend. Zero assets deleted.
"""
import bpy,os,json,hashlib
from pathlib import Path
assert not bpy.app.background,"Persistent running GUI PID lock"
ROOT=Path.home()/"Documents"/"futureworks-ep001-production"
asset=ROOT/"reference"/"S01_WIDE_PHOTO_LOCKED_CORE_CANDIDATE_G.png"
receipt=json.loads((ROOT/"reference"/"S01_CANDIDATE_G_QA.json").read_text())
assert asset.is_file() and hashlib.sha256(asset.read_bytes()).hexdigest()==receipt["result_sha256"]
assert receipt["original_core_preserved_pixel_exact"]
screen=bpy.context.window.screen
viewer=max((a for a in screen.areas if a.type=="IMAGE_EDITOR"),key=lambda a:a.width*a.height)
img=bpy.data.images.load(str(asset),check_existing=True)
img.name="FWAI EP001 / G / 1280px PHOTO SAFE"
img.use_fake_user=True
viewer.spaces.active.image=img
viewer.tag_redraw()
if "ASSETS" in globals():
 ASSETS["G"]=asset
def export():
 return {"pid":os.getpid(),"window_count":len(bpy.context.window_manager.windows),
 "visible_reference":viewer.spaces.active.image.name,
 "photo1280":list(img.size),"source_core_exact":True,
 "source_blend_saved":False,"new_blender_gui_created":False,
 "creative_status":"S01 PHOTO FRAMING IMPROVED / TWO-HAND GRIP STILL HOLD"}
(ROOT/"evidence"/"EP001_INPLACE_G_SHOWCASE.json").write_text(json.dumps(export(),indent=2))
print("FWAI_EP001_G_SHOWN_IN_EXISTING_GUI",export())
