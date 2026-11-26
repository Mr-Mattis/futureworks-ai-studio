"""Send one allowlisted command to the actual Blender 5.3 VQ04.05 GUI.

Usage (PowerShell):
 & $python send_live_cloth.py --frame 36
 & $python send_live_cloth.py --detail
 & $python send_live_cloth.py --smooth

Requires visible Blender with Future Works VQ04.05 live sync enabled. No sockets.
"""
import argparse,json,os,time,tempfile
from pathlib import Path
BASE=Path.home()/"Documents"/"futureworks-vq04-06"/"live_bridge"
CMD=BASE/"commands.json"
ACK=BASE/"ack.json"

def atomic(obj):
    CMD.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=CMD.parent,prefix=".vq05-cmd-",suffix=".json")
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as stream:
            json.dump(obj,stream,indent=2)
            stream.flush();os.fsync(stream.fileno())
        os.replace(tmp,CMD)
    finally:
        if os.path.isfile(tmp):os.remove(tmp)
def send(command,timeout=10):
    last=0
    for p in (CMD,ACK):
        if p.is_file():
            try:last=max(last,int(json.loads(p.read_text(encoding="utf-8")).get("seq",0)))
            except (ValueError,TypeError):pass
    seq=last+1
    atomic({"schema":"FWAI_VQ05_GUI_COMMAND_V1","seq":seq,"command":command})
    until=time.monotonic()+timeout
    while time.monotonic()<until:
        if ACK.is_file():
            try:
                received=json.loads(ACK.read_text(encoding="utf-8"))
                if received.get("seq")==seq:
                    print(json.dumps(received,indent=2))
                    return 0 if received.get("status")=="ok" and received.get("gui_visible") is True else 2
            except (ValueError,PermissionError,OSError):pass
        time.sleep(.15)
    print(json.dumps({"status":"pending","seq":seq,"message":"No visible Blender acknowledgement. Do not infer success."}))
    return 3

def main():
    a=argparse.ArgumentParser()
    opts=a.add_mutually_exclusive_group(required=True)
    opts.add_argument("--frame",type=int,choices=[1,18,36,54,72])
    for k in ("smooth","unsmooth","detail","wide","inspect"):
        opts.add_argument("--"+k,action="store_true")
    args=a.parse_args()
    command={"type":"frame","frame":args.frame} if args.frame is not None else {"type":next(k for k in ("smooth","unsmooth","detail","wide","inspect") if getattr(args,k))}
    raise SystemExit(send(command))
if __name__=="__main__":main()
