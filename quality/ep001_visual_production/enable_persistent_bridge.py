"""FWAI EP001 — persistent SINGLE Blender GUI visual review bridge.

Runs IN MEMORY in the existing visible Blender PID only. It accepts a fixed
allowlist of named images and can select a baked-cloth frame. It cannot load
arbitrary paths, invoke scripts, save scenes, create windows, or delete files.
Command inputs are local JSON files in a dedicated queue, not HTTP/sockets.
"""
import bpy,os,json,time,hashlib,tempfile
from pathlib import Path
LOCKED_PID=os.getpid()
assert os.getpid()==LOCKED_PID and not bpy.app.background
assert len(bpy.context.window_manager.windows)==1
ROOT=Path.home()/"Documents"/"futureworks-ep001-production"
BRIDGE=ROOT/"live_bridge"
CMD=BRIDGE/"command.json"
ACK=BRIDGE/"ack.json"
PRE=Path.home()/"Documents"/"futureworks-p04-data"/"FWAI-M001_EP001_PREPRODUCTION"
BASE=ROOT/"reference"
PUBLIC={
 "G":BASE/"S01_WIDE_PHOTO_LOCKED_CORE_CANDIDATE_G.png",
 "QA":BASE/"S01_CANDIDATE_G_PRODUCTION_FRAMING_QA.png",
 "F":PRE/"05_LOCAL_KEYFRAMES"/"S01"/"candidate_F_leg_grip_repair"/"FWAI_EP001_S01_MASKED_POSE_COMPOSITE_E.png",
 "MECH":Path.home()/"Documents"/"futureworks-p04-comfyui"/"output"/"FWAI_M001_LOCKED_V2_CHARACTER_KEYFRAME_00002_.png",
 "CAR":PRE/"02_CLEAN_CAR_REFERENCES"/"PRIMARY_NISMO_PASSENGER_3Q_500x293.png",
 "PROFILE":PRE/"02_CLEAN_CAR_REFERENCES"/"SUPPORT_NISMO_PASSENGER_SIDE_PROFILE.png",
 "REAR":PRE/"02_CLEAN_CAR_REFERENCES"/"SUPPORT_NISMO_REAR_3Q.png",
}
b=ROOT/"reference"/"S01_CANDIDATE_G_QA.json"
proof=json.loads(b.read_text())
assert hashlib.sha256(PUBLIC["G"].read_bytes()).hexdigest()==proof["result_sha256"]
assert hashlib.sha256(PUBLIC["MECH"].read_bytes()).hexdigest()=="5dcefd9309510754d7b5dd5dd549eae6f3244d1a4a3b6f9056c2055d620ba12b"
def atomic_json(path,thing):
    path.parent.mkdir(exist_ok=True,parents=True)
    fd,t=tempfile.mkstemp(dir=str(path.parent),prefix=".fwai-ep001-",suffix=".json")
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            json.dump(thing,f,indent=2)
            f.flush();os.fsync(f.fileno())
        os.replace(t,path)
    finally:
        if os.path.exists(t):os.remove(t)
def view_screen():
    w=next((w for w in bpy.context.window_manager.windows if w.screen.name=="Scripting"),None)
    if not w:raise RuntimeError("Existing Scripting workspace isn't active")
    s=w.screen
    viewer=max((a for a in s.areas if a.type=="IMAGE_EDITOR"),key=lambda a:a.width*a.height,default=None)
    if not viewer:raise RuntimeError("Existing image editor not found")
    return viewer
def status():
    a=view_screen()
    return {"pid":os.getpid(),"blender_window_count":len(bpy.context.window_manager.windows),
       "viewer":a.spaces.active.image.name if a.spaces.active.image else None,
       "frame":bpy.context.scene.frame_current,
       "source_blend":bpy.data.filepath,
       "scene_autosaved":False}
def apply(order):
    if not isinstance(order,dict) or "op" not in order:raise ValueError("Malformed EP001 command")
    if order["op"]=="show":
        if set(order)!={"op","key"}:raise ValueError("Unknown show parameters")
        k=order["key"]
        if type(k) is not str or k not in PUBLIC:raise ValueError("Reference must be locked key")
        path=PUBLIC[k]
        if not path.is_file():raise ValueError("Reference file unavailable")
        viewer=view_screen()
        image=bpy.data.images.load(str(path),check_existing=True)
        image.use_fake_user=True
        image.name="FWAI EP001 / "+k+" / approved source" if k=="MECH" else "FWAI EP001 / "+k
        viewer.spaces.active.image=image
        viewer.tag_redraw()
        return "SHOW "+k+" ("+str(image.size[0])+"x"+str(image.size[1])+")"
    if order["op"]=="frame":
        if set(order)!={"op","frame"} or type(order["frame"]) is not int or order["frame"] not in (1,18,36,54,72):
            raise ValueError("Frame not in approved 1/18/36/54/72")
        bpy.context.scene.frame_set(order["frame"])
        return "FRAME "+str(order["frame"])
    if order["op"]=="inspect":
        if set(order)!={"op"}:raise ValueError("Unknown inspect parameters")
        return "Persistent Blender "+json.dumps(status())
    raise ValueError("Command not permitted")
STATE={"processed":0,"last":0}
def poll():
    try:
        if CMD.exists():
            obj=json.loads(CMD.read_text(encoding="utf-8"))
            seq=obj.get("seq")
            if type(seq) is not int or not (0<seq<100000000):
                raise ValueError("Invalid sequence")
            receipt_seq=0
            if ACK.exists():
                try:receipt_seq=int(json.loads(ACK.read_text()).get("seq",0))
                except Exception:receipt_seq=0
            if seq>max(receipt_seq,STATE["last"]):
                try:
                    message=apply(obj["command"])
                    state="ok"
                except (KeyError,ValueError,RuntimeError,AssertionError) as ex:
                    message=str(ex)[:230]
                    state="rejected"
                out={"schema":"FWAI_EP001_SINGLE_GUI_BRIDGE_V1",
                  "seq":seq,"status":state,"message":message,
                  "pid":os.getpid(),"gui_visible":not bpy.app.background,
                  "windows_created":0,"window_count":len(bpy.context.window_manager.windows),
                  "master_source_saved":False,"paid_api_calls":0}
                atomic_json(ACK,out)
                STATE["last"]=seq
                STATE["processed"]+=1
    except (OSError,ValueError,TypeError,KeyError) as e:
        STATE["error"]=str(e)[:190]
    return .4
slot=bpy.app.driver_namespace.get("FWAI_EP001_GUI_BRIDGE")
if slot and bpy.app.timers.is_registered(slot["timer"]):
    bpy.app.timers.unregister(slot["timer"])
bpy.app.timers.register(poll,first_interval=.25,persistent=True)
bpy.app.driver_namespace["FWAI_EP001_GUI_BRIDGE"]={"timer":poll,"state":STATE}
ROOT.joinpath("evidence","EP001_PERSISTENT_BRIDGE.json").write_text(
    json.dumps({"pid":os.getpid(),"existing_blender_window_count":len(bpy.context.window_manager.windows),
      "queue":str(BRIDGE),"allowed_image_keys":sorted(PUBLIC),
      "preapproved_owner_master_sha":"5dcefd9309510754d7b5dd5dd549eae6f3244d1a4a3b6f9056c2055d620ba12b",
      "remote_execution":False,"new_blender_gui":False,"autodelete":False,
      "paid_cloud":False,"registered_timer":bpy.app.timers.is_registered(poll)},indent=2))
print("FWAI_EP001_ONE_GUI_PERSISTENT_BRIDGE_STARTED",os.getpid(),len(PUBLIC))
