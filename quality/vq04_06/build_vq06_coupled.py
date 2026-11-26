"""VQ04.06: wrist/index-driven native Blender cloth bake, no paid tools.

Create a separate developer proof .blend and disk-backed Blender point cache.
This scene uses VQ04.04's 425-vertex 0.25-mm partial-door film as rest geometry.
Pinned adhesive-edge vertices stay close to the door. The loose edge is moved by
a controlled Hook target BEFORE the cloth modifier, which computes intermediate
un-pinned vertices. This is *a real numerical cloth simulation*, but does NOT
yet implement adhesive peel forces, measured vinyl material parameters, full
mech-hand contact or accurate 370Z CAD.

Never rewrite the approved canonical images or VQ04.04 source scene.
"""
import bpy, math, sys, json, hashlib
from pathlib import Path
from mathutils import Vector, Matrix
root=Path.home()/"Documents"/"futureworks-vq04-06"
root.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(Path.home()/"Documents"/"futureworks-vq04-04"))
import fwai_film_contact as prior
MASTER=prior.MASTER
EXPECTED=prior.MASTER_SHA
assert MASTER.is_file() and hashlib.sha256(MASTER.read_bytes()).hexdigest()==EXPECTED
sc=bpy.context.scene
assert sc.unit_settings.system=="METRIC"
assert bpy.data.objects.get("NISSAN / door passenger") is not None
assert bpy.data.objects.get(prior.SOURCE) is not None
assert sc.frame_current>=1
sc.render.fps=24
sc.frame_start=1
sc.frame_end=72
sc.gravity=(0,0,-9.81)
collection=bpy.data.collections.new("FWAI VQ04.06 / COUPLED CLOTH / NOT APPROVED")
sc.collection.children.link(collection)
# Original visual sheet remains untouched and is hidden only in the NEW derivative scene.
orig=bpy.data.objects[prior.SOURCE]
orig.hide_render=True
orig.hide_set(True)
# Mesh follows VQ04.04 approved 0.25mm study topology but with shape keys REMOVED:
# all movement after frame1 is computed by Cloth.
verts=prior.grid(1)
quads=[]
for j in range(prior.NZ-1):
    for i in range(prior.NX-1):
        a=j*prior.NX+i
        quads.append((a,a+1,a+1+prior.NX,a+prior.NX))
mesh=bpy.data.meshes.new("FWAI 05 / 425-vertex physical film mesh")
mesh.from_pydata(verts,[],quads)
mesh.update()
sheet=bpy.data.objects.new("FWAI VQ04.06 / HAND-COUPLED FILM",mesh)
collection.objects.link(sheet)
# Dark satin charcoal wrap, matching EP001's locked creative direction;
# independent study material, not owner-approved final-grade material.
mat=bpy.data.materials.new("FWAI VQ04.06 / charcoal-satin vinyl")
mat.diffuse_color=(.065,.067,.074,1.0)
mat.use_nodes=True
node=mat.node_tree.nodes.get("Principled BSDF")
node.inputs["Base Color"].default_value=(.065,.067,.074,1)
node.inputs["Metallic"].default_value=.02
node.inputs["Roughness"].default_value=.46
node.inputs["Coat Weight"].default_value=.34
node.inputs["Coat Roughness"].default_value=.29
sheet.data.materials.append(mat)
sheet["FWAI_CANONICAL_SHA256"]=EXPECTED
sheet["FWAI_OWNER_APPROVED"]=False
sheet["FWAI_VISUAL_PROXY"]=True
sheet["FWAI_MATERIAL_CALIBRATED"]=False
sheet["FWAI_FILM_THICKNESS_M"]=.00025
sheet["FWAI_CLOTH_SOLVER"]="BLENDER_CLOTH"
# Vertex groups: adhesive edge pinned to the source panel without advancing
# adhesion through time; moving leftmost column is hooked to a controlled grip.
pin=sheet.vertex_groups.new(name="FWAI / PIN ADHERED + GRIPPED")
loose=sheet.vertex_groups.new(name="FWAI / GRIP CONTROL EDGE")
anchored=[]
free=[]
for j in range(prior.NZ):
    for i in range(prior.NX):
        idx=j*prior.NX+i
        if i>=15:anchored.append(idx)
        if i==0:free.append(idx)
pin.add(anchored+free,1.0,"REPLACE")
loose.add(free,1.0,"REPLACE")
# Moving hook target is placed at origin; identity bind matrix means its motion
# is an additive displacement on the loose-edge mesh vertices.
control=bpy.data.objects.new("FWAI VQ04.06 / FOLLOW R INDEX TIP DRIVER",None)
collection.objects.link(control)
control.empty_display_type="SPHERE"
control.empty_display_size=.045
control.hide_render=True
control.location=(0,0,0)
for frame,location in [(1,(0,0,0)),(36,(.015,.058,.014)),(72,(.095,.165,-.022))]:
    control.location=location
    control.keyframe_insert(data_path="location",frame=frame,group="VQ04.05 CONTROLLED GRIP")
