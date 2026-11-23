"""VQ04.03 contact-solve engineering tests; single pose only."""
from pathlib import Path
import bpy, sys, json, hashlib
ROOT=Path.home()/"Documents"/"futureworks-vq04-03";sys.path.insert(0,str(ROOT))
import fwai_hand_tool_preview as hw
import fwai_grip_contact as contact
import importlib
importlib.reload(contact)
OUT=ROOT/"evidence";OUT.mkdir(exist_ok=True,parents=True)
source=Path(bpy.data.filepath);old_sha=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.context.scene.frame_set(36)
hw.load()
tests={}
def ck(name,condition):
    tests[name]=bool(condition)
    if not condition:raise AssertionError(name)
before=contact.measure()
ck("initial_finger_gap_above_3mm",before["gap_m"]>.03)
orig=bpy.data.objects["IK TARGET / R HAND"].location.copy()
msg=contact.calibrate()
after=contact.measure()
ck("calibration_complete","reach achieved" in msg)
ck("measured_gap_under_3mm",after["gap_m"]<=.003)
sc=bpy.context.scene
sc.render.resolution_x=1280
sc.render.resolution_y=720
sc.render.resolution_percentage=100
sc.render.image_settings.file_format="PNG"
render=OUT/"VQ04_03_CONTACT_CALIBRATED.png"
sc.render.filepath=str(render)
bpy.ops.render.render(write_still=True)
ck("calibrated_contact_render_exists",render.is_file() and render.stat().st_size>12000)
ck("calibration_revalidated_after_render",contact.calibrate().startswith(("Kinematic fingertip already calibrated","Frame-36 fingertip kinematic reach achieved")) and contact.measure()["gap_m"]<=.003)
# Native Blender timeline scrubbing (not through our command bridge) can reset
# the animated underlying IK target. The receipt must detect invalidation.
bpy.context.scene.frame_set(72)
bpy.context.scene.frame_set(36)
ck("native_timeline_scrub_invalidates_contact_status","kinematic_only=False" in contact.inspect())
ck("native_timeline_scrub_recalibrates", "reach achieved" in contact.calibrate() and contact.measure()["gap_m"]<=.003)
ck("other_hand_unchanged",bpy.data.objects["IK TARGET / L HAND"].location.y==-1.02 or abs(bpy.data.objects["IK TARGET / L HAND"].location.y+1.02)<.0001)
ck("source_sha_unmodified",hashlib.sha256(source.read_bytes()).hexdigest()==old_sha)
ck("preview_objects_present_during_calibration",len([o for o in bpy.data.objects if o.name.startswith("FWAI GRIP /")])>30)
message=contact.clear()
ck("contact_correction_reversible","Restored original" in message)
ck("right_ik_target_restored",(bpy.data.objects["IK TARGET / R HAND"].location-orig).length<.00001)
ck("clear_is_idempotent","No active" in contact.clear())
# Test wrong-frame reject without altering current state.
bpy.context.scene.frame_set(72)
try:contact.calibrate();rejected=False
except ValueError:rejected=True
ck("frame72_invalid_contact_request_rejected",rejected)
bpy.context.scene.frame_set(36)
hw.clear()
ck("preview_removed_after_contact_cleared",hw.COL not in bpy.data.collections)
ck("source_preserved_after_cleanup",hashlib.sha256(source.read_bytes()).hexdigest()==old_sha)
report={"schema":"FWAI_VQ04_03_KINEMATIC_CONTACT_TEST_V1","checks":tests,"passes":sum(tests.values()),"total":len(tests),
 "pre_calibration":before,"post_calibration":after,"kinematic_contact_pass":after["gap_m"]<=.003,
 "friction_or_material_clamping_validated":False,"creative_approved":False}
(OUT/"VQ04_03_CONTACT_TEST.json").write_text(json.dumps(report,indent=2))
print("FWAI_VQ04_03_CONTACT_TEST",report["passes"],report["total"],report["kinematic_contact_pass"])
