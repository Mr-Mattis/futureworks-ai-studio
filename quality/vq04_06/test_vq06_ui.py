"""VQ04.06 independent controls/security regression against loaded baked .blend."""
import bpy,sys,hashlib,json,tempfile,importlib.util
from pathlib import Path
root=Path.home()/"Documents"/"futureworks-vq04-06"
out=root/"evidence"
spec=importlib.util.spec_from_file_location("fwai_vq06_coupled_review",root/"fwai_vq06_coupled_review.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
source=Path(bpy.data.filepath);source_sha=hashlib.sha256(source.read_bytes()).hexdigest()
checks={}
def ck(k,v):
    checks[k]=bool(v)
    if not v:raise AssertionError(k)
def reject(k,cmd):
    try:m.apply(cmd);failed=False
    except ValueError:failed=True
    ck(k,failed)
ck("real_disk_cache_baked",m.get_film()[1].point_cache.is_baked)
ck("frame1_operator_supported","frame 1" in m.apply({"type":"frame","frame":1}))
ck("frame36_operator_supported","frame 36" in m.apply({"type":"frame","frame":36}))
ck("frame72_operator_supported","frame 72" in m.apply({"type":"frame","frame":72}))
reject("arbitrary_python_rejected",{"type":"eval","src":"__import__('os').system('whoami')"})
reject("arbitrary_frame_rejected",{"type":"frame","frame":999})
reject("unexpected_path_rejected",{"type":"inspect","path":"C:/Windows"})
reject("unexpected_boolean_frame_rejected",{"type":"frame","frame":True})
ck("smooth_view_only","smoothing enabled" in m.smooth().lower())
ck("correct_eval_stack",[x.type for x in m.get_film()[0].modifiers]==["HOOK","CLOTH","SUBSURF","SOLIDIFY"])
ck("smooth_no_cache_invalidation",m.get_film()[1].point_cache.is_baked)
ck("smooth_idempotent","already" in m.smooth())
ck("unsmooth_view_only","Restored" in m.unsmooth())
ck("source_modifier_stack_restored",[x.type for x in m.get_film()[0].modifiers]==["HOOK","CLOTH","SOLIDIFY"])
orig_camera=bpy.context.scene.camera
ck("detail_view_camera","close-up" in m.detail())
ck("detail_camera_orbit",bpy.context.scene.camera.name==m.CAMERA_NAME)
ck("return_to_original_camera","original" in m.wide().lower() and bpy.context.scene.camera==orig_camera)
reject("no_arbitrary_filesystem_deletion",{"type":"delete","path":"C:/Users"})
with tempfile.TemporaryDirectory() as tmp:
    m.BRIDGE=Path(tmp);m.CMD=m.BRIDGE/"commands.json";m.ACK=m.BRIDGE/"ack.json"
    m.state.update(seq=0,enabled=False,processed=0)
    m.CMD.write_text(json.dumps({"seq":1,"command":{"type":"frame","frame":54}}))
    ack=m.tick()
    ck("valid_sequence_acknowledged",ack["status"]=="ok" and ack["frame"]==54)
    ck("headless_not_claimed_visible",ack["gui_visible"] is False)
    ck("duplicate_sequence_ignored",m.tick() is None)
    m.CMD.write_text(json.dumps({"seq":2,"command":{"type":"eval","src":"hack"}}))
    bad=m.tick()
    ck("unsafe_action_ack_rejected",bad["status"]=="rejected")
    ck("receipt_persisted",json.loads(m.ACK.read_text())["seq"]==2)
m.register()
ck("new_native_sidebar_operational",hasattr(bpy.ops.fwai,"vq06_frame"))
ck("native_frame_button",bpy.ops.fwai.vq06_frame(frame=36)=={"FINISHED"})
ck("native_smoothing_button",bpy.ops.fwai.vq06_action(action="smooth")=={"FINISHED"})
ck("native_original_reset",bpy.ops.fwai.vq06_action(action="unsmooth")=={"FINISHED"})
ck("native_reject_invalid_action",bpy.ops.fwai.vq06_action(action="erase_disk")=={"CANCELLED"})
m.unregister()
ck("canonical_blend_bytes_untouched",hashlib.sha256(source.read_bytes()).hexdigest()==source_sha)
result={"schema":"FWAI_VQ04_06_LIVE_PANEL_TEST_V1","tests":checks,"passed":sum(checks.values()),
"total":len(checks),"all_pass":all(checks.values()),
"gui_visible":False,"no_paid_services":True,"original_blend_sha":source_sha}
(out/"VQ04_06_UI_TESTS.json").write_text(json.dumps(result,indent=2))
print("FWAI_VQ06_UI_TESTS",result["passed"],"/",result["total"],"PASS")
