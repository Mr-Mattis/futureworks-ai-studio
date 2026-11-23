"""Future Works AI Studio — local Blender live scene bridge.
Visible GUI polls an allowlisted, atomically written local command file.
No socket listener, network access, arbitrary Python execution, or automatic save.
"""
bl_info = {
    "name": "Future Works AI Studio — Live View",
    "author": "Future Works AI Studio",
    "version": (0, 8, 1),
    "blender": (5, 3, 0),
    "location": "3D View > Sidebar > Future Works",
    "description": "Watch agent-driven scene pose, selection and preview changes live in Blender GUI",
    "category": "3D View",
}
import bpy
import json
import os
import fwai_geometry_preview as vq04preview
import fwai_identity_preview as identity_preview
import fwai_height_guard as height_guard
import fwai_hand_tool_preview as hand_tool
import fwai_grip_contact as contact
import fwai_film_contact as partial_film
import fwai_film_grip as partial_grip
import tempfile
from pathlib import Path
from bpy.props import BoolProperty, StringProperty

BRIDGE = Path.home() / "Documents" / "futureworks-vq04-04" / "live_bridge_v2"
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
        if frame!=36:
            contact.clear()
            partial_grip.clear()
        scene.frame_set(frame)
        return "Visible pose changed to frame "+str(frame)
    if kind == "set_frame":
        frame=command.get("frame")
        if type(frame) is not int or not (1 <= frame <= 72):
            raise ValueError("Frame must be integer in [1,72]")
        if frame!=36:
            contact.clear()
            partial_grip.clear()
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
    if kind == "load_preview":
        return vq04preview.load(command)
    if kind == "clear_preview":
        if set(command) != {"type"}:raise ValueError("Unexpected clear-preview arguments")
        return vq04preview.clear()
    if kind == "inspect_preview":
        if set(command) != {"type"}:raise ValueError("Unexpected inspection arguments")
        return vq04preview.inspect()
    if kind == "load_identity_preview":
        return identity_preview.load(command)
    if kind == "clear_identity_preview":
        if set(command)!={"type"}:raise ValueError("Unexpected identity clear arguments")
        return identity_preview.clear()
    if kind == "inspect_identity_preview":
        if set(command)!={"type"}:raise ValueError("Unexpected identity inspect arguments")
        return identity_preview.inspect()
    if kind == "apply_height_guard":
        if set(command)!={"type"}:raise ValueError("Unexpected height-guard arguments")
        return height_guard.apply()
    if kind == "clear_height_guard":
        if set(command)!={"type"}:raise ValueError("Unexpected height-clear arguments")
        return height_guard.clear()
    if kind == "inspect_height_guard":
        if set(command)!={"type"}:raise ValueError("Unexpected height-inspect arguments")
        return "Fin top elevations (m): "+str(height_guard.inspect())
    if kind == "load_hand_preview":
        if set(command)!={"type"}:raise ValueError("Unexpected hand-preview arguments")
        return hand_tool.load()
    if kind == "clear_hand_preview":
        if set(command)!={"type"}:raise ValueError("Unexpected hand clear arguments")
        contact.clear()
        partial_grip.clear()
        return hand_tool.clear()
    if kind == "inspect_hand_preview":
        if set(command)!={"type"}:raise ValueError("Unexpected hand inspection arguments")
        return hand_tool.inspect()
    if kind == "set_hand_stage":
        if set(command)!={"type","frame"}:raise ValueError("Unexpected grip stage arguments")
        if command["frame"]!=36:
            contact.clear()
            partial_grip.clear()
        return hand_tool.set_stage(command["frame"])
    if kind == "calibrate_grip_contact":
        if set(command)!={"type"}:raise ValueError("Unexpected contact calibration arguments")
        return contact.calibrate()
    if kind == "clear_grip_contact":
        if set(command)!={"type"}:raise ValueError("Unexpected contact reset arguments")
        return contact.clear()
    if kind == "inspect_grip_contact":
        if set(command)!={"type"}:raise ValueError("Unexpected contact inspection arguments")
        return contact.inspect()
    if kind=="set_film_stage":
        if set(command)!={"type","frame"}:raise ValueError("Unexpected film-stage fields")
        partial_grip.clear()
        return partial_film.set_stage(command["frame"])
    if kind=="load_partial_film":
        if set(command)!={"type"}:raise ValueError("Unexpected film-load fields")
        return partial_film.load()
    if kind=="clear_partial_film":
        if set(command)!={"type"}:raise ValueError("Unexpected film-clear fields")
        partial_grip.clear()
        return partial_film.clear()
    if kind=="inspect_partial_film":
        if set(command)!={"type"}:raise ValueError("Unexpected film-inspect fields")
        return partial_film.inspect()
    if kind=="diagnose_partial_film":
        if set(command)!={"type","frame"} or type(command["frame"]) is not int or command["frame"] not in (1,36,72):
            raise ValueError("Disallowed film diagnostic")
        r=partial_film.diagnose(command["frame"])
        return "Film "+str(command["frame"])+": penetration="+str(r["door_penetrating_vertices"])+", door coverage="+str(r["door_projected_coverage_fraction_upper_estimate"])
    if kind=="calibrate_two_sided":
        if set(command)!={"type"}:raise ValueError("Unexpected two-sided pinch arguments")
        return partial_grip.calibrate()
    if kind=="inspect_two_sided":
        if set(command)!={"type"}:raise ValueError("Unexpected contact-inspection arguments")
        return partial_grip.inspect()
    if kind=="clear_two_sided":
        if set(command)!={"type"}:raise ValueError("Unexpected contact-clear arguments")
        return partial_grip.clear()
    if kind=="diagnose_fingerpads":
        if set(command)!={"type","frame"} or type(command["frame"]) is not int or command["frame"] not in (1,36,72):
            raise ValueError("Disallowed finger diagnostics")
        r=partial_grip.diagnose(command["frame"])
        return "Finger pads "+str(command["frame"])+": intersecting="+str(r["penetrating_pad_count"])+" of 10"
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
        col.separator()
        col.label(text="VQ04.04 — Partial Vinyl / Contact",icon="MOD_CLOTH")
        col.operator("fwai.film_load_vq044",text="Load Narrow Film",icon="ADD")
        row=col.row(align=True)
        for frame,label in ((1,"HOLD"),(36,"REACH"),(72,"LAY")):
            op=row.operator("fwai.film_phase_vq044",text=label)
            op.frame=frame
        col.operator("fwai.film_grip_vq044",text="Stage 2-Sided Grip (36)",icon="CONSTRAINT")
        col.operator("fwai.film_check_vq044",text="Door Collision Check",icon="VIEWZOOM")
        col.operator("fwai.film_reset_vq044",text="Reset Pinch Guides",icon="FILE_REFRESH")
        col.operator("fwai.film_clear_vq044",text="Remove Narrow Film",icon="X")
        col.label(text="Not cloth-baked; no force validation")
        col.separator()
        col.label(text="VQ04.03 — Hand / Tool Controls",icon="BONE_DATA")
        col.operator("fwai.hand_load_vq043",text="Load Hands",icon="ADD")
        row=col.row(align=True)
        for frame,label in ((1,"OPEN"),(36,"REACH"),(72,"PINCH")):
            op=row.operator("fwai.hand_stage_vq043",text=label)
            op.frame=frame
        col.operator("fwai.hand_calibrate_vq043",text="Calibrate Reach (36)",icon="CONSTRAINT")
        col.operator("fwai.hand_reset_vq043",text="Reset Contact",icon="FILE_REFRESH")
        col.operator("fwai.hand_clear_vq043",text="Clear Hand Study",icon="X")
        col.label(text="Mechanical controls ≠ force simulation")
        col.separator()
        col.label(text="VQ04.03 articulated hand controls ready")
        col.label(text="Pinch = kinematic only (no force solver)")
        col.label(text="VQ04.02 identity mesh import ready")
        col.label(text="Identity still unapproved")
        col.label(text="Geometry preview commands supported")
        col.label(text="Unsaved live preview",icon="INFO")
        col.label(text="No network / no auto-save")
