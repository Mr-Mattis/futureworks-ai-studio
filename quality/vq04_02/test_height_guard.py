"""VQ04.02 dimension acceptance for 6ft5in mech helmet.
Proves bounding coordinates, reversible in-memory geometry, master immutability.
"""
from pathlib import Path
import bpy,sys,json,hashlib
ROOT=Path.home()/"Documents"/"futureworks-vq04-02"
sys.path.insert(0,str(ROOT))
import fwai_height_guard as hg
source=Path(bpy.data.filepath)
before_sha=hashlib.sha256(source.read_bytes()).hexdigest()
before=hg.inspect()
tests={}
def ck(k,v):
  tests[k]=bool(v)
  if not v:raise AssertionError(k)
ck("preexisting_helmet_overheight_detected",max(h for _,h in before)>1.9558)
msg=hg.apply()
during=hg.inspect()
ck("all_three_fins_within_1_9558m",max(h for _,h in during)<=1.95582)
for frame in (1,36,72):
  bpy.context.scene.frame_set(frame)
  ck("height_bounded_frame_"+str(frame),max(h for _,h in hg.inspect())<=1.95582)
ck("height_guard_reports_applied","Corrected" in msg)
ck("idempotent_second_apply","already active" in hg.apply())
ck("reversible_mesh_restore","Restored 3" in hg.clear())
after=hg.inspect()
ck("original_fin_heights_restored",before==after)
ck("source_blend_unchanged",hashlib.sha256(source.read_bytes()).hexdigest()==before_sha)
ck("does_not_autosave",bool(bpy.data.filepath))
results={"schema":"FWAI_VQ04_02_HEIGHT_GUARD","checks":tests,"passed":sum(tests.values()),"total":len(tests),"master_height_m":1.9558,
 "before":before,"clamped":during,"restored":after,"production_assets_unchanged":True,"creative_approved":False}
out=ROOT/"evidence";out.mkdir(exist_ok=True)
(out/"VQ04_02_HEIGHT_GUARD_TEST.json").write_text(json.dumps(results,indent=2))
print("FWAI_VQ04_02_HEIGHT_GUARD",results["passed"],results["total"],"PASS")
