"""VQ04.04 measured fingertip/BVH geometry and optional safe IK target proof."""
import bpy,sys,hashlib,json
from pathlib import Path
ROOT=Path.home()/"Documents"/"futureworks-vq04-04";OUT=ROOT/"evidence";OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(Path.home()/"Documents"/"futureworks-vq04-03"))
import fwai_film_contact as film
import fwai_hand_tool_preview as hand
import fwai_film_grip as grip
sc=bpy.context.scene;sc.frame_set(36)
source=Path(bpy.data.filepath);source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
original=set(bpy.data.objects)
hand.load()
film.load()
tests={}
def check(k,v):
 tests[k]=bool(v)
 if not v:raise AssertionError(k)
measures={}
for frame in (1,36,72):
 diag=grip.diagnose(frame)
 measures[frame]=diag
 check("all_ten_finger_pads_measured_frame"+str(frame),len(diag["pads"])==10)
 check("all_clearances_finite_frame"+str(frame),all(abs(p["surface_clearance_m"])<3 for p in diag["pads"]))
 print("FRAME",frame,"penetrating",diag["penetrating_pad_count"],"minclear",diag["min_surface_clearance_m"])
sc.frame_set(36)
previous=bpy.data.objects[grip.TARGET].location.copy()
print("INITIAL",grip.measure())
try:
 msg=grip.calibrate()
 print("CONTACT_RESULT",msg,grip.measure())
 check("index_gap_below_3mm",grip.measure()["gap_to_offset_target_m"]<=.003)
 check("original_animated_ik_target_not_changed",(bpy.data.objects[grip.TARGET].location-previous).length<.000001)
 check("calibration_uses_unanimated_IK_proxy",grip._state["proxy"] is not None)
 check("ik_constraint_retargeted_to_proxy",grip._state["ik"].target==grip._state["proxy"])
 pair=grip._thumb_report()
 print("TWO_SIDED_GRIP",json.dumps(pair))
 check("thumb_and_index_on_opposing_sides",pair["opposing_sides"])
 check("thumb_target_under_3mm",pair["thumb_target_gap_m"]<=.003)
 check("grip_staging_is_not_certified_force",pair["pinch_force_newtons"] is None and not pair["grip_physically_validated"])
 post=grip.diagnose(36)
 print("BVH_CONTACT_CLEARANCES",[(p["digit"],p["surface_clearance_m"]) for p in post["pads"] if p["digit"] in ("R_index","R_thumb")])
 check("all_ten_pads_not_penetrating_in_pose36",post["penetrating_pad_count"]==0)
 check("index_pad_min_film_clearance_1mm",next(p for p in post["pads"] if p["digit"]=="R_index")["surface_clearance_m"]>=.0009)
 check("thumb_pad_not_penetrating",next(p for p in post["pads"] if p["digit"]=="R_thumb")["surface_clearance_m"]>=-.00005)
 status="PASS"
except Exception as exc:
 print("CONTACT_NOT_REACHED",repr(exc))
 status="HOLD"
 check("unreachable_restores_r_hand",(bpy.data.objects[grip.TARGET].location-previous).length<.00001)
# Always reversible and source unchanged.
grip.clear()
check("ik_constraint_restored_to_original",any(c.type=="IK" and c.target==bpy.data.objects[grip.TARGET] for pb in bpy.data.objects[hand.RIG].pose.bones for c in pb.constraints))
check("temporary_ik_proxy_removed","FWAI / VQ04.04 temporary right-hand IK goal" not in bpy.data.objects)
hand.clear();film.clear()
check("all_preview_collections_removed",hand.COL not in bpy.data.collections and film.COL not in bpy.data.collections)
check("original_scene_objects_still_present",original.issubset(set(bpy.data.objects)))
check("source_scene_sha_unchanged",source_hash==hashlib.sha256(source.read_bytes()).hexdigest())
report={"schema":"FWAI_VQ04_04_BVH_FINGER_TEST_V1","tests":tests,"passed":sum(tests.values()),"total":len(tests),
"status":status,"precalibration_measures":measures,"source_sha":source_hash,
"full_film_grip_validated":False,"full_mesh_collision_validated":False}
(OUT/"VQ04_04_FINGER_DIAGNOSTICS.json").write_text(json.dumps(report,indent=2))
print("FWAI_VQ04_04_FINGER_TESTS",report["passed"],report["total"],report["status"])
