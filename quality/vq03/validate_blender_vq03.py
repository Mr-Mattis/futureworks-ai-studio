"""Run inside Blender on the VQ03 saved scene. Technical, not cinematic, acceptance."""
import bpy,json,hashlib,sys,math
from pathlib import Path
out=Path(sys.argv[sys.argv.index("--")+1]) if "--" in sys.argv else Path.cwd()
scene=bpy.context.scene
rig=bpy.data.objects.get("FWAI-M001 / 6ft5in RIG / VQ03")
sheet=bpy.data.objects.get("VINYL / partially adhered flexible sheet")
door=bpy.data.objects.get("COLLISION / passenger door")
checks={}
checks["rig_present"]=bool(rig and rig.type=="ARMATURE")
checks["metric_scene"]=scene.unit_settings.system=="METRIC" and scene.unit_settings.scale_length==1.0
checks["mech_height_witness_1_9558m"]=bool(bpy.data.objects.get("METRIC / 1.9558m height witness"))
checks["kinematic_targets"]=sum(x.name.startswith("IK TARGET /") for x in bpy.data.objects)==4
checks["ik_constraints"]=sum(c.type=="IK" for pb in rig.pose.bones for c in pb.constraints)==4
checks["mechanical_bones"]=len(rig.data.bones)>=15
checks["leg_foot_keyframes"]=all(bpy.data.objects.get("IK TARGET / "+s+" FOOT").animation_data is not None for s in ("L","R"))
checks["vinyl_mesh_topology"]=bool(sheet and sheet.type=="MESH" and len(sheet.data.vertices)==435)
checks["vinyl_phase_shapes"]=bool(sheet.data.shape_keys and len(sheet.data.shape_keys.key_blocks)==3)
checks["cloth_modifier_available_not_baked"]=bool(any(m.type=="CLOTH" for m in sheet.modifiers))
checks["car_collision_proxy"]=bool(door and any(m.type=="COLLISION" for m in door.modifiers))
checks["vehicle_proxy_exists"]=bool(bpy.data.objects.get("NISSAN / door passenger"))
checks["camera_present"]=bool(scene.camera and scene.camera.data.type=="ORTHO")
# Rig root is lowered at frame36 while target feet don't move, proving a planted-foot crouch command.
pelvis_values={}
feet={}
for frame in (1,36,72):
    scene.frame_set(frame)
    pelvis_values[frame]=round(float(rig.pose.bones["pelvis"].location.z),4)
    feet[frame]={side:[round(float(v),5) for v in bpy.data.objects["IK TARGET / "+side+" FOOT"].location] for side in ("L","R")}
checks["actual_crouch_translation"]=pelvis_values[36]<pelvis_values[1] and pelvis_values[36]<pelvis_values[72]
checks["feet_targets_fixed"]=feet[1]==feet[36]==feet[72]
checks["rig_mesh_binding"]=sum(x.parent==rig and x.parent_type=="BONE" for x in bpy.data.objects)>15
manifest=json.loads((out/"VQ03_PROOF_MANIFEST.json").read_text())
checks["canonical_id_pinned"]=manifest["canonical_reference_sha256"]=="480263bdd7637bfb2d90cc2deecdeb616eef03492a35216dbebfd3b1f44c555c"
checks["height_m"]=abs(manifest["mech_height_m"]-1.9558)<1e-8
checks["three_render_receipts"]=len(manifest["render_files"])==3 and len({x["sha256"] for x in manifest["render_files"]})==3
checks["three_render_bytes_verified"]=all(hashlib.sha256((out/x["render"]).read_bytes()).hexdigest()==x["sha256"] for x in manifest["render_files"])
checks["save_blend_verified"]=hashlib.sha256((out/manifest["blend"]).read_bytes()).hexdigest()==manifest["blend_sha256"]
report={"schema":"FWAI_VQ03_TECHNICAL_ACCEPTANCE_V1","checks":checks,"passes":sum(checks.values()),
 "total":len(checks),"all_pass":all(checks.values()),"pelvis_z_by_frame":pelvis_values,"foot_targets_by_frame":feet,
 "owner_creative_approved":False,"physics_bake_complete":False,"real_vehicle_model_used":False}
(out/"VQ03_ACCEPTANCE.json").write_text(json.dumps(report,indent=2))
print("FWAI_VQ03_ACCEPTANCE",json.dumps({"passes":report["passes"],"total":report["total"],"all_pass":report["all_pass"]}))
if not report["all_pass"]:raise SystemExit("Technical checks failed")
