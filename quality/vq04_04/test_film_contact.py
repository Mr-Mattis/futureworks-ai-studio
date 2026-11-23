"""VQ04.04 independent 0.25mm vinyl partial-door/collision proxy tests.

All proof remains 3D geometric/kinematic. Not a Blender cloth bake.
"""
from pathlib import Path
import bpy,sys,json,hashlib,math
ROOT=Path.home()/"Documents"/"futureworks-vq04-04"
OUT=ROOT/"evidence";OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT))
import fwai_film_contact as film
src=Path(bpy.data.filepath);srcsha=hashlib.sha256(src.read_bytes()).hexdigest()
source=bpy.data.objects[film.SOURCE]
door=bpy.data.objects[film.DOOR]
orig_hide=(source.hide_get(),source.hide_render)
orig_door=[tuple(round(x,6) for x in door.matrix_world@v.co) for v in door.data.vertices]
original=set(bpy.data.objects)
test={}
def ck(n,v):
 test[n]=bool(v)
 if not v:raise AssertionError(n)
ck("locked_character_sha",hashlib.sha256(film.MASTER.read_bytes()).hexdigest()==film.MASTER_SHA)
ck("source_film_is_present",film.SOURCE in bpy.data.objects)
ck("film_is_independent",film.NAME not in bpy.data.objects)
ck("metric_thinfilm_250microns",film.THICKNESS_M==0.00025)
ck("sheet_narrower_than_door",film.FILM_MAX_X - film.ADHERED_FROM_X <1.4)
ck("patch_height_smaller_than_door",film.FILM_MAX_Z-film.FILM_MIN_Z<.62)
diagnostics={}
for f in film.STAGES:
 data=film.diagnose(f)
 diagnostics[str(f)]=data
 ck("no_door_penetration_frame"+str(f),data["door_penetrating_vertices"]==0)
 ck("door_clearance_atleast_1p1mm_frame"+str(f),data["min_door_clearance_m"]>=.00109)
 ck("door_coverage_under_45percent_frame"+str(f),data["door_projected_coverage_fraction_upper_estimate"]<.45)
 ck("anchored_clearance_bounded_frame"+str(f),data["anchored_clearance_max_m"]<.025)
ck("no_replacement_of_legacy_film",source==bpy.data.objects[film.SOURCE])
msg=film.load()
preview=bpy.data.objects[film.NAME]
ck("three_film_phases_keyed",preview.data.shape_keys is not None and len(preview.data.shape_keys.key_blocks)==4)
ck("mesh_425_vertices",len(preview.data.vertices)==425 and "425" in msg)
ck("source_film_hidden_for_review",source.hide_get() and source.hide_render)
ck("thinfilm_real_solidify_modifier",any(m.type=="SOLIDIFY" and abs(m.thickness-.00025)<1e-8 for m in preview.modifiers))
ck("preview_film_not_approved",preview["FWAI_APPROVED"] is False and preview["FWAI_NOT_BAKED_CLOTH"] is True)
# Check evaluated vertex positions follow the authored three keyframed phases.
for stage in film.STAGES:
 bpy.context.scene.frame_set(stage)
 ev=preview.evaluated_get(bpy.context.evaluated_depsgraph_get())
 raw=film.grid(stage)
 ck("evaluated_frame"+str(stage)+"_matches_shape",abs((ev.data.vertices[0].co.x)-raw[0][0])<.00005)
ck("prior_scene_objects_preserved",original.issubset(set(bpy.data.objects)))
ck("nissan_vertex_geometry_identical",orig_door==[tuple(round(x,6) for x in door.matrix_world@v.co) for v in door.data.vertices])
# Camera: original scene camera, preview film only. Keep source .blend unsaved.
sc=bpy.context.scene;sc.frame_set(36)
sc.render.resolution_x=1280;sc.render.resolution_y=720;sc.render.resolution_percentage=100
sc.render.image_settings.file_format="PNG"
im=OUT/"VQ04_04_PARTIAL_DOOR_FILM.png";sc.render.filepath=str(im)
bpy.ops.render.render(write_still=True)
ck("render_generated",im.is_file() and im.stat().st_size>12000)
ck("load_idempotent","425" in film.load())
try:film.set_stage(45);bad=False
except ValueError:bad=True
ck("arbitrary_film_stages_rejected",bad)
ck("correct_film_stage_selection","REACH" in film.set_stage(36))
ck("clear_restores_legacy_film","restored" in film.clear())
ck("legacy_film_hide_flags_restored",(source.hide_get(),source.hide_render)==orig_hide)
ck("preview_collection_removed",film.COL not in bpy.data.collections)
ck("source_scene_sha_unchanged",hashlib.sha256(src.read_bytes()).hexdigest()==srcsha)
result={"schema":"FWAI_VQ04_04_FILM_TEST_V1","tests":test,"passed":sum(test.values()),"total":len(test),
 "all_pass":all(test.values()),"diagnostics":diagnostics,
 "source_blend_sha256":srcsha,"render_sha256":hashlib.sha256(im.read_bytes()).hexdigest(),
 "cloth_baked":False,"physical_grip_verified":False,"adhesion_load_verified":False,"creative_approved":False}
(OUT/"VQ04_04_FILM_TESTS.json").write_text(json.dumps(result,indent=2))
print("FWAI_VQ04_04_FILM_TESTS",result["passed"],result["total"],result["all_pass"])
print("FWAI_VQ04_04_DOOR_COVERAGE",json.dumps({s:v["door_projected_coverage_fraction_upper_estimate"] for s,v in diagnostics.items()}))
