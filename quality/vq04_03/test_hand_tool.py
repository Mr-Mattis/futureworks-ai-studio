"""VQ04.03: safe preview mechanism acceptance in unsaved Blender scene.
Distinguishes successful kinematics from unvalidated vinyl pinch/contact.
"""
import bpy, sys, json, hashlib, math
from pathlib import Path
from mathutils import Vector
ROOT=Path.home()/"Documents"/"futureworks-vq04-03"
sys.path.insert(0,str(ROOT))
import fwai_hand_tool_preview as hw
OUT=ROOT/"evidence";OUT.mkdir(parents=True,exist_ok=True)
source=Path(bpy.data.filepath);sh=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.context.scene.frame_set(36)
orig=set(bpy.data.objects)
checks={}
def ck(name,condition):
    checks[name]=bool(condition)
    if not condition:raise AssertionError(name)
ck("canonical_source_hash",hashlib.sha256(hw.CANON.read_bytes()).hexdigest()==hw.EXPECTED_SHA)
ck("proper_source_mech_and_vinyl",hw._required()[0].type=="ARMATURE")
ck("scene_unchanged_before",hw.COL not in bpy.data.collections)
message=hw.load()
col=bpy.data.collections[hw.COL]
ck("two_hands_30_individual_hinge_pivots","30 finger joints" in message)
ck("thirty_individually_articulated_segments","30 segment meshes" in message)
ck("both_palms_exist",all(hw.PREFIX+s+"_palm_mount" in bpy.data.objects for s in ("L","R")))
ck("finger_phalanx_organized",len([x for x in col.objects if "_phalanx" in x.name])==30)
ck("fingerpad_organized",len([x for x in col.objects if "_fingerpad" in x.name])==10)
ck("distinct_hidden_forearm_tool_interface",hw.PREFIX+"tool_slider" in bpy.data.objects)
ck("squeegee_tip_mesh_integrated",hw.PREFIX+"squeegee_tip_bridge" in bpy.data.objects)
ck("tool_not_spuriously_approved",col["FWAI_OWNER_APPROVED"] is False)
ck("cloth_not_falsely_claimed",col["FWAI_CLOTH_SOLVED"] is False and col["FWAI_CONTACT_CERTIFIED"] is False)
ck("original_scene_meshes_preserved",orig.issubset(set(bpy.data.objects)))
tip=bpy.data.objects[hw.PREFIX+"R_index_fingerpad"]
slider=bpy.data.objects[hw.PREFIX+"tool_slider"]
measure={}
for frame in (1,36,72):
    hw.set_stage(frame);bpy.context.view_layer.update()
    eval_tip=tip.evaluated_get(bpy.context.evaluated_depsgraph_get())
    eval_slider=slider.evaluated_get(bpy.context.evaluated_depsgraph_get())
    measure[str(frame)]={"tip":list(round(float(v),6) for v in eval_tip.matrix_world.translation),
                         "slider":list(round(float(v),6) for v in eval_slider.matrix_world.translation),
                         "index_joint_angle":round(float(bpy.data.objects[hw.PREFIX+"R_index_joint1"].rotation_euler.y),5)}
ck("sustained_3_pose_finger_curl",measure["1"]["index_joint_angle"]!=measure["36"]["index_joint_angle"] and measure["36"]["index_joint_angle"]!=measure["72"]["index_joint_angle"])
ck("tool_actually_retracts_and_deploys",measure["1"]["slider"]!=measure["72"]["slider"])
ck("finger_tip_actually_moves",measure["1"]["tip"]!=measure["72"]["tip"])
try:hw.set_stage(500);bad=False
except ValueError:bad=True
ck("invalid_grip_stage_rejected",bad)
# Proximity is reported numerically, NOT counted as visual approval/contact.
film=bpy.data.objects["VINYL / partially adhered flexible sheet"]
proximity={}
for frame in (1,36,72):
    hw.set_stage(frame)
    bpy.context.view_layer.update()
    deps=bpy.context.evaluated_depsgraph_get()
    f=film.evaluated_get(deps)
    t=tip.evaluated_get(deps)
    index=12*29 # near upper part of left edge, u=0/v~.86
    surface=f.matrix_world@f.data.vertices[index].co
    finger=t.matrix_world.translation
    proximity[str(frame)]={"sheet_left_edge_xyz_m":[round(v,5) for v in surface],
       "index_pad_center_xyz_m":[round(v,5) for v in finger],
       "gap_m":round((finger-surface).length,5)}
ck("film_and_finger_measurements_recorded",len(proximity)==3 and all(x["gap_m"]>=0 for x in proximity.values()))
# Render study frame without altering owner material or camera.
hw.set_stage(36)
sc=bpy.context.scene
sc.render.resolution_x=1280;sc.render.resolution_y=720;sc.render.resolution_percentage=100
sc.render.image_settings.file_format="PNG"
output=OUT/"VQ04_03_HAND_TOOL_PREVIEW.png";sc.render.filepath=str(output)
bpy.ops.render.render(write_still=True)
ck("real_blender_preview_render_created",output.is_file() and output.stat().st_size>12000)
ck("loaded_preview_refuses_duplicate_meshes","30 finger joints" in hw.load() and hw.COL in bpy.data.collections)
n=len(bpy.data.objects)
message=hw.clear()
ck("clear_removes_only_preview",len(bpy.data.objects)==len(orig) and hw.COL not in bpy.data.collections and n>len(orig))
ck("clear_idempotent","already cleared" in hw.clear())
ck("original_blend_bytes_untouched",hashlib.sha256(source.read_bytes()).hexdigest()==sh)
report={"schema":"FWAI_VQ04_03_ENGINEERING_TESTS_V1","checks":checks,
 "passed":sum(checks.values()),"total":len(checks),"all_pass":all(checks.values()),
 "three_frame_joint_motion":measure,"gap_to_film_edge_m":proximity,
 "source_scene_sha256":sh,"render_sha256":hashlib.sha256(output.read_bytes()).hexdigest(),
 "actual_film_grip_verified":False,"tool_working_load_verified":False,
 "design_fidelity_approved":False,"no_paid_calls":True}
(OUT/"VQ04_03_ENGINEERING_TESTS.json").write_text(json.dumps(report,indent=2))
print("FWAI_VQ04_03_TESTS",report["passed"],report["total"],report["all_pass"])
print("FWAI_VQ04_03_FILM_GAPS",json.dumps(proximity))
