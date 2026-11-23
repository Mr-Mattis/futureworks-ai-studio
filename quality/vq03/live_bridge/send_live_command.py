"""Queue a safe, allowlisted Blender GUI command with atomic JSON handoff.
Blender must be open with 'Future Works — Live Sync' enabled. No network and no arbitrary code.
Usage (PowerShell):
 python send_live_command.py --pose 36
 python send_live_command.py --frame 24
 python send_live_command.py --select-rig
"""
from pathlib import Path
import json, tempfile, os, argparse, time
BRIDGE=Path.home()/"Documents"/"futureworks-vq03"/"live_bridge"
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
    opts.add_argument("--ik-target",choices=["L HAND","R HAND","L FOOT","R FOOT"])
    p.add_argument("--location",type=float,nargs=3,metavar=("X","Y","Z"))
    args=p.parse_args()
    if args.pose is not None:command={"type":"set_pose","frame":args.pose}
    elif args.frame is not None:
        if not 1<=args.frame<=72:p.error("Frame must be between 1 and 72")
        command={"type":"set_frame","frame":args.frame}
    elif args.select_rig:command={"type":"select_rig"}
    else:
        if args.location is None:p.error("--ik-target requires --location X Y Z")
        if any(not (-10 <= v <= 10) for v in args.location):p.error("IK target coordinates must be between -10 and +10")
        command={"type":"set_ik_target","target":"IK TARGET / "+args.ik_target,"location":args.location}
    raise SystemExit(send(command))
if __name__=="__main__":main()
