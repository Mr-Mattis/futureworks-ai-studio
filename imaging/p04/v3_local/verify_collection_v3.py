import json,hashlib
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageStat
root=Path.home()/"Documents"/"futureworks-p04-data"/"collection-v3"
base=json.loads((root/"receipts.json").read_text())
up=json.loads((root/"upscale-receipts.json").read_text())
items=[]
sheet=Image.new("RGB",(1800,460),(21,25,32))
draw=ImageDraw.Draw(sheet)
for i in range(1,11):
    n=f"{i:02d}"
    a=root/f"V3_{n}_768x512.png"
    p=root/f"V3_{n}_1920x1080_ESRGAN.png"
    assert a.is_file() and p.is_file()
    h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    assert h(a)==base[n]["sha256"] and h(p)==up[n]["sha256"]
    with Image.open(p) as im:
        im.verify()
    with Image.open(p) as im:
        assert im.size==(1920,1080)
        thumb=ImageOps.fit(im.convert("RGB"),(350,197),method=Image.Resampling.LANCZOS)
        x=(i-1)%5*360+5;y=(i-1)//5*230+5
        sheet.paste(thumb,(x,y))
        draw.text((x+5,y+200),n+" | RealESRGAN 1080p",fill="white")
    items.append({"id":n,"original_sha256":h(a),"upscaled_sha256":h(p),"original_dimensions":"768x512","upscaled_dimensions":"1920x1080"})
out=root/"P04_V3_ESRGAN_1080P_CONTACT_SHEET.png"
sheet.save(out,optimize=True)
(root/"P04_V3_VERIFIED_ASSETS.json").write_text(json.dumps({"status":"pixel_hash_and_dimension_verified","model_sha256":"37f9a931c215f040aa6d50f711f2cb115f713c46df1d0d6469a8bd7bfe9a60bb","assets":items,"visual_quality":"requires_owner_review","production_approved":False,"external_upload_approved":False},indent=2))
print("10_NATIVE_AND_10_SUPERRES_ASSETS_VERIFIED")
print(out)
