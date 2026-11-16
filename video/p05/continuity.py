"""P05.06 local clip continuity triage, never automatic creative approval.

Samples decoded opening, midpoint and closing frames with system FFmpeg.
Uses deterministic color proxies ONLY. This is NOT a vision-quality model,
rights assessment or proof of generative frame consistency.
"""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import statistics

from engine import Rejected, STAGES


def frame_rgb(path, second, *, ffmpeg="/usr/bin/ffmpeg"):
    command=[ffmpeg,"-nostdin","-hide_banner","-loglevel","error",
             "-ss",str(second),"-i",str(path),"-frames:v","1",
             "-vf","scale=64:64","-pix_fmt","rgb24","-f","rawvideo","-"]
    p=subprocess.run(command,capture_output=True,timeout=25)
    if p.returncode or len(p.stdout)!=64*64*3:
        raise Rejected("Could not decode representative video frame")
    raw=p.stdout
    return [round(sum(raw[i::3])/(64*64),3) for i in range(3)]


def color_distance(a,b):
    return round((sum((x-y)**2 for x,y in zip(a,b))/3)**0.5,3)


def inspect(local_previews, *, max_gap=42):
    """Generate correction *requests*, never label three clips as approved."""
    root=Path(local_previews).resolve()
    videos=[root/("P05_STORYBOARD_"+s+".mp4") for s in STAGES]
    if any(not v.is_file() or not v.is_relative_to(root) for v in videos):
        raise Rejected("Exactly three known local preview files required")
    rows=[]
    for scene,v in zip(STAGES,videos):
        frames=[frame_rgb(v,t) for t in (0.25,2.0,3.5)]
        rows.append({"scene_id":scene,"file_name":v.name,
                     "frame_times_seconds":[0.25,2.0,3.5],
                     "frame_mean_rgb":frames,
                     "motion_proxy_distance":color_distance(frames[0],frames[2])})
    gaps=[{"cut":STAGES[i]+"→"+STAGES[i+1],
           "color_distance":color_distance(rows[i]["frame_mean_rgb"][-1],
                                           rows[i+1]["frame_mean_rgb"][0])}
          for i in range(2)]
    needs=[g for g in gaps if g["color_distance"]>max_gap]
    return {"checkpoint":"P05.06","verdict":"human_review_required",
            "source":"local_FFmpeg_storyboard_previews_not_generative_video",
            "sampled_scenes":rows,"cuts":gaps,
            "correction_requests":[
              "Color-grade and inspect the transition "+g["cut"]+
              " (mean RGB discrepancy "+str(g["color_distance"])+")" for g in needs],
            "always_required":["Human visual review for robot morphology, silhouette and continuity",
                               "Verify original image licensing and consent before production",
                               "Review actual moving AI-generated clips after budget authorization"],
            "publish_authorized":False,"paid_provider_calls":0}


if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--preview-directory",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    report=inspect(args.preview_directory)
    dest=Path(args.output).resolve()
    if dest.parent != Path(args.preview_directory).resolve():
        raise Rejected("Save QC report alongside local preview clips")
    dest.write_text(json.dumps(report,indent=2))
    print(json.dumps({"verdict":report["verdict"],
                      "review_required":len(report["always_required"]),
                      "correction_requests":len(report["correction_requests"]),
                      "paid_provider_calls":0}))
