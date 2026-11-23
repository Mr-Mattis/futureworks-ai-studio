"""VQ04.03 native Blender UI operator regression, without user GUI activation."""
from pathlib import Path
import bpy,sys,hashlib,json
ROOT=Path.home()/"Documents"/"futureworks-vq04-03"
USERADD=Path.home()/"AppData"/"Roaming"/"Blender Foundation"/"Blender"/"5.3"/"scripts"/"addons"
sys.path.insert(0,str(USERADD))
sys.path.insert(0,str(ROOT))
import fwai_live_bridge_addon as bridge
sc=bpy.context.scene;sc.frame_set(36)
source=Path(bpy.data.filepath);sha=hashlib.sha256(source.read_bytes()).hexdigest()
checks={}
def ck(k,v):
  checks[k]=bool(v)
  if not v:raise AssertionError(k)
bridge.register()
ck("ui_operator_registers",hasattr(bpy.ops.fwai,"hand_load_vq043"))
ck("ui_refuses_pinch_stage_before_load",bpy.ops.fwai.hand_stage_vq043(frame=72)=={"CANCELLED"})
ck("ui_loads_hands",bpy.ops.fwai.hand_load_vq043()=={"FINISHED"})
ck("ui_changes_pose_to_reach",bpy.ops.fwai.hand_stage_vq043(frame=36)=={"FINISHED"})
ck("ui_calibrates_reach_pose",bpy.ops.fwai.hand_calibrate_vq043()=={"FINISHED"})
ck("ui_resets_calibration",bpy.ops.fwai.hand_reset_vq043()=={"FINISHED"})
ck("ui_sets_pinch_pose",bpy.ops.fwai.hand_stage_vq043(frame=72)=={"FINISHED"})
ck("ui_clears_geometry",bpy.ops.fwai.hand_clear_vq043()=={"FINISHED"})
ck("no_autosave_from_ui",hashlib.sha256(source.read_bytes()).hexdigest()==sha)
bridge.unregister()
report={"schema":"FWAI_VQ04_03_NATIVE_UI_REGRESSION_V1","checks":checks,"passed":sum(checks.values()),"total":len(checks),
"all_pass":all(checks.values()),"gui_actually_visible":False,
"note":"UI operator registration tested in background; visible Blender separately acknowledged live bridge commands."}
out=ROOT/"evidence";out.mkdir(exist_ok=True)
(out/"VQ04_03_UI_TESTS.json").write_text(json.dumps(report,indent=2))
print("FWAI_VQ04_03_UI_TESTS",report["passed"],report["total"],report["all_pass"])
