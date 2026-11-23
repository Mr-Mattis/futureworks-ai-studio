"""P05.07 zero-budget local cinematic *storyboard previews* from P04 images.

Uses FFmpeg's Ken-Burns camera move on still images; no generative video model
is called. This is NOT proof of Runway image-to-video generation and does not
satisfy P05's paid three-scene approval gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess

from engine import REPO, Rejected, sha

def preview(bundle_path, out, *, fps=24, seconds=4):
    if (fps, seconds) != (24,4):
        raise Rejected("Fixed isolated preview frame budget required")
    path=Path(bundle_path).resolve()
    target=Path(out).resolve()
    if target.is_relative_to(REPO) or target.is_relative_to(Path("/data")):
        raise Rejected("Previews must remain outside git/production")
    bundle=json.loads(path.read_text())
    if bundle.get("project_id")!="FWAI-EP-0001" or bundle.get("assets_count")!=10:
        raise Rejected("Original ten-image batch reference required")
    if any(bundle.get("authorization",{}).values()) or bundle.get("paid_provider_calls")!=0:
        raise Rejected("Cannot invent authorization")
    target.mkdir(parents=True,exist_ok=True)
    originals={s:next((x for x in bundle["assets"] if x["scene_id"]==s),None)
               for s in ("S01","S02","S03")}
    completed=[]
    for idx,(scene,ref) in enumerate(originals.items()):
        if ref is None:
            raise Rejected("Missing approved test scene reference")
        # WSL sees Windows-created output via /mnt/c; the recorded original
        # absolute Windows path is not portable. Resolve by immutable asset ID
        # beside the trusted handoff, then verify SHA instead of path trust.
        if not isinstance(ref["asset_id"],str) or not re.fullmatch(r"P04_[A-Za-z0-9_]+",ref["asset_id"]):
            raise Rejected("Invalid fixed image asset ID")
        img=(path.parent/(ref["asset_id"]+".png")).resolve()
        if not img.is_relative_to(path.parent) or not img.is_file() or sha(img.read_bytes())!=ref["sha256"]:
            raise Rejected("Source-image SHA or path mismatch")
        dest=target/("P05_STORYBOARD_"+scene+".mp4")
        if dest.exists():
            raise Rejected("Never overwrite a different existing preview")
        # FFmpeg produces a genuine local MP4 file with real motion frames
        # from a still source. It does NOT generate novel temporal content.
        framecount=fps*seconds
        command=[
            "/usr/bin/ffmpeg","-nostdin","-hide_banner","-loglevel","error",
            "-threads","2","-loop","1","-framerate",str(fps),
            "-i",str(img),
            "-vf",("scale=960:540:force_original_aspect_ratio=increase,"
                   "crop=960:540,zoompan="
                   "z='min(zoom+0.0007,1.08)':"
                   "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                   "d=1:s=960x540:fps=24,format=yuv420p"),
            "-frames:v",str(framecount),"-an","-c:v","libx264",
            "-preset","ultrafast","-crf","24","-movflags","+faststart",
            "-y",str(dest)
        ]
        result=subprocess.run(command,capture_output=True,text=True,timeout=180)
        if result.returncode!=0:
            raise Rejected("Local FFmpeg failed: "+result.stderr[-250:])
        probe=subprocess.run(
            ["/usr/bin/ffprobe","-v","error","-select_streams","v:0",
             "-show_entries","stream=codec_name,width,height,nb_frames",
             "-of","json",str(dest)],
            capture_output=True,text=True,check=True,timeout=20)
        streams=json.loads(probe.stdout)["streams"]
        if not streams or streams[0].get("codec_name")!="h264" or int(streams[0].get("nb_frames",0))!=framecount:
            raise Rejected("FFmpeg storyboard preview decode metadata mismatch")
        completed.append({
            "scene_id":scene,"source_asset_id":ref["asset_id"],
            "source_sha256":ref["sha256"],"video_sha256":sha(dest.read_bytes()),
            "codec":"h264","width":960,"height":540,
            "frames":framecount,"duration_seconds":seconds,
            "file":str(dest),"source_type":"still_image_camera_motion",
            "generative_video_provider_used":False,
            "human_continuity_review":"required",
        })
    report={
        "checkpoint":"P05.07 LOCAL NON-GENERATIVE PREVIEW ONLY",
        "mode":"FFmpeg_Ken_Burns_from_real_P04_Stills",
        "status":"three_local_storyboards_preserved_not_runway",
        "clips":completed,"total":3,"spent_usd":0,
        "approved_budget_usd":0,
        "runway_video_generation_performed":False,
        "authorization":{"production_approved":False,"spend_authorized":False,
                         "publish_authorized":False},
        "locked_P05_exit":"OPEN",
    }
    target.joinpath("PREVIEW_EVIDENCE.json").write_text(
        json.dumps(report,indent=2))
    return report

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-bundle",required=True)
    parser.add_argument("--output",required=True)
    opts=parser.parse_args()
    print(json.dumps(preview(opts.reference_bundle,opts.output),indent=2))
