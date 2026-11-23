"""QC detector for gross image defects; does NOT certify creative realism."""
from pathlib import Path
from PIL import Image
from collections import Counter
import json,sys,hashlib
ROOT=Path.home()/"Documents"/"futureworks-maintenance"
def scan(name):
    folder=ROOT/name
    output=folder/("BL05_P04_composite.png" if name=="poc-bl05-gpu-baseline" else "BL02_P04_composite.png" if name=="poc-bl02" else "BL01_P04_composite.png")
    with Image.open(output) as im,Image.open(folder/"BL01_edit_mask.png") as m:
        img=im.convert("RGB"); mask=m.convert("L")
        vals=[img.getpixel((x,y)) for y in range(576) for x in range(1024) if mask.getpixel((x,y))>=128]
        most,n=Counter(vals).most_common(1)[0]
        share=n/len(vals)
        # Large contiguous exact-color regions indicate damaged latent reconstruction.
        no_flat_fill=share<0.18
        result={"schema":"FWAI_VQ02_QC_GROSS_ARTIFACT_GATE_V1","candidate":name,
          "masked_sample_count":len(vals),"most_common_rgb":most,"most_common_fraction":round(share,5),
          "gross_flat_fill_test":"PASS" if no_flat_fill else "FAIL",
          "technical_image_continuity":"PARTIAL_TESTS_ONLY",
          "human_realism_review":"PENDING","approved_for_runway":False,
          "is_creative_pass":False}
    (folder/"VQ02_GROSS_ARTIFACT_QA.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    return no_flat_fill
if __name__=="__main__":
    if len(sys.argv)!=2 or sys.argv[1] not in {"poc-bl01","poc-bl02","poc-bl05-gpu-baseline"}:raise SystemExit("Usage: python quality_gate.py poc-bl01|poc-bl02|poc-bl05-gpu-baseline")
    scan(sys.argv[1])
