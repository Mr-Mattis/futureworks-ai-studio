"""VQ04.02 character identity geometry: isolated Blender proof and negative tests."""
import bpy, sys, json, hashlib, tempfile, copy
from pathlib import Path
sys.path.insert(0,str(Path.home()/"Documents"/"futureworks-vq04"))
import fwai_identity_preview as fw
OUT=Path.home()/"Documents"/"futureworks-vq04-02"/"evidence";OUT.mkdir(parents=True,exist_ok=True)
DATA=fw.ROOT/(fw.ID+".json")
asset=json.loads(DATA.read_text())
digest=hashlib.sha256(DATA.read_bytes()).hexdigest()
command={"type":"load_identity_preview","asset_id":fw.ID,"sha256":digest}
source=Path(bpy.data.filepath);source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
scene=bpy.context.scene
original_names=set(bpy.data.objects.keys())
tests={}
def ck(name,ok):
    tests[name]=bool(ok)
    if not ok:raise AssertionError(name)
def reject(name,cmd):
    try:fw.load(cmd);was_rejected=False
    except ValueError:was_rejected=True
    ck(name,was_rejected)
ck("canonical_master_hash",hashlib.sha256(fw.MASTER.read_bytes()).hexdigest()==fw.MASTER_SHA)
ck("metric_scene",scene.unit_settings.system=="METRIC")
ck("correct_asset_id_and_version",asset["asset_id"]==fw.ID and asset["schema"]=="FWAI_VQ04_IDENTITY_PREVIEW_V1")
ck("correct_payload_size",1<=len(asset["parts"])<=120 and DATA.stat().st_size<131072)
ck("all_design_details_stay_differentiable",len({p["name"] for p in asset["parts"]})==len(asset["parts"]))
ck("never_creative_approved",asset["approved"] is False)
reject("wrong_sha",dict(command,sha256="0"*64))
reject("unapproved_asset_id",dict(command,asset_id="DROP TABLE"))
with tempfile.TemporaryDirectory() as tmp:
    old=fw.ROOT;fw.ROOT=Path(tmp);filename=fw.ROOT/(fw.ID+".json")
    for name,mutation in (
       ("unknown_bone",{"bone":"NISSAN / front bumper"}),
       ("bad_material",{"material":"injected-unknown"}),
       ("bad_thickness",{"thickness":999}),
       ("bad_shape",{"shape":"python"}),
       ("height_escape",{"points":[[-1.7,-1.0,2.4],[-1.65,-1.0,1.85],[-1.8,-1.0,1.87]]}),
    ):
        changed=copy.deepcopy(asset);changed["parts"][0].update(mutation)
        blob=json.dumps(changed).encode();filename.write_bytes(blob)
        reject(name,dict(command,sha256=hashlib.sha256(blob).hexdigest()))
    fw.ROOT=old
ck("invalid_input_never_adds_scene_objects",original_names==set(bpy.data.objects.keys()))
message=fw.load(command)
collection=bpy.data.collections[fw.COL]
ck("loaded_70_identity_parts",len(collection.objects)==70 and "70" in message)
ck("model_continuity_preserved",original_names.issubset(set(bpy.data.objects.keys())))
ck("correct_identity_parenting",all(x.parent and x.parent.name==fw.RIG and x.parent_bone in fw.BONES for x in collection.objects))
ck("different_pbr_materials",len({x.data.materials[0].name for x in collection.objects})>=6)
ck("some_custom_armor_plates",sum(x.type=="MESH" for x in collection.objects)>=20)
ck("some_coolant_curves",sum(x.type=="CURVE" for x in collection.objects)>=20)
ck("source_digest_in_collection",collection["FWAI_SHA256"]==digest)
ck("no_promoted_preview_approval",collection["FWAI_APPROVED"] is False)
ck("no_geometry_outside_6ft5in_box",all(max((v.z for v in (fw.triplet(pt,"coord") for pt in p["points"])),default=0)<=1.9558 for p in asset["parts"]))
# Verify new shell remains parented to animated mechanical controls.
scene.frame_set(1)
shell=bpy.data.objects[fw.PREFIX+"L_bicep_shell"]
position1=shell.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation.copy()
scene.frame_set(36)
position2=shell.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation.copy()
ck("dynamic_bone_moves_new_upperarm_shell",(position2-position1).length>.00001)
sc=scene
sc.render.resolution_x=1280;sc.render.resolution_y=720;sc.render.resolution_percentage=100
sc.render.image_settings.file_format="PNG"
path=OUT/"VQ04_02_V2_IDENTITY_PREVIEW.png";sc.render.filepath=str(path)
bpy.ops.render.render(write_still=True)
ck("rendered_real_blender_image",path.stat().st_size>15000)
ck("replace_preview_without_duplicating",("70" in fw.load(command)) and len(bpy.data.collections[fw.COL].objects)==70)
ck("inspect_reports_live_count","70" in fw.inspect())
removed=fw.clear()
ck("remove_only_staged_preview",(fw.COL not in bpy.data.collections) and len(bpy.data.objects)==len(original_names))
ck("clear_idempotent","No identity" in fw.clear())
ck("original_scene_bytes_unchanged",hashlib.sha256(source.read_bytes()).hexdigest()==source_hash)
data={"schema":"FWAI_VQ04_02_IDENTITY_ENGINEERING_V1","tests":tests,"passed":sum(tests.values()),"total":len(tests),
      "passed_all":all(tests.values()),"canonical_sha":fw.MASTER_SHA,"source_scene_sha":source_hash,
      "image_sha":hashlib.sha256(path.read_bytes()).hexdigest(),"artistic_approval":False,
      "accurate_3d_character_reproduction":False,"runway_calls":0}
(OUT/"VQ04_02_TESTS.json").write_text(json.dumps(data,indent=2))
print("FWAI_VQ04_02_IDENTITY_TESTS",data["passed"],data["total"], "PASS" if data["passed_all"] else "FAIL")
