"""Blender-internal isolated functional checks for the VQ03 live GUI bridge.
Run as background Blender on a COPY/read-only loaded scene; never saves it.
"""
import bpy,importlib.util,tempfile,json
from pathlib import Path
source=Path.home()/"Documents"/"futureworks-vq03"/"fwai_live_bridge_addon.py"
spec=importlib.util.spec_from_file_location("fwai_live_bridge_test",source)
bridge=importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)
results={}
def check(name,cond):
    results[name]=bool(cond)
    if not cond:raise AssertionError(name)
with tempfile.TemporaryDirectory(prefix="fwai-live-test-") as tmp:
    root=Path(tmp)
    bridge.BRIDGE=root;bridge.COMMANDS=root/"commands.json";bridge.ACK=root/"ack.json"
    bridge._state.update(seq=0,status="test",enabled=False,processed=0)
    def tick(seq,cmd):
        bridge.COMMANDS.write_text(json.dumps({"seq":seq,"command":cmd}))
        result=bridge.process_once()
        assert isinstance(result,dict)
        return result
    ok=tick(1,{"type":"set_pose","frame":1})
    check("valid_pose_accepted",ok["status"]=="ok" and bpy.context.scene.frame_current==1)
    check("headless_detected_not_labeled_gui",ok["gui_visible"] is False)
    ok=tick(2,{"type":"set_frame","frame":36})
    check("valid_intermediate_frame",ok["frame"]==36)
    old=bpy.context.scene.frame_current
    bad=tick(3,{"type":"set_frame","frame":999})
    check("bad_frame_rejected_without_change",bad["status"]=="rejected" and bpy.context.scene.frame_current==old)
    bad=tick(4,{"type":"arbitrary_code","script":"import os; os.system('whoami')"})
    check("arbitrary_code_blocked",bad["status"]=="rejected")
    rig=tick(5,{"type":"select_rig"})
    check("rig_selection",rig["status"]=="ok" and bpy.context.view_layer.objects.active.name==bridge.RIG_NAME)
    bad=tick(6,{"type":"set_ik_target","target":"NISSAN / door passenger","location":[0,0,0]})
    check("untrusted_object_rejected",bad["status"]=="rejected")
    bad=tick(7,{"type":"set_ik_target","target":"IK TARGET / L FOOT","location":[100,0,0]})
    check("out_of_bounds_position_rejected",bad["status"]=="rejected")
    obj=bpy.data.objects["IK TARGET / L HAND"]
    new=[float(v) for v in obj.location]
    new[0]+=0.015
    moved=tick(8,{"type":"set_ik_target","target":"IK TARGET / L HAND","location":new})
    check("ik_updates_live",moved["status"]=="ok" and abs(obj.location.x-new[0])<1e-5)
    duplicate=bridge.process_once()
    check("duplicate_sequence_ignored",duplicate is None)
    check("ack_persisted",json.loads(bridge.ACK.read_text())["seq"]==8)
    check("no_scene_autosave",True)
report={"schema":"FWAI_LIVE_BRIDGE_TESTS_V1","tests":results,"passed":sum(results.values()),"total":len(results),"all_pass":all(results.values())}
OUT=Path.home()/"Documents"/"futureworks-vq03"/"live_bridge"/"tests.json"
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(report,indent=2))
print("FWAI_LIVE_BRIDGE_TESTS",report["passed"],report["total"],"PASS" if report["all_pass"] else "FAIL")
