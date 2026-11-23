"""Prepare on-machine GUI review: frame 36, camera mode, external unchanged reference images."""
import bpy,json,hashlib,sys
from pathlib import Path
out=Path(sys.argv[sys.argv.index("--")+1])
root=Path.home()/"Documents"/"futureworks-p04-data"
refs={
  "REFERENCE | FWAI-M001 Approved V2":"character-library/FWAI-M001/v2.0/FWAI-M001_APPROVED_FINAL_MASTER_V2.0.png",
  "REFERENCE | Nissan approved stage":"FWAI-M001_EP001_PREPRODUCTION/05_LOCAL_KEYFRAMES/S01/candidate_D4_env_crop/FWAI_EP001_S01_LOCAL_REFERENCE_CANDIDATE_1024x576.png"}
for label,path in refs.items():
    f=root/path
    if not f.is_file():raise RuntimeError("Missing canonical external reference: "+str(f))
    img=bpy.data.images.load(str(f),check_existing=True)
    img.name=label;img.use_fake_user=True
scene=bpy.context.scene
scene.frame_set(36)
for area in bpy.context.screen.areas:
    if area.type=="VIEW_3D":
        area.spaces.active.region_3d.view_perspective="CAMERA"
        area.spaces.active.show_region_ui=True
        area.spaces.active.overlay.show_floor=True
        area.spaces.active.shading.type="MATERIAL" if False else "SOLID"
rig=bpy.data.objects.get("FWAI-M001 / 6ft5in RIG / VQ03")
bpy.ops.object.select_all(action="DESELECT")
rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.wm.save_as_mainfile(filepath=str(out/"FWAI_VQ03_MECH_NISSAN_VINYL.blend"))
manifest=json.loads((out/"VQ03_PROOF_MANIFEST.json").read_text())
manifest["blend_sha256"]=hashlib.sha256((out/manifest["blend"]).read_bytes()).hexdigest()
manifest["view_in_blender_gui"]="Camera view, frame 36; choose frame 1/36/72 from timeline; IK target empties can be manipulated."
manifest["reference_images_loaded_without_mutation"]=list(refs.keys())
(out/"VQ03_PROOF_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
print("FWAI_VQ03_GUI_READY",scene.frame_current,len(bpy.data.images))