class FWAI_OT_hand_load(bpy.types.Operator):
    bl_idname="fwai.hand_load_vq043"
    bl_label="Load Articulated Hands"
    def execute(self,context):
        try:message=hand_tool.load()
        except (ValueError,RuntimeError) as exc:
            self.report({"WARNING"},str(exc)[:180]);return {"CANCELLED"}
        self.report({"INFO"},message)
        return {"FINISHED"}

class FWAI_OT_hand_stage(bpy.types.Operator):
    bl_idname="fwai.hand_stage_vq043"
    bl_label="Hand and Tool Stage"
    frame: bpy.props.IntProperty(default=36)
    def execute(self,context):
        try:
            if self.frame !=36:
                contact.clear()
                partial_grip.clear()
            message=hand_tool.set_stage(self.frame)
        except (ValueError,RuntimeError) as exc:
            self.report({"WARNING"},str(exc)[:180]);return {"CANCELLED"}
        self.report({"INFO"},message)
        return {"FINISHED"}

class FWAI_OT_hand_calibrate(bpy.types.Operator):
    bl_idname="fwai.hand_calibrate_vq043"
    bl_label="Calibrate Frame-36 Finger Target"
    def execute(self,context):
        try:message=contact.calibrate()
        except (ValueError,RuntimeError) as exc:
            self.report({"WARNING"},str(exc)[:180]);return {"CANCELLED"}
        self.report({"INFO"},message)
        return {"FINISHED"}

