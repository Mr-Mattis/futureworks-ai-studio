"""Uncommitted image experiment: render-only smoothing AFTER baked cloth.

No Blender source/caches rewritten, and no claim of physical material calibration.
"""
import bpy,hashlib,json
from pathlib import Path
from mathutils import Vector
root=Path.home()/"Documents"/"futureworks-vq04-05"
out=root/"evidence"
sc=bpy.context.scene
obj=bpy.data.objects["FWAI VQ04.05 / SOLVER FILM"]
cloth=next(m for m in obj.modifiers if m.type=="CLOTH")
assert cloth.point_cache.is_baked
before=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()
for poly in obj.data.polygons:poly.use_smooth=True
smooth=obj.modifiers.new("FWAI 05 / TEMP render-only subdivision","SUBSURF")
smooth.subdivision_type="CATMULL_CLARK";smooth.levels=1;smooth.render_levels=2
# Move it between CLOTH and SOLIDIFY, preserving cloth-cache evaluation.
mods=obj.modifiers
i=next(n for n,m in enumerate(mods) if m==smooth)
j=next(n for n,m in enumerate(mods) if m.type=="SOLIDIFY")
mods.move(i,j)
assert [m.type for m in mods]==["HOOK","CLOTH","SUBSURF","SOLIDIFY"]
bpy.context.view_layer.update()
orig_cam=sc.camera
bpy.ops.object.camera_add(location=(-.66,-1.55,1.08))
cam=bpy.context.object
cam.name="FWAI / ephemeral smooth cloth inspection"
aim=Vector((-.58,-.55,.81))
cam.rotation_euler=(aim-cam.location).to_track_quat("-Z","Y").to_euler()
cam.data.type="ORTHO";cam.data.ortho_scale=1.25
sc.camera=cam
sc.render.engine="BLENDER_EEVEE"
sc.render.resolution_x=1280;sc.render.resolution_y=720
sc.render.resolution_percentage=100
sc.render.image_settings.file_format="PNG"
rows=[]
for frame in (1,36,72):
    sc.frame_set(frame)
    p=out/("VQ04_05_SMOOTH_DETAIL_%03d.png"%frame)
    sc.render.filepath=str(p)
    bpy.ops.render.render(write_still=True)
    rows.append({"frame":frame,"file":p.name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"bytes":p.stat().st_size})
# Real cached cloth, smoothed VISUALLY after dynamics, 72 physical frames.
movie_frames=out/"frames_smooth"
movie_frames.mkdir(exist_ok=True)
sc.render.resolution_x=960
sc.render.resolution_y=540
sc.render.filepath=str(movie_frames/"S_")
sc.frame_start=1
sc.frame_end=72
bpy.ops.render.render(animation=True)
assert len(list(movie_frames.glob("S_*.png")))==72,"Missing physically derived video frames"
assert hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()==before
(out/"VQ04_05_SMOOTH_RENDER.json").write_text(json.dumps({
"schema":"FWAI_VQ04_05_VISUAL_EXPERIMENT_V1","image_tests":rows,
"input_baked_cache":cloth.point_cache.is_baked,
"film_modifier_stack":[m.type for m in obj.modifiers],
"render_only":True,
"not_baked_new_physics":True,
"approved_by_owner":False,"original_sha256":before},indent=2))
print("FWAI_VQ05_SMOOTH_RENDER_PASS",len(rows))
