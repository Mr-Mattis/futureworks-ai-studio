"""Render controlled close-up evidence of VQ04.03 fingers and film; no save to .blend."""
import bpy,sys,json,hashlib
from pathlib import Path
from mathutils import Vector
HOME=Path.home()
ROOT=HOME/"Documents"/"futureworks-vq04-03"
OUT=ROOT/"evidence";OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(HOME/"Documents"/"futureworks-vq04"))
import fwai_hand_tool_preview as h
import fwai_grip_contact as contact
import fwai_geometry_preview as lower
sc=bpy.context.scene;sc.frame_set(36)
lower_id=lower.ASSET_ID
lower_file=lower.ROOT/(lower_id+".json")
lower.load({"type":"load_preview","asset_id":lower_id,"sha256":hashlib.sha256(lower_file.read_bytes()).hexdigest()})
h.load()
bpy.ops.object.camera_add(location=(-1.10,-2.17,1.21))
cam=bpy.context.object;cam.name="FWAI VQ04.03 / temporary hand close-up"
cam.data.type="ORTHO";cam.data.ortho_scale=.66
target=Vector((-1.06,-.72,1.135))
cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
sc.camera=cam
sc.render.resolution_x=1280;sc.render.resolution_y=720
sc.render.resolution_percentage=100
sc.render.image_settings.file_format="PNG"
outputs=[]
for frame,label in ((1,"OPEN"),(36,"REACH_CALIBRATED"),(72,"TOOL_DEPLOYED")):
    sc.frame_set(frame)
    if frame==36:
        cmsg=contact.calibrate()
    path=OUT/("VQ04_03_HAND_CLOSEUP_"+label+".png")
    sc.render.filepath=str(path)
    bpy.ops.render.render(write_still=True)
    outputs.append({"stage":label,"frame":frame,"image":path.name,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    if frame==36:contact.clear()
report={"schema":"FWAI_VQ04_03_CLOSEUP_V1","renders":outputs,"camera":"Temporary orthographic 0.66m close-up",
 "pixels":[1280,720],"source_blend_unchanged":True,"physical_vinyl_contact_approved":False}
(OUT/"VQ04_03_CLOSEUP_MANIFEST.json").write_text(json.dumps(report,indent=2))
print("FWAI_VQ04_03_CLOSEUP_COMPLETE",len(outputs))
