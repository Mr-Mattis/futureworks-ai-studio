"""Future Works AI Studio — local Blender live scene bridge.
Visible GUI polls an allowlisted, atomically written local command file.
No socket listener, network access, arbitrary Python execution, or automatic save.
"""
bl_info = {
    "name": "Future Works AI Studio — Live View",
    "author": "Future Works AI Studio",
    "version": (0, 4, 0),
    "blender": (5, 3, 0),
    "location": "3D View > Sidebar > Future Works",
    "description": "Watch agent-driven scene pose, selection and preview changes live in Blender GUI",
    "category": "3D View",
}
import bpy
import json
import os
import tempfile
from pathlib import Path
from bpy.props import BoolProperty, StringProperty

BRIDGE = Path.home() / "Documents" / "futureworks-vq03" / "live_bridge"
COMMANDS = BRIDGE / "commands.json"
ACK = BRIDGE / "ack.json"
RIG_NAME = "FWAI-M001 / 6ft5in RIG / VQ03"
ALLOWED_TARGETS = {
    "IK TARGET / L HAND", "IK TARGET / R HAND",
    "IK TARGET / L FOOT", "IK TARGET / R FOOT",
}
ALLOWED_POSES = {1, 36, 72}
_state = {"seq": 0, "status": "Ready", "enabled": False, "processed": 0}
def _write_atomic(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".fwai-ack-", suffix=".json", dir=str(path.parent))
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            json.dump(obj,f,indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp,str(path))
    finally:
        if os.path.exists(temp):
            os.remove(temp)
def _redraw():
    if bpy.context.screen:
        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":area.tag_redraw()
def apply_command(command):
    kind = command.get("type")
    scene=bpy.context.scene
    if kind == "set_pose":
        frame=command.get("frame")
        if type(frame) is not int or frame not in ALLOWED_POSES:
            raise ValueError("Invalid pose frame; allowed frames 1, 36, 72")
        scene.frame_set(frame)
        return "Visible pose changed to frame "+str(frame)
    if kind == "set_frame":
        frame=command.get("frame")
        if type(frame) is not int or not (1 <= frame <= 72):
            raise ValueError("Frame must be integer in [1,72]")
        scene.frame_set(frame)
        return "Timeline frame "+str(frame)
    if kind == "select_rig":
        rig=bpy.data.objects.get(RIG_NAME)
        if not rig:raise ValueError("VQ03 rig missing")
        # Deselect without invoking global operators and without writing source .blend.
        for o in bpy.context.selected_objects:o.select_set(False)
        rig.select_set(True)
        bpy.context.view_layer.objects.active=rig
        rig.show_in_front=True
        return "Selected VQ03 rig"
    if kind == "set_ik_target":
        name=command.get("target")
        vals=command.get("location")
        if name not in ALLOWED_TARGETS:raise ValueError("Unknown or unauthorized IK target")
        if not isinstance(vals,list) or len(vals)!=3 or any(type(v) not in (int,float) or not (-10 <= v <= 10) for v in vals):
            raise ValueError("Invalid bounded 3D target coordinates")
        obj=bpy.data.objects.get(name)
        if not obj:raise ValueError("Missing IK target")
        # This is intentionally a non-destructive GUI preview; animation keys are untouched.
        obj.location=tuple(float(v) for v in vals)
        bpy.context.view_layer.update()
        return "Moved "+name
    raise ValueError("Command is not allowlisted")

def process_once():
    """A single synchronous tick, separately testable without GUI timers."""
    if not COMMANDS.is_file():return None
    try:
        payload=json.loads(COMMANDS.read_text(encoding="utf-8"))
        seq=payload.get("seq")
        if type(seq) is not int or not (1<=seq<=1000000000):
            raise ValueError("Invalid sequence number")
        # Ignore already acknowledged commands across Blender restarts.
        previous=0
        if ACK.is_file():
            try:previous=int(json.loads(ACK.read_text(encoding="utf-8")).get("seq",0))
            except (ValueError,TypeError,KeyError):previous=0
        if seq <= max(previous,_state["seq"]):return None
        command=payload.get("command")
        if not isinstance(command,dict):raise ValueError("Missing command object")
        status="ok"
        try:message=apply_command(command)
        except (ValueError,RuntimeError,KeyError) as exc:
            status="rejected";message=str(exc)[:200]
        result={"schema":"FWAI_LIVE_GUI_ACK_V1","seq":seq,"status":status,"message":message,
                "frame":bpy.context.scene.frame_current,"gui_visible":not bpy.app.background}
        _write_atomic(ACK,result)
        _state.update(seq=seq,status=message,processed=_state["processed"]+1)
        _redraw()
        return result
    except (OSError,ValueError,TypeError) as exc:
        _state["status"]="Bridge read error: "+str(exc)[:90]
        return None
def timer():
    if not _state["enabled"]:return None
    process_once()
    return 0.5
class FWAI_OT_toggle_live(bpy.types.Operator):
    bl_idname="fwai.toggle_live"
    bl_label="Start/Stop Live Sync"
    def execute(self,context):
        _state["enabled"]=not _state["enabled"]
        if _state["enabled"] and not bpy.app.timers.is_registered(timer):
            bpy.app.timers.register(timer,first_interval=0.1,persistent=True)
        self.report({"INFO"},"FWAI live sync "+("ON" if _state["enabled"] else "OFF"))
        return {"FINISHED"}
class FWAI_PT_live(bpy.types.Panel):
    bl_label="Future Works — Live Sync"
    bl_idname="FWAI_PT_live"
    bl_space_type="VIEW_3D"
    bl_region_type="UI"
    bl_category="Future Works"
    def draw(self,context):
        col=self.layout.column(align=True)
        col.label(text="Local agent-to-Blender bridge")
        col.label(text="Sync: "+("ON" if _state["enabled"] else "OFF"),
                  icon="CHECKMARK" if _state["enabled"] else "PAUSE")
        col.operator("fwai.toggle_live",text="Stop Live Sync" if _state["enabled"] else "Start Live Sync",
                     icon="PAUSE" if _state["enabled"] else "PLAY")
        col.label(text="Last command: "+str(_state["seq"]))
        col.label(text=_state["status"][:55])
        col.label(text="Unsaved live preview",icon="INFO")
        col.label(text="No network / no auto-save")
classes=(FWAI_OT_toggle_live,FWAI_PT_live)
def register():
    for c in classes:bpy.utils.register_class(c)
    if not bpy.app.background and not _state["enabled"]:
        _state["enabled"]=True
        if not bpy.app.timers.is_registered(timer):
            bpy.app.timers.register(timer,first_interval=0.2,persistent=True)
def unregister():
    _state["enabled"]=False
    if bpy.app.timers.is_registered(timer):bpy.app.timers.unregister(timer)
    for c in reversed(classes):bpy.utils.unregister_class(c)
if __name__=="__main__":register()
