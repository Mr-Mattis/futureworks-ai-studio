"""Render VQ03 Blender preview as 72 PNGs; ffmpeg separately packages an MP4."""
import bpy,sys
from pathlib import Path
out=Path(sys.argv[sys.argv.index("--")+1]);frames=out/"frames";frames.mkdir(exist_ok=True)
sc=bpy.context.scene;sc.render.engine="BLENDER_EEVEE"
sc.render.resolution_x=960;sc.render.resolution_y=540;sc.render.resolution_percentage=100
sc.render.fps=24;sc.frame_start=1;sc.frame_end=72
sc.render.image_settings.file_format="PNG"
sc.render.filepath=str(frames/"F_")
bpy.ops.render.render(animation=True)
paths=list(frames.glob("F_*.png"))
assert len(paths)==72, f"Only {len(paths)} animation PNGs found"
print("FWAI_VQ03_72_FRAMES_COMPLETE",str(frames))
