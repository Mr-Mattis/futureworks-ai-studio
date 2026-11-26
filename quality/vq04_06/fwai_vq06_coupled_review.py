"""Future Works AI Studio VQ04.06 – native baked cloth live inspection.

Watch genuine Blender disk-cache-backed cloth in the visible GUI.
No listening socket, arbitrary executable, image upload, autosave or deletion.
Commands are allowlisted local JSON requests and acknowledged with GUI status.
"""
bl_info={
 "name":"Future Works AI Studio — VQ04.06 Mech-Coupled Cloth",
 "author":"Future Works AI Studio",
 "version":(0,5,0),
 "blender":(5,3,0),
 "location":"View3D > Sidebar > Future Works",
 "description":"Live inspection of independent baked film, with reversible view smoothing",
 "category":"3D View"
}
import bpy, json, os, tempfile, math
from pathlib import Path
from mathutils import Vector
BRIDGE=Path.home()/"Documents"/"futureworks-vq04-06"/"live_bridge"
CMD=BRIDGE/"commands.json"
ACK=BRIDGE/"ack.json"
FILM="FWAI VQ04.06 / HAND-COUPLED FILM"
CAMERA_NAME="FWAI VQ04.06 / TEMP COUPLED DETAIL CAMERA"
SMOOTH_NAME="FWAI VQ04.06 / TEMP VIEW SUBDIVISION"
ALLOWED_FRAMES={1,18,36,54,72}
state={"enabled":False,"seq":0,"last":"Ready","processed":0,"original_camera":None}

def get_film():
    film=bpy.data.objects.get(FILM)
    if film is None or film.type!="MESH":
        raise ValueError("Open the VQ04.06 baked scene first")
    mod=next((m for m in film.modifiers if m.type=="CLOTH"),None)
    if not mod or not mod.point_cache.is_baked:
        raise ValueError("Cloth point cache is not baked; do not show it as simulated")
    return film,mod

def _camera_view():
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=="VIEW_3D":
                try:area.spaces.active.region_3d.view_perspective="CAMERA"
                except Exception:pass
                area.tag_redraw()

def detail():
    film,cloth=get_film()
    sc=bpy.context.scene
    if bpy.data.objects.get(CAMERA_NAME) is None:
        cam_data=bpy.data.cameras.new(CAMERA_NAME)
        cam=bpy.data.objects.new(CAMERA_NAME,cam_data)
        sc.collection.objects.link(cam)
        cam.location=(-.66,-1.55,1.08)
        target=Vector((-.58,-.55,.81))
        cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
        cam_data.type="ORTHO";cam_data.ortho_scale=1.25
    else:cam=bpy.data.objects[CAMERA_NAME]
    if state["original_camera"] is None and sc.camera!=cam:
        state["original_camera"]=sc.camera.name if sc.camera else None
    sc.camera=cam
    _camera_view()
    return "Viewing physical-film close-up, unsaved"

def wide():
    sc=bpy.context.scene
    prior=state["original_camera"]
    if prior and bpy.data.objects.get(prior):
        sc.camera=bpy.data.objects[prior]
    else:
        # Native existing canonical camera object, if present.
        candidates=[o for o in bpy.data.objects if o.type=="CAMERA" and o.name!=CAMERA_NAME]
        if not candidates:raise ValueError("No original scene camera found")
        sc.camera=candidates[0]
    _camera_view()
    return "Returned to original scene camera, unsaved"

def smooth():
    ob,_mod=get_film()
    existing=ob.modifiers.get(SMOOTH_NAME)
    if existing:return "Smooth preview already enabled (derived only)"
    for poly in ob.data.polygons:poly.use_smooth=True
    sub=ob.modifiers.new(SMOOTH_NAME,"SUBSURF")
    sub.subdivision_type="CATMULL_CLARK"
    sub.levels=1;sub.render_levels=2
    mods=ob.modifiers
    idx=next(i for i,m in enumerate(mods) if m==sub)
    before=next(i for i,m in enumerate(mods) if m.type=="SOLIDIFY")
    mods.move(idx,before)
    assert [m.type for m in ob.modifiers]==["HOOK","CLOTH","SUBSURF","SOLIDIFY"]
    return "Subdivision smoothing enabled after baked cloth (unsaved)"

def unsmooth():
    ob,_mod=get_film()
    m=ob.modifiers.get(SMOOTH_NAME)
    if m:ob.modifiers.remove(m)
    for p in ob.data.polygons:p.use_smooth=False
    return "Restored original faceted preview (unsaved)"

def status():
    ob,m=get_film()
    cache=m.point_cache
    return ("Baked "+str(cache.frame_start)+"–"+str(cache.frame_end)
         +", frame "+str(bpy.context.scene.frame_current)
         +", smooth "+str(SMOOTH_NAME in ob.modifiers)
         +", source not edited")

def apply(command):
    if not isinstance(command,dict) or "type" not in command:
        raise ValueError("Malformed command")
    kind=command.get("type")
    if kind=="frame":
        if set(command)!={"type","frame"} or type(command["frame"]) is not int or command["frame"] not in ALLOWED_FRAMES:
            raise ValueError("Only approved simulation frames 1,18,36,54,72")
        get_film()
        bpy.context.scene.frame_set(command["frame"])
        return status()
    if set(command)!={"type"}:raise ValueError("No additional command fields allowed")
    if kind=="smooth":return smooth()
    if kind=="unsmooth":return unsmooth()
    if kind=="detail":return detail()
    if kind=="wide":return wide()
    if kind=="inspect":return status()
    raise ValueError("No arbitrary actions or source modification allowed")

