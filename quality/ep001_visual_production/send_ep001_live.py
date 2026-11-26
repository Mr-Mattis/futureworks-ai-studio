"""Send safe reference/film-frame commands to the already-running Blender one persistent Blender session.

No new Blender processes or windows, no cloud, no arbitrary scripts, no save.
"""
import argparse,json,time,tempfile,os
from pathlib import Path
BASE=Path.home()/"Documents"/"futureworks-ep001-production"/"live_bridge"
CMD=BASE/"command.json";ACK=BASE/"ack.json"
def run(command):
 BASE.mkdir(parents=True,exist_ok=True)
 old=0
 for path in (CMD,ACK):
  if path.exists():
   try:old=max(old,int(json.loads(path.read_text()).get("seq",0)))
   except (ValueError,TypeError):pass
 seq=old+1
 fd,tmp=tempfile.mkstemp(dir=str(BASE),prefix=".fwai-ep001-",suffix=".json")
 try:
  with os.fdopen(fd,"w",encoding="utf-8") as f:
   json.dump({"seq":seq,"command":command},f)
   f.flush();os.fsync(f.fileno())
  os.replace(tmp,CMD)
 finally:
  if os.path.exists(tmp):os.remove(tmp)
 for attempt in range(70):
  if ACK.exists():
   try:
    report=json.loads(ACK.read_text(encoding="utf-8"))
    if report.get("seq")==seq:
     print(json.dumps(report,indent=2))
     return 0 if (report.get("status")=="ok" and report.get("pid")==json.loads((BASE.parent/"evidence"/"EP001_PERSISTENT_BRIDGE.json").read_text())["pid"]
                  and report.get("gui_visible") is True and report.get("window_count")==1) else 1
   except (OSError,ValueError):pass
  time.sleep(.15)
 print(json.dumps({"status":"NO_ACK","seq":seq,"message":"No Blender screenshot or completion inferred"}))
 return 3
if __name__=="__main__":
 p=argparse.ArgumentParser()
 g=p.add_mutually_exclusive_group(required=True)
 g.add_argument("--show",choices=["G","QA","F","MECH","CAR","PROFILE","REAR"])
 g.add_argument("--frame",type=int,choices=[1,18,36,54,72])
 g.add_argument("--inspect",action="store_true")
 a=p.parse_args()
 command={"op":"show","key":a.show} if a.show else ({"op":"frame","frame":a.frame} if a.frame is not None else {"op":"inspect"})
 raise SystemExit(run(command))