hook=sheet.modifiers.new("FWAI / move free edge BEFORE cloth","HOOK")
hook.object=control
hook.vertex_group=loose.name
hook.strength=1
hook.matrix_inverse=Matrix.Identity(4)
# Real physically integrated COLLISION proxy (duplicate, NOT original door).
# Plane front face exactly -0.379m, thick enough to catch a numerical cloth.
xmin,xmax=-.47,.93
yfront,yrear=-.379,-.340
zmin,zmax=.41,1.03
points=[
(xmin,yfront,zmin),(xmax,yfront,zmin),(xmax,yfront,zmax),(xmin,yfront,zmax),
(xmin,yrear,zmin),(xmax,yrear,zmin),(xmax,yrear,zmax),(xmin,yrear,zmax)
]
faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(1,2,6,5),(0,4,7,3)]
col_mesh=bpy.data.meshes.new("FWAI / stationary door collision box mesh")
col_mesh.from_pydata(points,[],faces);col_mesh.update()
door=bpy.data.objects.new("FWAI VQ04.06 / STATIONARY DOOR COLLIDER",col_mesh)
collection.objects.link(door)
col=door.modifiers.new("FWAI / door surface collision","COLLISION")
door.collision.thickness_outer=.002
door.collision.cloth_friction=5
door.hide_render=True
door.hide_set(False)
door.display_type="WIRE"
# Real Blender cloth modifier. It solves unpinned vertices in world gravity.
cloth=sheet.modifiers.new("FWAI / REAL BLENDER CLOTH","CLOTH")
s=cloth.settings
s.quality=6
s.mass=.075
s.tension_stiffness=18
s.compression_stiffness=20
s.shear_stiffness=12
s.bending_stiffness=.42
s.tension_damping=4
s.compression_damping=4
s.shear_damping=4
s.bending_damping=.4
s.air_damping=1
s.vertex_group_mass=pin.name
s.pin_stiffness=1
collision=cloth.collision_settings
collision.use_collision=True
collision.collision_quality=5
collision.distance_min=.003
collision.use_self_collision=False
cache=cloth.point_cache
cache.frame_start=1
cache.frame_end=72
cache.name="FWAI_VQ04_06_V2"
cache.use_disk_cache=True
# Physically thin visible film, evaluated only AFTER cloth simulation.
solid=sheet.modifiers.new("FWAI / 0.25mm render thickness AFTER cloth","SOLIDIFY")
solid.thickness=.00025
solid.offset=0
# VQ04.06 PROOF: the free edge is no longer controlled by unrelated
# keyframes. It follows the REAL Blender R-index tip attached to mech rig.
# Fit its animated IK proxy to the front of the TOP-LEFT film corner at f1.
# This is an exact geometric parent constraint, NOT a force/friction grip.
sys.path.insert(0,str(Path.home()/"Documents"/"futureworks-vq04-03"))
import fwai_hand_tool_preview as hands
sc.frame_set(1)
hands.load()
sc.frame_set(1)
rig=bpy.data.objects[hands.RIG]
old_target=bpy.data.objects["IK TARGET / R HAND"]
constraints=[c for pb in rig.pose.bones for c in pb.constraints
             if c.type=="IK" and c.target==old_target]
if len(constraints)!=1:raise RuntimeError("Unexpected R-hand IK constraint")
ik=constraints[0]
indexpad=bpy.data.objects["FWAI GRIP / R_index_fingerpad"]
proxy=bpy.data.objects.new("FWAI VQ04.06 / R-hand IK fitted target",None)
collection.objects.link(proxy)
proxy.matrix_world=old_target.matrix_world.copy()
proxy.hide_render=True
ik.target=proxy
target=Vector(prior.grid(1)[16*prior.NX])+Vector((0,-.0143,0))
for iteration in range(30):
    bpy.context.view_layer.update()
    actual=indexpad.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation.copy()
    error=target-actual
    if error.length<.002:break
    proxy.location+=error*.7
if error.length>=.0025:
    raise RuntimeError("Initial R finger cannot reach top-left film corner "+str(error.length))
fit_error=float(error.length)
# Follow native IK animation with a constant fitted transform offset.
# Parent inverse preserves the calibrated pose at f1.
fit_matrix=proxy.matrix_world.copy()
proxy.parent=old_target
proxy.matrix_parent_inverse=old_target.matrix_world.inverted()
proxy.matrix_world=fit_matrix
bpy.context.view_layer.update()
recovered=indexpad.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation.copy()
if (recovered-target).length>.004:
    raise RuntimeError("IK fit shifted during proxy parenting")