class FWAI_OT_hand_reset(bpy.types.Operator):
    bl_idname="fwai.hand_reset_vq043"
    bl_label="Reset Kinematic Target"
    def execute(self,context):
        self.report({"INFO"},contact.clear())
        return {"FINISHED"}

class FWAI_OT_hand_clear(bpy.types.Operator):
    bl_idname="fwai.hand_clear_vq043"
    bl_label="Remove Hand Study"
    def execute(self,context):
        contact.clear()
        self.report({"INFO"},hand_tool.clear())
        return {"FINISHED"}

class FWAI_OT_film_load(bpy.types.Operator):
    bl_idname="fwai.film_load_vq044"
    bl_label="Load Partial Film"
    def execute(self,context):
        try:message=partial_film.load()
        except (ValueError,RuntimeError) as exc:
            self.report({"WARNING"},str(exc)[:180]);return {"CANCELLED"}
        self.report({"INFO"},message)
        return {"FINISHED"}
class FWAI_OT_film_phase(bpy.types.Operator):
    bl_idname="fwai.film_phase_vq044"
    bl_label="Film Animation Stage"
    frame: bpy.props.IntProperty(default=36)
    def execute(self,context):
        try:
            partial_grip.clear()
            message=partial_film.set_stage(self.frame)
        except (ValueError,RuntimeError) as exc:
            self.report({"WARNING"},str(exc)[:180]);return {"CANCELLED"}
        self.report({"INFO"},message)
        return {"FINISHED"}
class FWAI_OT_film_grip(bpy.types.Operator):
    bl_idname="fwai.film_grip_vq044"
    bl_label="Stage Two-Sided Grip"
    def execute(self,context):
        try:message=partial_grip.calibrate()
        except (ValueError,RuntimeError) as exc:
            self.report({"WARNING"},str(exc)[:180]);return {"CANCELLED"}
        self.report({"INFO"},message);return {"FINISHED"}
class FWAI_OT_film_check(bpy.types.Operator):
    bl_idname="fwai.film_check_vq044"
    bl_label="Check Door / Film Clearance"
    def execute(self,context):
        try:
            f=bpy.context.scene.frame_current
            if f not in (1,36,72):raise ValueError("Use frame 1/36/72")
            report=partial_film.diagnose(f)
        except (ValueError,RuntimeError) as exc:
            self.report({"WARNING"},str(exc)[:180]);return {"CANCELLED"}
        self.report({"INFO"},"Door collisions: "+str(report["door_penetrating_vertices"])+"; covered area < "+str(round(report["door_projected_coverage_fraction_upper_estimate"]*100,1))+"%")
        return {"FINISHED"}
class FWAI_OT_film_reset(bpy.types.Operator):
    bl_idname="fwai.film_reset_vq044"
    bl_label="Reset Pinch Geometry"
    def execute(self,context):
        self.report({"INFO"},partial_grip.clear());return {"FINISHED"}
class FWAI_OT_film_clear(bpy.types.Operator):
    bl_idname="fwai.film_clear_vq044"
    bl_label="Remove Partial Film"
    def execute(self,context):
        partial_grip.clear()
        self.report({"INFO"},partial_film.clear());return {"FINISHED"}
classes=(FWAI_OT_toggle_live,FWAI_OT_hand_load,FWAI_OT_hand_stage,FWAI_OT_hand_calibrate,FWAI_OT_hand_reset,FWAI_OT_hand_clear,FWAI_OT_film_load,FWAI_OT_film_phase,FWAI_OT_film_grip,FWAI_OT_film_check,FWAI_OT_film_reset,FWAI_OT_film_clear,FWAI_PT_live)
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
