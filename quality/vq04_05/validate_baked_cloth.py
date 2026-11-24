"""Independent all-frame VQ04.05 cloth/door assessment, reopened baked .blend.

Data is evaluated from BLENDER CLOTH modifier and disk cache, not authored shape keys.
Acceptance is deliberately evidence-based; report violations rather than hiding them.
"""
import bpy, sys, json, hashlib, math, os
from pathlib import Path
from mathutils import Vector
root=Path.home()/"Documents"/"futureworks-vq04-05"
out=root/"evidence";out.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(Path.home()/"Documents"/"futureworks-vq04-04"))
import fwai_film_contact as prior
sc=bpy.context.scene
film=bpy.data.objects["FWAI VQ04.05 / SOLVER FILM"]
source=bpy.data.objects[prior.SOURCE]
door=bpy.data.objects["NISSAN / door passenger"]
cloth=next(m for m in film.modifiers if m.type=="CLOTH")
cache=cloth.point_cache
cache_folder=root/"scene"/"blendcache_FWAI_VQ04_05_CLOTH_BAKED"
files=list(cache_folder.glob("*"))
records=[]
errors=[]
samples={}
topology=len(film.data.vertices)
initial=[Vector(x) for x in prior.grid(1)]
for f in range(1,73):
    sc.frame_set(f)
    dg=bpy.context.evaluated_depsgraph_get()
    evalobj=film.evaluated_get(dg)
    evalverts=[evalobj.matrix_world@v.co for v in evalobj.data.vertices[:topology]]
    # Door proxy fronts from original baseline are same since original isn't touched.
    within=[v for v in evalverts if -.47<=v.x<=.93 and .41<=v.z<=1.03]
    penetrated=[v for v in within if v.y>prior.DOOR_FRONT_Y+.000001]
    door_gap=min((prior.DOOR_FRONT_Y-v.y for v in within),default=100)
    loose=[evalverts[j*prior.NX] for j in range(prior.NZ)]
    anchored=[evalverts[j*prior.NX+i] for j in range(prior.NZ) for i in range(16,prior.NX)]
    orig_anchor=[initial[j*prior.NX+i] for j in range(prior.NZ) for i in range(16,prior.NX)]
    anchor_delta=max((a-b).length for a,b in zip(anchored,orig_anchor))
    # Unpinned mechanical behavior: comparing mesh to vq04.04 shape keys is not
    # meaningful physically, so compare actual evaluated to source rest geometry.
    free_diff=sum((evalverts[j*prior.NX+i]-initial[j*prior.NX+i]).length for j in range(prior.NZ) for i in range(1,16))/(prior.NZ*15)
    center=evalverts[(prior.NZ//2)*prior.NX+8]
    gripper=bpy.data.objects["FWAI VQ04.05 / UNANIMATED SOURCE GRIP DRIVER"]
    gripper_location=gripper.matrix_world.translation.copy()
    rec={
      "frame":f,
      "simulated_center_xyz_m":[round(v,6) for v in center],
      "free_edge_center_xyz_m":[round(v,6) for v in loose[len(loose)//2]],
      "grip_control_xyz_m":[round(v,6) for v in gripper_location],
      "door_penetrating_surface_vertices":len(penetrated),
      "min_door_surface_gap_m":round(door_gap,6),
      "max_fixed_adhesion_drift_m":round(anchor_delta,6),
      "mean_free_region_displacement_from_frame1_rest_m":round(free_diff,6),
      "cloth_modifier_cached":cache.is_baked
    }
    records.append(rec)
    if f in (1,2,18,36,54,72):samples[str(f)]=rec
summary={
 "schema":"FWAI_VQ04_05_ALL_FRAME_DIAGNOSTIC_V1",
 "reopened_disk_cache_baked":bool(cache.is_baked),
 "cloth_modifier":cloth.name,"mesh_topology":topology,
 "keyframe_shapes":0 if film.data.shape_keys is None else len(film.data.shape_keys.key_blocks),
 "modifier_stack":[x.type for x in film.modifiers],
 "cache_files":len(files),"cache_bytes":sum(p.stat().st_size for p in files),
 "cache_path":str(cache_folder),
 "n_frames":len(records),
 "max_door_intersecting_vertices":max(x["door_penetrating_surface_vertices"] for x in records),
 "worst_adhesion_anchor_drift_m":max(x["max_fixed_adhesion_drift_m"] for x in records),
 "min_surface_door_gap_m":min(x["min_door_surface_gap_m"] for x in records),
 "dynamic_mean_free_delta_range_m":[min(x["mean_free_region_displacement_from_frame1_rest_m"] for x in records),
                                     max(x["mean_free_region_displacement_from_frame1_rest_m"] for x in records)],
 "center_position_distinct_all_frames":len({tuple(x["simulated_center_xyz_m"]) for x in records}),
 "samples":samples,
 "full_trace_filename":"VQ04_05_FRAME_TRACE.json",
 "validated_physical_adhesion":False,
 "verified_finger_film_gripping":False,
 "production_material_properties_calibrated":False,
 "cinematic_approval":False
}
(out/"VQ04_05_FRAME_TRACE.json").write_text(json.dumps(records,indent=2))
(out/"VQ04_05_SIMULATION_DIAGNOSTIC.json").write_text(json.dumps(summary,indent=2))
print("FWAI_VQ05_ANALYSIS",json.dumps(summary),flush=True)
