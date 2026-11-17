"""Archive exactly the three paid Runway tasks from the owner-scoped pilot.
No paid provider calls. Uses authenticated GET /v1/tasks and strict P05
download.py (HTTPS hostname bounds, verified task identity, ffprobe, immutability).
"""
import json,sys
from pathlib import Path
import runway_three_clip_pilot as pilot
sys.path.insert(0,str(Path.home()/"futureworks-studio/futureworks-p04-quality-v3/video/p05"))
from download import archive_provider_result
from sign_p04_pilot_scope import verify
def archive():
    verify()
    state=pilot.begin()
    total=0
    for scene in pilot.PINNED:
        row=state["scenes"][scene]
        if row["state"]=="archived":
            print(scene,"already archived",row["clip_sha256"]);total+=1;continue
        task_id=row.get("task_id")
        if not task_id:raise RuntimeError("Missing paid task receipt "+scene)
        response=pilot.api("GET","/v1/tasks/"+task_id)
        if response.get("id")!=task_id:raise RuntimeError("Provider receipt mismatch")
        status=response.get("status")
        if status!="SUCCEEDED":
            print(scene,"not ready",status);continue
        target=pilot.OUT/(scene+"_"+task_id+".mp4")
        record=archive_provider_result(response,task_id,target)
        row.pop("output_url",None)
        row.update({"state":"archived","clip_sha256":record["sha256"],"clip_file":record["file"],"media":record["verified_media"],"bytes":record["bytes"],"archived_at":pilot.iso()})
        pilot.save(pilot.OUT/"pilot-journal.json",state)
        total+=1
        print(scene,"ARCHIVED",record["verified_media"]["width"],"x",record["verified_media"]["height"],"sha256",record["sha256"])
    print("ARCHIVED",total,"of",3)
if __name__=="__main__":archive()
