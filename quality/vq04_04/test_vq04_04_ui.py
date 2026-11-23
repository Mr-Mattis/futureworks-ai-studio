"""VQ04.04 local bridge security + native film sidebar operator acceptance.
No GIF, no paid service, no .blend changes.
"""
from pathlib import Path
import bpy,sys,hashlib,json,importlib.util,tempfile
ROOT=Path.home()/"Documents"/"futureworks-vq04-04"
OUT=ROOT/"evidence";OUT.mkdir(exist_ok=True)
USERADD=Path.home()/"AppData"/"Roaming"/"Blender Foundation"/"Blender"/"5.3"/"scripts"/"addons"
sys.path.insert(0,str(USERADD));sys.path.insert(0,str(ROOT))
source=Path(bpy.data.filepath);hash_before=hashlib.sha256(source.read_bytes()).hexdigest()
import fwai_live_bridge_addon as bridge
import fwai_hand_tool_preview as hands
import fwai_film_contact as film
import fwai_film_grip as grip
tests={}
def ck(k,v):
    tests[k]=bool(v)
    if not v:raise AssertionError(k)
def reject(name,cmd):
    try:bridge.apply_command(cmd);bad=False
    except (ValueError,RuntimeError):bad=True
    ck(name,bad)
bpy.context.scene.frame_set(36)
# Evaluate explicit local allowlist against unsafe mutations.
reject("reject_arbitrary_code",{"type":"eval","src":"__import__('os').system('whoami')"})
reject("reject_unexpected_film_path",{"type":"load_partial_film","path":"C:/some/other.blend"})
reject("reject_invalid_diagnostic_frame",{"type":"diagnose_fingerpads","frame":200})
reject("reject_film_unknown_field",{"type":"clear_partial_film","delete":True})
reject("reject_calibration_before_assets",{"type":"calibrate_two_sided"})
bridge.register()
ck("native_panel_registered",hasattr(bpy.ops.fwai,"film_load_vq044"))
ck("native_load_film",bpy.ops.fwai.film_load_vq044()=={"FINISHED"})
ck("real_film_geometry_present",len(bpy.data.objects[film.NAME].data.vertices)==425)
ck("native_film_diagnostic",bpy.ops.fwai.film_check_vq044()=={"FINISHED"})
ck("native_grip_rejected_until_hands_loaded",bpy.ops.fwai.film_grip_vq044()=={"CANCELLED"})
hands.load()
ck("native_reach_stage",bpy.ops.fwai.film_phase_vq044(frame=36)=={"FINISHED"})
ck("native_two_sided_calibration",bpy.ops.fwai.film_grip_vq044()=={"FINISHED"})
ck("two_sided_geometry_but_not_force",grip._thumb_report()["two_sided_geometry_pass"] and grip._thumb_report()["pinch_force_newtons"] is None)
ck("native_reset",bpy.ops.fwai.film_reset_vq044()=={"FINISHED"})
ck("native_clear_film",bpy.ops.fwai.film_clear_vq044()=={"FINISHED"})
ck("native_clear_hands",bpy.ops.fwai.hand_clear_vq043()=={"FINISHED"})
ck("no_staged_film_remains",film.COL not in bpy.data.collections)
ck("source_not_written",hashlib.sha256(source.read_bytes()).hexdigest()==hash_before)
bridge.unregister()
report={"schema":"FWAI_VQ04_04_UI_SECURITY_V1","tests":tests,"passed":sum(tests.values()),"total":len(tests),
    "all_pass":all(tests.values()),"background_native_ui_only":True,"actual_visible_gui_checked_separately":False}
(OUT/"VQ04_04_UI_SECURITY_TESTS.json").write_text(json.dumps(report,indent=2))
print("FWAI_VQ04_04_UI_SECURITY",report["passed"],report["total"],report["all_pass"])
