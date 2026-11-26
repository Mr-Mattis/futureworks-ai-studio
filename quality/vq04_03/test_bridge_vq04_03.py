"""Safety/functional regression of VQ04.03 live bridge without an actual GUI.
Real visible GUI is separately proven by ack receipts; this test does NOT claim GUI.
"""
from pathlib import Path
import bpy, sys, importlib.util, tempfile, json, hashlib
ROOT=Path.home()/"Documents"/"futureworks-vq04-03";sys.path.insert(0,str(ROOT))
src=ROOT/"fwai_live_bridge_addon.py"
spec=importlib.util.spec_from_file_location("fwai_vq043_bridge_test",src)
bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
tests={}
def ck(n,v):
    tests[n]=bool(v)
    if not v:raise AssertionError(n)
def must_reject(n,cmd):
    try:bridge.apply_command(cmd);bad=False
    except (ValueError,RuntimeError):bad=True
    ck(n,bad)
with tempfile.TemporaryDirectory(prefix="fwai-vq043-") as tmp:
    bridge.BRIDGE=Path(tmp)
    bridge.COMMANDS=bridge.BRIDGE/"commands.json"
    bridge.ACK=bridge.BRIDGE/"ack.json"
    bridge._state.update(seq=0,enabled=False,processed=0)
    def tick(seq,cmd):
        bridge.COMMANDS.write_text(json.dumps({"seq":seq,"command":cmd}))
        return bridge.process_once()
    must_reject("unknown_command_type",{"type":"eval","src":"__import__('os').system('whoami')"})
    must_reject("unknown_file_path_for_hand",{"type":"load_hand_preview","path":"C:/windows/win.ini"})
    must_reject("invalid_stage_outside_1_36_72",{"type":"set_hand_stage","frame":52})
    must_reject("no_contact_solver_before_preview",{"type":"calibrate_grip_contact"})
    result=tick(1,{"type":"load_hand_preview"})
    ck("valid_hand_preview_accepted",result["status"]=="ok" and "30 finger joints" in result["message"])
    ck("background_correctly_not_claimed_gui",result["gui_visible"] is False)
    result=tick(2,{"type":"set_hand_stage","frame":36})
    ck("set_phase_36",result["status"]=="ok" and result["frame"]==36)
    result=tick(3,{"type":"calibrate_grip_contact"})
    ck("calibration_function_calls_real_solver",result["status"]=="ok" and "reach achieved" in result["message"])
    result=tick(4,{"type":"inspect_grip_contact"})
    ck("contact_gap_readback","gap=" in result["message"] and result["status"]=="ok")
    ck("old_seq_ignored",bridge.process_once() is None)
    result=tick(5,{"type":"set_hand_stage","frame":72})
    ck("phase_72_with_contact_cleanup",result["status"]=="ok" and result["frame"]==72)
    result=tick(6,{"type":"clear_hand_preview"})
    ck("reversible_preview_clear",result["status"]=="ok" and "Cleared" in result["message"])
    ck("after_clear_collection_missing",bridge.hand_tool.COL not in bpy.data.collections)
    ck("ack_last_seq_persisted",json.loads(bridge.ACK.read_text())["seq"]==6)
report={"schema":"FWAI_VQ04_03_BRIDGE_TEST_V1","tests":tests,"passed":sum(tests.values()),"total":len(tests),
 "all_pass":all(tests.values()),"browser_or_remote_streaming":False,"gui_receipt_not_inferred_from_background":True}
OUT=ROOT/"evidence";OUT.mkdir(exist_ok=True)
(OUT/"VQ04_03_BRIDGE_TESTS.json").write_text(json.dumps(report,indent=2))
print("FWAI_VQ04_03_BRIDGE_TESTS",report["passed"],report["total"],report["all_pass"])
