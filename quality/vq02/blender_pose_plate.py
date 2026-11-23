"""Generate a deterministic articulated mech blocking/pose plate in Blender.
Run: blender --background --factory-startup --python blender_pose_plate.py -- OUTPUT_DIR
No paid provider requests, no changes to approved source assets.
"""
import bpy, math, sys, json, hashlib
from pathlib import Path
from mathutils import Vector
out = Path(sys.argv[sys.argv.index("--")+1]) if "--" in sys.argv else Path.cwd()
out.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine="BLENDER_EEVEE"
scene.render.resolution_x=1024
scene.render.resolution_y=576
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGBA"
scene.render.film_transparent=True
scene.world.color=(0.08,0.08,0.08)
def wp(px,py,z=0):
    return Vector(((px-512)/100.0,(288-py)/100.0,z))
def mat(name,rgb,metallic=0.1):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*rgb,1)
    m.use_nodes=True
    bsdf=m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value=(*rgb,1)
    bsdf.inputs["Metallic"].default_value=metallic
    bsdf.inputs["Roughness"].default_value=0.34
    return m
armor=mat("plum anodized aluminum",(.24,.085,.32),.75)
dark=mat("machined graphite joint",(.035,.044,.052),.68)
cyan=mat("cyan tool orientation",(.04,.70,.88),.3)
def sphere(name, p, radius, material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=radius,location=p)
    o=bpy.context.object
    o.name=name;o.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return o
def limb(name,p1,p2,width,material):
    a,b=wp(*p1),wp(*p2)
    midpoint=(a+b)/2
    diff=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=width/200,depth=diff.length,location=midpoint)
    obj=bpy.context.object
    obj.name=name
    obj.rotation_euler=diff.to_track_quat("Z","Y").to_euler()
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return obj
# Pose coordinates are pixel-space blocking targets, not a factual reconstruction.
POSE={
 "hips":[(194,291),(228,291)],
 "left_leg":[(194,291),(156,383),(176,487),(214,508)],
 "right_leg":[(228,291),(269,385),(282,483),(313,508)],
 "left_arm":[(200,185),(272,230),(341,284)],
 "right_arm":[(235,187),(312,234),(398,277)]
}
# A real armature with independently editable limb bones, not only a sketch.
bpy.ops.object.armature_add(enter_editmode=True,location=(0,0,0))
rig=bpy.context.object
rig.name="FWAI_M001_POSE_CONTROL_RIG"
arm=rig.data
for bone in list(arm.edit_bones):arm.edit_bones.remove(bone)
for path in ("left_leg","right_leg","left_arm","right_arm"):
    nodes=POSE[path]
    for i,(a,b) in enumerate(zip(nodes,nodes[1:])):
        eb=arm.edit_bones.new(path+"_"+str(i))
        eb.head=wp(*a);eb.tail=wp(*b)
        if i>0:eb.parent=arm.edit_bones[path+"_"+str(i-1)]
bpy.ops.object.mode_set(mode="OBJECT")
for path in ("left_leg","right_leg","left_arm","right_arm"):
    nodes=POSE[path]
    for i,(a,b) in enumerate(zip(nodes,nodes[1:])):
        obj=limb(path+"_"+str(i),a,b,16 if "leg" in path else 12,armor)
        current_world=obj.matrix_world.copy()
        obj.parent=rig
        obj.parent_type="BONE"
        obj.parent_bone=path+"_"+str(i)
        obj.matrix_world=current_world
    for i,p in enumerate(nodes[1:-1]):
        joint=sphere(path+"_joint_"+str(i),wp(*p,0.015),.14,dark)
        world=joint.matrix_world.copy()
        joint.parent=rig; joint.parent_type="BONE"; joint.parent_bone=path+"_"+str(i)
        joint.matrix_world=world
    tip=sphere(path+"_endpoint",wp(*nodes[-1],0.028),.095,cyan)
    world=tip.matrix_world.copy()
    tip.parent=rig; tip.parent_type="BONE"; tip.parent_bone=path+"_"+str(len(nodes)-2)
    tip.matrix_world=world
for path in ("left_leg","right_leg"):
    toe=POSE[path][-1]
    sphere(path+"_floor_contact",wp(*toe,0.02),.14,dark)
# Wide stance body anchor and mechanical links.
limb("pelvic_pose_anchor",(194,291),(228,291),29,dark)
sphere("mech_hip_left",wp(194,291,.04),.18,armor)
sphere("mech_hip_right",wp(228,291,.04),.18,armor)
# Camera directly aligns orthographically to existing 1024x576 shot.
bpy.ops.object.camera_add(location=(0,0,12))
camera=bpy.context.object
camera.name="CAMERA_LOCKED_PIXEL_FRAME"
camera.data.type="ORTHO"
camera.data.ortho_scale=10.24
scene.camera=camera
# Blender camera looks local -Z, mapped picture Y points upwards.
bpy.ops.object.light_add(type="AREA",location=(0,2,6))
bpy.context.object.data.energy=750
bpy.context.object.data.shape="DISK"
bpy.context.object.data.size=9
scene.render.filepath=str(out/"BL01_mech_pose_overlay.png")
bpy.ops.wm.save_as_mainfile(filepath=str(out/"BL01_mech_pose.blend"))
bpy.ops.render.render(write_still=True)
original_sha=hashlib.sha256((out/"BL01_mech_pose_overlay.png").read_bytes()).hexdigest()
# Actual rig test: moving a pose bone must move its parented visible mesh.
rig.pose.bones["left_leg_1"].rotation_mode="XYZ"
rig.pose.bones["left_leg_1"].rotation_euler.z=math.radians(22)
bpy.context.view_layer.update()
scene.render.filepath=str(out/"BL01_mech_pose_variant.png")
bpy.ops.render.render(write_still=True)
variant_sha=hashlib.sha256((out/"BL01_mech_pose_variant.png").read_bytes()).hexdigest()
if original_sha==variant_sha:raise RuntimeError("Pose rig movement did not change rendered geometry")
rig.pose.bones["left_leg_1"].rotation_euler.z=0
manifest={"schema":"FWAI_BL01_BLOCKING_V1","pose_pixels":POSE,"resolution":[1024,576],
 "rig_object":rig.name,"camera":camera.name,"render":"BL01_mech_pose_overlay.png",
 "purpose":"mech pose blocking only; not verified real-world engineering or finished photorealism",
 "render_sha256":original_sha,"variant_render_sha256":variant_sha,"rig_drives_mesh_verified":True}
(out/"BL01_pose_manifest.json").write_text(json.dumps(manifest,indent=2))
print("FWAI_BL01_COMPLETE",str(out),manifest["render_sha256"])
