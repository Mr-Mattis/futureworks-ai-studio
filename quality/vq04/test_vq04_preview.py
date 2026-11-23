"""VQ04 engineering gate for live in-memory lower-leg mesh preview.
Test against a loaded VQ03 .blend; source scene never saved or overwritten.
"""
import bpy,hashlib,json,sys,math,tempfile,copy
from pathlib import Path
sys.path.insert(0,str(Path.home()/"Documents"/"futureworks-vq04"))
import fwai_geometry_preview as preview
BASE=Path.home()/"Documents"/"futureworks-vq04"
OUT=BASE/"evidence"
OUT.mkdir(parents=True,exist_ok=True)
assert not bpy.data.collections.get(preview.COLLECTION),"Test must start on clean base scene"
src=(preview.ROOT/(preview.ASSET_ID+".json"))
payload=json.loads(src.read_text())
digest=hashlib.sha256(src.read_bytes()).hexdigest()
cmd={"type":"load_preview","asset_id":preview.ASSET_ID,"sha256":digest}
tests={}
def ck(name,ok):
    tests[name]=bool(ok)
    if not ok:raise AssertionError(name)
original=set(bpy.data.objects.keys())
rig=bpy.data.objects[preview.SCENE_RIG]
ck("canonical_ref_hash_lock",hashlib.sha256(preview.CANONICAL.read_bytes()).hexdigest()==preview.CANON_SHA)
ck("metric_scene_1_9558m",bpy.context.scene.unit_settings.system=="METRIC" and bpy.data.objects.get("METRIC / 1.9558m height witness") is not None)
ck("local_payload_70_parts",len(payload["parts"])==70)
ck("payload_under_128kb",src.stat().st_size<128*1024)
try:preview.load({**cmd,"sha256":"0"*64});rejected=False
except ValueError:rejected=True
ck("reject_tampered_digest",rejected and bpy.data.collections.get(preview.COLLECTION) is None)
try:preview.load({**cmd,"asset_id":"not_allowlisted"});rejected=False
except ValueError:rejected=True
ck("reject_unknown_asset",rejected)
with tempfile.TemporaryDirectory(prefix="fwai-vq04-negative-") as root:
    old=preview.ROOT
    preview.ROOT=Path(root)
    p=Path(root)/(preview.ASSET_ID+".json")
    bad=copy.deepcopy(payload)
    bad["parts"][0]["bone"]="NISSAN / door passenger"
    raw=json.dumps(bad).encode()
    p.write_bytes(raw)
    try:preview.load({"type":"load_preview","asset_id":preview.ASSET_ID,"sha256":hashlib.sha256(raw).hexdigest()});rejected=False
    except ValueError:rejected=True
    ck("reject_untrusted_bone_binding",rejected)
    bad=copy.deepcopy(payload)
    bad["parts"][0]["a"]=[float("nan"),0,0]
    raw=json.dumps(bad).encode();p.write_bytes(raw)
    try:preview.load({"type":"load_preview","asset_id":preview.ASSET_ID,"sha256":hashlib.sha256(raw).hexdigest()});rejected=False
    except ValueError:rejected=True
    ck("reject_nonfinite_geometry",rejected)
    preview.ROOT=old
message=preview.load(cmd)
col=bpy.data.collections[preview.COLLECTION]
ck("live_geom_load_70_objects",len(col.objects)==70 and "70" in message)
ck("bind_parent_to_approved_rig",all(o.parent==rig and o.parent_type=="BONE" for o in col.objects))
ck("source_unchanged",original.issubset(set(bpy.data.objects.keys())))
ck("hash_provenance_recorded",col["FWAI_SHA256"]==digest)
ck("creative_gate_unapproved",col["FWAI_APPROVED"] is False)
bpy.context.scene.frame_set(1)
obj=bpy.data.objects["FWAI VQ04 / L_thigh_guard_front"]
pos1=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation.copy()
bpy.context.scene.frame_set(36)
pos2=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation.copy()
ck("rig_attached_geometry_moves_across_poses",(pos2-pos1).length>0.005)
ck("preview_inspection", "70" in preview.inspect())
# Save only an image/evidence, not a new .blend or modification to the approved master.
sc=bpy.context.scene
sc.render.resolution_x=1280;sc.render.resolution_y=720
sc.render.resolution_percentage=100
sc.render.image_settings.file_format="PNG"
im=OUT/"VQ04_LOWER_BODY_LIVE_PREVIEW.png"
sc.render.filepath=str(im)
bpy.ops.render.render(write_still=True)
ck("generated_preview_render",im.is_file() and im.stat().st_size>10000)
old_hash=hashlib.sha256(im.read_bytes()).hexdigest()
ck("preview_sha_written",len(old_hash)==64)
preview.load(cmd)
ck("reload_is_idempotent",len(bpy.data.collections[preview.COLLECTION].objects)==70)
message=preview.clear()
ck("clearing_only_preview_mesh",len(bpy.data.objects)==len(original) and bpy.data.collections.get(preview.COLLECTION) is None)
ck("clear_idempotent", "No preview" in preview.clear())
ck("scene_base_not_saved",bpy.data.filepath.endswith("FWAI_VQ03_MECH_NISSAN_VINYL.blend"))
result={"schema":"FWAI_VQ04_TEST_RESULT_V1","status":"PASS" if all(tests.values()) else "FAIL",
"tests":tests,"passed":sum(tests.values()),"total":len(tests),
"preview_sha256":old_hash,"source_scene_sha256":hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
"visual_approval":False,"automatic_save":False,"paid_calls":0}
(OUT/"VQ04_ENGINEERING_TESTS.json").write_text(json.dumps(result,indent=2))
print("FWAI_VQ04_GEOMETRY_TESTS",result["passed"],result["total"],result["status"])