# Original stand-alone Hook path is removed from this derivative only.
# Its world-space grip motion now comes from the rigged index-pad transform.
control.animation_data_clear()
initial_control=control.matrix_world.copy()
control.parent=indexpad
control.matrix_parent_inverse=indexpad.matrix_world.inverted()
control.matrix_world=initial_control
bpy.context.view_layer.update()
if control.matrix_world.translation.length>.002:
    raise RuntimeError("Hook driver changed rest position while parenting")
sheet["FWAI_GRIP_DRIVER"]="MECH / R_index_fingerpad"
sheet["FWAI_GRIP_DRIVER_IS_KINEMATIC"]=True
sheet["FWAI_FORCE_CONTACT_CERTIFIED"]=False
sheet["FWAI_INITIAL_PINCH_PAD_TARGET_GAP_M"]=fit_error
# Lock latest approved OWNER image as a separate, higher-priority visual
# reference than the older V2 concept board. Neither source is modified.
latest=Path.home()/"Documents"/"futureworks-p04-comfyui"/"output"/"FWAI_M001_LOCKED_V2_CHARACTER_KEYFRAME_00002_.png"
latest_sha="5dcefd9309510754d7b5dd5dd549eae6f3244d1a4a3b6f9056c2055d620ba12b"
if not latest.exists() or hashlib.sha256(latest.read_bytes()).hexdigest()!=latest_sha:
    raise RuntimeError("Latest owner-approved M001 visual master SHA mismatch")
sheet["FWAI_LATEST_OWNER_MASTER_SHA"]=latest_sha
# Keep separate SOURCE unaltered. Create a new artifact file.
sc.frame_set(1)
bpy.context.view_layer.objects.active=sheet
sheet.select_set(True)
path=root/"scene"/"FWAI_VQ04_06_COUPLED_CLOTH_BAKED_V2.blend"
path.parent.mkdir(exist_ok=True,parents=True)
# This standalone builder is an isolated one-time creation step.
# Fail closed on rerun: never overwrite a baked derivative or its disk cache.
if path.exists() or (path.parent/("blendcache_"+path.stem)).exists():
    raise RuntimeError("Destination VQ04.06 derivative exists; refusing overwrite/rebake")
bpy.ops.wm.save_as_mainfile(filepath=str(path))
# Need bake context with active object + explicit point_cache context.
bpy.ops.object.select_all(action="DESELECT")
sheet.select_set(True)
bpy.context.view_layer.objects.active=sheet
print("FWAI_VQ05_BAKE_BEGIN","vertices",len(sheet.data.vertices),
      "cloth",cloth.type,"pin",s.vertex_group_mass,
      "hook_first",sheet.modifiers[0].type,"cache",cache.frame_start,cache.frame_end,
      "blend",str(path),flush=True)
try:
    with bpy.context.temp_override(point_cache=cache,object=sheet,active_object=sheet):
        result=bpy.ops.ptcache.bake(bake=True)
    print("FWAI_VQ05_BAKE_OPERATOR",str(result),flush=True)
except Exception as ex:
    print("FWAI_VQ05_BAKE_ERROR",type(ex).__name__,str(ex),flush=True)
    raise
print("FWAI_VQ05_BAKE_STATUS","baked",cache.is_baked,"frames",cache.frame_start,cache.frame_end,flush=True)
if not cache.is_baked:
    raise RuntimeError("Point cache bake was not confirmed")
# Save the derivative so reopened scene references its disk cache.
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(path))
manifest={
  "schema":"FWAI_VQ04_06_COUPLED_BAKE_PROOF_V1",
  "scene":str(path),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
  "cache_is_baked":bool(cache.is_baked),
  "frames":[1,36,72],"frame_start":cache.frame_start,"frame_end":cache.frame_end,
  "film_vertices":len(sheet.data.vertices),"quads":len(quads),
  "modifier_order":[x.type for x in sheet.modifiers],
  "pin_adhered_vertices":len(anchored),
  "pin_gripper_vertices":len(free),
  "clamped_film_surface_thickness_m":.00025,
  "source_image_sha256":EXPECTED,
  "master_unchanged":hashlib.sha256(MASTER.read_bytes()).hexdigest()==EXPECTED,
  "physical_cloth_solver_used":True,
  "calibrated_real_vinyl_material":False,
  "adhesive_strength_tested":False,"full_hand_grip_tested":False,"cinema_approved":False
}
out=root/"evidence"
out.mkdir(exist_ok=True,parents=True)
(out/"VQ04_06_COUPLED_BAKE_MANIFEST_V2.json").write_text(json.dumps(manifest,indent=2))
print("FWAI_VQ05_BAKE_COMPLETE",json.dumps(manifest),flush=True)
