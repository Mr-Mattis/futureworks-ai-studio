"""Queue a safe, allowlisted Blender GUI command with atomic JSON handoff.
Blender must be open with 'Future Works — Live Sync' enabled. No network and no arbitrary code.
Usage (PowerShell):
 python send_live_command.py --pose 36
 python send_live_command.py --frame 24
 python send_live_command.py --select-rig
"""
from pathlib import Path
import json, tempfile, os, argparse, time, hashlib
BRIDGE=Path.home()/"Documents"/"futureworks-vq04-04"/"live_bridge_v2"
CMD=BRIDGE/"commands.json"
ACK=BRIDGE/"ack.json"
def put(path,record):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=".fwai-cmd-",suffix=".json",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as stream:
            json.dump(record,stream,indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.remove(tmp)
def send(command,timeout=8):
    old=0
    for path in (CMD,ACK):
        if path.is_file():
            try:old=max(old,int(json.loads(path.read_text(encoding="utf-8")).get("seq",0)))
            except (ValueError,TypeError):pass
    seq=old+1
    put(CMD,{"schema":"FWAI_GUI_COMMAND_V1","seq":seq,"command":command})
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if ACK.is_file():
            try:
                record=json.loads(ACK.read_text(encoding="utf-8"))
                if record.get("seq")==seq:
                    print(json.dumps(record,indent=2))
                    return 0 if record["status"]=="ok" and record.get("gui_visible") else 2
            except (ValueError,KeyError,PermissionError):pass
        time.sleep(.15)
    print(json.dumps({"status":"pending","seq":seq,"message":"Blender GUI did not acknowledge. Do not assume the pose was applied."}))
    return 3
def main():
    p=argparse.ArgumentParser()
    opts=p.add_mutually_exclusive_group(required=True)
    opts.add_argument("--pose",type=int,choices=[1,36,72])
    opts.add_argument("--frame",type=int)
    opts.add_argument("--select-rig",action="store_true")
    opts.add_argument("--load-preview",action="store_true")
    opts.add_argument("--load-identity",action="store_true")
    opts.add_argument("--clear-identity",action="store_true")
    opts.add_argument("--inspect-identity",action="store_true")
    opts.add_argument("--apply-height-guard",action="store_true")
    opts.add_argument("--clear-height-guard",action="store_true")
    opts.add_argument("--inspect-height-guard",action="store_true")
    opts.add_argument("--load-hand",action="store_true")
    opts.add_argument("--clear-hand",action="store_true")
    opts.add_argument("--inspect-hand",action="store_true")
    opts.add_argument("--hand-stage",type=int,choices=[1,36,72])
    opts.add_argument("--calibrate-contact",action="store_true")
    opts.add_argument("--clear-contact",action="store_true")
    opts.add_argument("--inspect-contact",action="store_true")
    opts.add_argument("--load-film",action="store_true")
    opts.add_argument("--inspect-film",action="store_true")
    opts.add_argument("--clear-film",action="store_true")
    opts.add_argument("--film-stage",type=int,choices=[1,36,72])
    opts.add_argument("--film-door-diagnostic",type=int,choices=[1,36,72])
    opts.add_argument("--film-finger-diagnostic",type=int,choices=[1,36,72])
    opts.add_argument("--calibrate-two-sided",action="store_true")
    opts.add_argument("--inspect-two-sided",action="store_true")
    opts.add_argument("--clear-two-sided",action="store_true")
    opts.add_argument("--clear-preview",action="store_true")
    opts.add_argument("--inspect-preview",action="store_true")
    opts.add_argument("--ik-target",choices=["L HAND","R HAND","L FOOT","R FOOT"])
    p.add_argument("--location",type=float,nargs=3,metavar=("X","Y","Z"))
    args=p.parse_args()
    if args.pose is not None:command={"type":"set_pose","frame":args.pose}
    elif args.frame is not None:
        if not 1<=args.frame<=72:p.error("Frame must be between 1 and 72")
        command={"type":"set_frame","frame":args.frame}
    elif args.select_rig:command={"type":"select_rig"}
    elif args.load_preview:
        asset="FWAI_M001_LOWER_BODY_DETAIL_V1"
        path=Path.home()/"Documents"/"futureworks-vq04"/"staging"/(asset+".json")
        if not path.is_file():p.error("Preview asset must be generated first")
        command={"type":"load_preview","asset_id":asset,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
    elif args.load_identity:
        identity="FWAI_M001_V2_IDENTITY_DETAIL_01"
        path=Path.home()/"Documents"/"futureworks-vq04-02"/"staging"/(identity+".json")
        if not path.is_file():p.error("Identity stage must be generated first")
        command={"type":"load_identity_preview","asset_id":identity,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
    elif args.clear_identity:command={"type":"clear_identity_preview"}
    elif args.inspect_identity:command={"type":"inspect_identity_preview"}
    elif args.apply_height_guard:command={"type":"apply_height_guard"}
    elif args.clear_height_guard:command={"type":"clear_height_guard"}
    elif args.inspect_height_guard:command={"type":"inspect_height_guard"}
    elif args.load_hand:command={"type":"load_hand_preview"}
    elif args.clear_hand:command={"type":"clear_hand_preview"}
    elif args.inspect_hand:command={"type":"inspect_hand_preview"}
    elif args.hand_stage is not None:command={"type":"set_hand_stage","frame":args.hand_stage}
    elif args.calibrate_contact:command={"type":"calibrate_grip_contact"}
    elif args.clear_contact:command={"type":"clear_grip_contact"}
    elif args.inspect_contact:command={"type":"inspect_grip_contact"}
    elif args.load_film:command={"type":"load_partial_film"}
    elif args.inspect_film:command={"type":"inspect_partial_film"}
    elif args.clear_film:command={"type":"clear_partial_film"}
    elif args.film_stage is not None:command={"type":"set_film_stage","frame":args.film_stage}
    elif args.film_door_diagnostic is not None:command={"type":"diagnose_partial_film","frame":args.film_door_diagnostic}
    elif args.film_finger_diagnostic is not None:command={"type":"diagnose_fingerpads","frame":args.film_finger_diagnostic}
    elif args.calibrate_two_sided:command={"type":"calibrate_two_sided"}
    elif args.inspect_two_sided:command={"type":"inspect_two_sided"}
    elif args.clear_two_sided:command={"type":"clear_two_sided"}
    elif args.clear_preview:command={"type":"clear_preview"}
    elif args.inspect_preview:command={"type":"inspect_preview"}
    else:
        if args.location is None:p.error("--ik-target requires --location X Y Z")
        if any(not (-10 <= v <= 10) for v in args.location):p.error("IK target coordinates must be between -10 and +10")
        command={"type":"set_ik_target","target":"IK TARGET / "+args.ik_target,"location":args.location}
    raise SystemExit(send(command))
if __name__=="__main__":main()
