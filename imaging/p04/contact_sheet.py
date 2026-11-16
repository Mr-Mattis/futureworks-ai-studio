"""P04 offline contact sheet for human pixel-level review (not extra generation)."""
from __future__ import annotations
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--images-dir",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    folder=Path(args.images_dir).resolve()
    paths=sorted(folder.glob("P04_*.png"))
    if len(paths)!=10:
        raise SystemExit("Expected exactly ten real generated PNGs")
    width,height=384,288
    sheet=Image.new("RGB",(width*5,height*2),(23,25,30))
    draw=ImageDraw.Draw(sheet)
    for i,file in enumerate(paths):
        with Image.open(file) as src:
            src.verify()
        with Image.open(file) as src:
            im=src.convert("RGB")
            im.thumbnail((width-12,height-42))
            x=(i%5)*width+(width-im.width)//2
            y=(i//5)*height+(height-42-im.height)//2
            sheet.paste(im,(x,y))
        draw.text(((i%5)*width+12,(i//5)*height+height-30),
                  file.stem,fill=(234,236,241))
    dest=Path(args.output)
    if not dest.parent.resolve()==folder:
        raise SystemExit("Contact sheet must remain in isolated image output")
    sheet.save(dest,optimize=True)
    print(f"Created original-image review montage from {len(paths)} real ComfyUI outputs: {dest}")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