def _atomic(path,content):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=str(path.parent),prefix=".fwai-vq06-",suffix=".json")
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            json.dump(content,f,indent=2)
            f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.remove(tmp)

def tick():
    if not CMD.is_file():return None
    try:
        input=json.loads(CMD.read_text(encoding="utf-8"))
        seq=input.get("seq")
        if type(seq) is not int or not 0<seq<1000000000:raise ValueError("Invalid sequence")
        acked=0
        if ACK.is_file():
            try:acked=int(json.loads(ACK.read_text()).get("seq",0))
            except (ValueError,TypeError):acked=0
        if seq<=max(acked,state["seq"]):return None
        try:
            message=apply(input["command"])
            result="ok"
        except (KeyError,ValueError,RuntimeError,AssertionError) as exc:
            message=str(exc)[:180];result="rejected"
        receipt={
            "schema":"FWAI_VQ04_06_LIVE_GUI_ACK_V1",
            "seq":seq,"status":result,"message":message,
            "frame":bpy.context.scene.frame_current,
            "gui_visible":not bpy.app.background,
            "paid_calls":0,"scene_saved":False
        }
        _atomic(ACK,receipt)
        state["seq"]=seq;state["last"]=message;state["processed"]+=1
        for area in bpy.context.screen.areas if bpy.context.screen else []:
            if area.type=="VIEW_3D":area.tag_redraw()
        return receipt
    except (ValueError,TypeError,OSError,KeyError) as exc:
        state["last"]="Bridge read error: "+str(exc)[:60]
        return None

def poll():
    if not state["enabled"]:return None
    tick()
    return .4

class FWAI_OT_vq06_frame(bpy.types.Operator):
    bl_idname="fwai.vq06_frame"
    bl_label="VQ06 Cloth Frame"
    frame:bpy.props.IntProperty(default=36)
    def execute(self,ctx):
        try:message=apply({"type":"frame","frame":self.frame})
        except (ValueError,RuntimeError) as exc:
            self.report({"WARNING"},str(exc));return {"CANCELLED"}
        self.report({"INFO"},message);return {"FINISHED"}

class FWAI_OT_vq06_action(bpy.types.Operator):
    bl_idname="fwai.vq06_action"
    bl_label="VQ06 Cloth Action"
    action:bpy.props.StringProperty(default="inspect")
    def execute(self,ctx):
        try:message=apply({"type":self.action})
        except (ValueError,RuntimeError) as exc:
            self.report({"WARNING"},str(exc));return {"CANCELLED"}
        self.report({"INFO"},message);return {"FINISHED"}

class FWAI_OT_vq06_sync(bpy.types.Operator):
    bl_idname="fwai.vq06_sync"
    bl_label="Toggle VQ06 Live Sync"
    def execute(self,ctx):
        state["enabled"]=not state["enabled"]
        if state["enabled"] and not bpy.app.timers.is_registered(poll):
            bpy.app.timers.register(poll,first_interval=.2,persistent=True)
        self.report({"INFO"},"VQ06 live sync "+("ON" if state["enabled"] else "OFF"))
        return {"FINISHED"}

class FWAI_PT_vq06(bpy.types.Panel):
    bl_idname="FWAI_PT_vq06"
    bl_label="VQ04.06 — Baked Vinyl Physics"
    bl_space_type="VIEW_3D"
    bl_region_type="UI"
    bl_category="Future Works"
    def draw(self,ctx):
        col=self.layout.column(align=True)
        col.label(text="REAL Blender disk-baked cloth",icon="MOD_CLOTH")
        try:
            ob,mod=get_film()
            col.label(text="Cache: BAKED / 72 frames",icon="CHECKMARK")
        except ValueError:
            col.label(text="Open baked scene!",icon="ERROR")
        row=col.row(align=True)
        for frame,label in ((1,"HOLD"),(36,"REACH"),(72,"LAY")):
            op=row.operator("fwai.vq06_frame",text=label)
            op.frame=frame
        row=col.row(align=True)
        for frame in (18,54):
            op=row.operator("fwai.vq06_frame",text="f"+str(frame))
            op.frame=frame
        col.operator("screen.animation_play",text="Play / Pause",icon="PLAY")
        row=col.row(align=True)
        for action,label in (("detail","Detail Cam"),("wide","Wide Cam")):
            op=row.operator("fwai.vq06_action",text=label)
            op.action=action
        row=col.row(align=True)
        for action,label in (("smooth","Smooth View"),("unsmooth","Raw Grid")):
            op=row.operator("fwai.vq06_action",text=label)
            op.action=action
        col.operator("fwai.vq06_sync",text="Live Sync: "+("ON" if state["enabled"] else "OFF"))
        op=col.operator("fwai.vq06_action",text="Inspect Bake")
        op.action="inspect"
        col.label(text="R-index drives cloth / force NOT measured")
        col.label(text="VQ06 material realism: QC HOLD",icon="ERROR")
        col.label(text="No autosave, no paid Runway")
        col.label(text="Last: "+str(state["seq"]))

classes=(FWAI_OT_vq06_frame,FWAI_OT_vq06_action,FWAI_OT_vq06_sync,FWAI_PT_vq06)
def register():
    for cls in classes:bpy.utils.register_class(cls)
    if not bpy.app.background and not state["enabled"]:
        state["enabled"]=True
        if not bpy.app.timers.is_registered(poll):
            bpy.app.timers.register(poll,first_interval=.2,persistent=True)
def unregister():
    state["enabled"]=False
    if bpy.app.timers.is_registered(poll):bpy.app.timers.unregister(poll)
    for cls in reversed(classes):bpy.utils.unregister_class(cls)
if __name__=="__main__":register()
