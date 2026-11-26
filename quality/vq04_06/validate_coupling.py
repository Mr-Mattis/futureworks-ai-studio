"""VQ04.06 all-frame hand-to-cloth kinematic coupling verification.

A passed test means constrained film corner follows the robot R index pad with a
stable offset. Does NOT establish physically exerted fingertip force or true grip.
"""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
root=Path.home()/"Documents"/"futureworks-vq04-06"
out=root/"evidence";out.mkdir(exist_ok=True,parents=True)
sc=bpy.context.scene
film=bpy.data.objects["FWAI VQ04.06 / HAND-COUPLED FILM"]
tip=bpy.data.objects["FWAI GRIP / R_index_fingerpad"]
ctrl=bpy.data.objects["FWAI VQ04.06 / FOLLOW R INDEX TIP DRIVER"]
mech=bpy.data.objects["FWAI-M001 / 6ft5in RIG / VQ03"]
door=bpy.data.objects["NISSAN / door passenger"]
old_target=bpy.data.objects["IK TARGET / R HAND"]
proxy=bpy.data.objects["FWAI VQ04.06 / R-hand IK fitted target"]
cloth=next(m for m in film.modifiers if m.type=="CLOTH")
assert cloth.point_cache.is_baked
latest=Path.home()/"Documents"/"futureworks-p04-comfyui"/"output"/"FWAI_M001_LOCKED_V2_CHARACTER_KEYFRAME_00002_.png"
latest_sha="5dcefd9309510754d7b5dd5dd549eae6f3244d1a4a3b6f9056c2055d620ba12b"
assert hashlib.sha256(latest.read_bytes()).hexdigest()==latest_sha
assert film["FWAI_LATEST_OWNER_MASTER_SHA"]==latest_sha
assert ctrl.parent==tip
assert proxy.parent==old_target
assert film.data.shape_keys is None
assert [m.type for m in film.modifiers]==["HOOK","CLOTH","SOLIDIFY"]
assert film["FWAI_FORCE_CONTACT_CERTIFIED"] is False
rows=[]
initial_offset=None
for frame in range(1,73):
 sc.frame_set(frame)
 dg=bpy.context.evaluated_depsgraph_get()
 f=film.evaluated_get(dg)
 p=tip.evaluated_get(dg)
 v=f.matrix_world@f.data.vertices[16*25].co
 pad=p.matrix_world.translation.copy()
 diff=pad-v
 if initial_offset is None:initial_offset=diff
 residual=(diff-initial_offset).length
 allpoints=[f.matrix_world@x.co for x in f.data.vertices[:425]]
 within=[x for x in allpoints if -.47<=x.x<=.93 and .41<=x.z<=1.03]
 count=sum(x.y>-.3790001 for x in within)
 center=f.matrix_world@f.data.vertices[8*25+8].co
 rows.append({"frame":frame,"fingertip_xyz_m":[round(x,6) for x in pad],
     "film_gripped_corner_xyz_m":[round(x,6) for x in v],
     "finger_to_corner_offset_xyz_m":[round(x,6) for x in diff],
     "offset_residual_m":round(residual,6),
     "distance_from_pad_to_corner_m":round(diff.length,6),
     "door_surface_intrusions":count,
     "simulated_center_xyz":[round(x,6) for x in center]})
cache_dir=root/"scene"/"blendcache_FWAI_VQ04_06_COUPLED_CLOTH_BAKED_V2"
summary={
 "schema":"FWAI_VQ04_06_ALLFRAME_COUPLED_DIAGNOSTICS_V1",
 "frames":len(rows),"distinct_sheet_center_positions":len({tuple(r["simulated_center_xyz"]) for r in rows}),
 "max_offset_residual_m":max(r["offset_residual_m"] for r in rows),
 "max_corner_distance_m":max(r["distance_from_pad_to_corner_m"] for r in rows),
 "initial_fingertip_corner_offset":[round(x,6) for x in initial_offset],
 "max_door_surface_intrusions":max(r["door_surface_intrusions"] for r in rows),
 "cache_baked":cloth.point_cache.is_baked,
 "cache_file_count":len(list(cache_dir.glob("*"))),
 "controller_parent":ctrl.parent.name,"ik_proxy_parent":proxy.parent.name,
 "original_visual_sha_verified":True,
 "full_hand_film_collision_checked":False,
 "pressure_or_pinch_force_verified":False,
 "manufacturing_vinyl_material_properties_verified":False,
 "photoreal_quality_approved":False,
 "samples":{str(f):rows[f-1] for f in (1,18,36,54,72)}
}
(out/"VQ04_06_FRAME_TRACE.json").write_text(json.dumps(rows,indent=2))
(out/"VQ04_06_COUPLING_DIAGNOSTICS.json").write_text(json.dumps(summary,indent=2))
print("FWAI_VQ06_ALLFRAME_COUPLING",json.dumps(summary))
