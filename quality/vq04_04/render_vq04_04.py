"""Render VQ04.04 three partial-sheet stages and close-up two-sided grip study.

Temporary camera, all preview objects and shape keys ephemeral; source scene untouched.
"""
import bpy, sys, json, hashlib
from mathutils import Vector
from pathlib import Path
ROOT=Path.home()/"Documents"/"futureworks-vq04-04";OUT=ROOT/"evidence";OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(Path.home()/"Documents"/"futureworks-vq04-03"))
sys.path.insert(0,str(Path.home()/"Documents"/"futureworks-vq04-02"))
sys.path.insert(0,str(Path.home()/"Documents"/"futureworks-vq04"))
import fwai_film_contact as film
import fwai_film_grip as grip
import fwai_hand_tool_preview as hands
import fwai_geometry_preview as legs
import fwai_identity_preview as identity
src=Path(bpy.data.filepath);sha=hashlib.sha256(src.read_bytes()).hexdigest()
bpy.context.scene.frame_set(36)
manifest=legs.ROOT/(legs.ASSET_ID+".json")
legs.load({"type":"load_preview","asset_id":legs.ASSET_ID,"sha256":hashlib.sha256(manifest.read_bytes()).hexdigest()})
manifest=identity.ROOT/(identity.ID+".json")
identity.load({"type":"load_identity_preview","asset_id":identity.ID,"sha256":hashlib.sha256(manifest.read_bytes()).hexdigest()})
hands.load();film.load()
sc=bpy.context.scene
sc.render.resolution_x=1280
sc.render.resolution_y=720
sc.render.resolution_percentage=100
sc.render.image_settings.file_format="PNG"
images=[]
for frame,label in ((1,"HOLD"),(36,"REACH"),(72,"PARTIAL_APPLY")):
    bpy.context.scene.frame_set(frame)
    if frame==36:grip.calibrate()
    filename="VQ04_04_PARTIAL_SHEET_"+label+".png"
    dest=OUT/filename
    sc.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
    images.append({"file":filename,"frame":frame,"sha256":hashlib.sha256(dest.read_bytes()).hexdigest()})
    if frame==36:grip.clear()
# Camera just for detailed geometry study: angle exposes both tips/film edge.
bpy.context.scene.frame_set(36);grip.calibrate()
bpy.ops.object.camera_add(location=(-1.25,-1.23,1.19))
cam=bpy.context.object
cam.name="FWAI / VQ04.04 temporary two-sided grip detail camera"
cam.data.type="ORTHO"
cam.data.ortho_scale=.36
aim=Vector((-1.054,-.682,1.095))
cam.rotation_euler=(aim-cam.location).to_track_quat("-Z","Y").to_euler()
sc.camera=cam
pre_render_pair=grip._thumb_report()
pre_render_bvh=grip.diagnose(36)
out=OUT/"VQ04_04_GRIP_DETAIL.png"
sc.render.filepath=str(out);bpy.ops.render.render(write_still=True)
images.append({"file":out.name,"frame":36,"sha256":hashlib.sha256(out.read_bytes()).hexdigest()})
pair=pre_render_pair
bvh=pre_render_bvh
post_render_pair=grip._thumb_report()
rig=bpy.data.objects[hands.RIG]
targets=[(pb.name,c.target.name if c.target else None) for pb in rig.pose.bones for c in pb.constraints if c.type=="IK" and pb.name=="R_hand"]
print("VQ04_RENDER_TARGET_DEBUG",targets,"calibrated",grip._state["calibrated"],"proxy",grip._state["proxy"].name if grip._state["proxy"] else None,"proxy_position",list(grip._state["proxy"].location) if grip._state["proxy"] else None)
result={"schema":"FWAI_VQ04_04_RENDER_PROOF_V1","images":images,
        "verified_kinematic_pair_before_render":pair,"post_render_pair":post_render_pair,"bvh_pair_clearances":[r for r in bvh["pads"] if r["digit"] in ("R_thumb","R_index")],
        "camera_is_temporary":True,"scene_sha_unchanged":hashlib.sha256(src.read_bytes()).hexdigest()==sha,
        "adhesion_force_proven":False,"photorealism_approved":False}
(OUT/"VQ04_04_RENDER_MANIFEST.json").write_text(json.dumps(result,indent=2))
print("FWAI_VQ04_04_RENDERS",len(images),"pre_render_staging",pair["two_sided_geometry_pass"],"post_render_staging",post_render_pair["two_sided_geometry_pass"])
