"""Create VQ04.05 genuinely baked cloth stills, detail frames and video frames.

Reopens existing baked simulation. Does not rebake or change source .blend;
renders evaluated simulator geometry, not shape-key or image-generated impostors.
"""
import bpy, json, hashlib, math
from mathutils import Vector
from pathlib import Path
root=Path.home()/"Documents"/"futureworks-vq04-05"
out=root/"evidence";out.mkdir(exist_ok=True,parents=True)
frames=out/"frames";frames.mkdir(exist_ok=True)
sc=bpy.context.scene
cloth=bpy.data.objects["FWAI VQ04.05 / SOLVER FILM"]
mod=next(x for x in cloth.modifiers if x.type=="CLOTH")
assert mod.point_cache.is_baked, "Baked physical solver cache required"
sc.render.engine="BLENDER_EEVEE"
sc.render.image_settings.file_format="PNG"
sc.render.resolution_percentage=100
sc.render.film_transparent=False
orig_cam=sc.camera
receipts=[]
for frame in (1,36,72):
    sc.frame_set(frame)
    sc.render.resolution_x=1280;sc.render.resolution_y=720
    sc.render.filepath=str(out/("VQ04_05_BAKED_WIDE_%03d.png"%frame))
    bpy.ops.render.render(write_still=True)
    p=Path(sc.render.filepath)
    receipts.append({"camera":"original wide","frame":frame,"image":p.name,"bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
# Add temporary proof-only inspection camera; don't save to .blend.
bpy.ops.object.camera_add(location=(-0.66,-1.55,1.08))
cam=bpy.context.object
cam.name="FWAI / VQ04.05 inspect physical film (unsaved)"
target=Vector((-.58,-.55,.81))
cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
cam.data.type="ORTHO";cam.data.ortho_scale=1.25
sc.camera=cam
for frame in (1,36,72):
    sc.frame_set(frame)
    sc.render.resolution_x=1280;sc.render.resolution_y=720
    sc.render.filepath=str(out/("VQ04_05_BAKED_DETAIL_%03d.png"%frame))
    bpy.ops.render.render(write_still=True)
    p=Path(sc.render.filepath)
    receipts.append({"camera":"unsaved closeup","frame":frame,"image":p.name,"bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
# video preview: original camera (consistent locked stage), 72 actual cloth frames.
sc.camera=orig_cam
sc.render.resolution_x=960;sc.render.resolution_y=540
sc.render.filepath=str(frames/"F_")
sc.frame_start=1;sc.frame_end=72
bpy.ops.render.render(animation=True)
found=sorted(frames.glob("F_*.png"))
assert len(found)==72, "Missing real sim video frames: "+str(len(found))
summary={
  "schema":"FWAI_VQ04_05_RENDER_PROOF_V1",
  "source_blend_sha256":hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
  "cloth_cache_is_baked":mod.point_cache.is_baked,
  "evidence":receipts,
  "video_frame_count":len(found),
  "video_fps":24,
  "video_frames_sha256":[hashlib.sha256(p.read_bytes()).hexdigest() for p in found],
  "lens":"Blender Eevee, no ComfyUI/Runway calls",
  "visual_approval":False
}
(out/"VQ04_05_RENDER_PROOF.json").write_text(json.dumps(summary,indent=2))
print("FWAI_VQ05_RENDER_PASS",len(receipts),"stills",len(found),"video frames",flush=True)
