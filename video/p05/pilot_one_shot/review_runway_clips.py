"""Produce offline contact sheet and QC index from verified Runway pilot clips."""
import hashlib,json,subprocess
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
ROOT=Path.home()/"Documents"/"futureworks-p05-data"/"real-runway-pilot-001"
d=json.loads((ROOT/"pilot-journal.json").read_text())
frames=ROOT/"review_frames"
frames.mkdir(exist_ok=True)
sheet=Image.new("RGB",(1440,900),(15,18,22))
draw=ImageDraw.Draw(sheet)
report=[]
for i,scene in enumerate(("S01","S02","S03")):
    job=d["scenes"][scene]
    if job["state"]!="archived":
        print(scene,"PENDING",job["state"]);continue
    raw_path=job["clip_file"]
    file=Path("C:/"+raw_path.removeprefix("/mnt/c/") if raw_path.startswith("/mnt/c/") else raw_path)
    if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest()!=job["clip_sha256"]:raise RuntimeError("clip SHA mismatch")
    for t_idx,sec in enumerate((0.5,2.5,4.5)):
        frame=frames/(scene+f"_{t_idx}.png")
        # Use ffmpeg from Ubuntu WSL: source path is on C drive.
        wsl_source="/mnt/c/"+str(file).replace("\\","/")[3:]
        wsl_dest="/mnt/c/"+str(frame).replace("\\","/")[3:]
        subprocess.run(["wsl.exe","-d","Ubuntu","--","ffmpeg","-nostdin","-hide_banner","-loglevel","error","-ss",str(sec),"-i",wsl_source,"-frames:v","1","-y",wsl_dest],check=True,timeout=45)
        with Image.open(frame) as im:
            tile=ImageOps.fit(im.convert("RGB"),(468,263),method=Image.Resampling.LANCZOS)
            sheet.paste(tile,(t_idx*480+6,i*300+8))
        draw.text((t_idx*480+10,i*300+274),f"{scene} / {sec:.1f}s / real Runway",fill="white")
    report.append({"scene":scene,"path":str(file),"sha256":job["clip_sha256"],"bytes":job["bytes"],"task":job["task_id"],"media":job["media"],"visual_review":"pending_owner","publication_approved":False})
out=ROOT/"RUNWAY_P05_THREE_CLIP_REVIEW_CONTACT_SHEET.png"
sheet.save(out,optimize=True)
(ROOT/"RUNWAY_P05_REVIEW_REPORT.json").write_text(json.dumps({"status":"requires_human_review","videos":report,"actual_verified_clips":len(report),"publishing_authorized":False},indent=2))
print("REVIEW_REPORT",len(report),"clips",out)
