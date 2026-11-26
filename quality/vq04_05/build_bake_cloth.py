"""VQ04.05: isolated native Blender CLOTH + COLLISION bake, no paid tools.

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
root=Path.home()/"Documents"/"futureworks-vq04-05"
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
collection=bpy.data.collections.new("FWAI VQ04.05 / CLOTH PROOF / NOT APPROVED")
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
sheet=bpy.data.objects.new("FWAI VQ04.05 / SOLVER FILM",mesh)
collection.objects.link(sheet)
sheet.data.materials.append(prior._material())
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
        if i>=16:anchored.append(idx)
        if i==0:free.append(idx)
pin.add(anchored+free,1.0,"REPLACE")
loose.add(free,1.0,"REPLACE")
# Moving hook target is placed at origin; identity bind matrix means its motion
# is an additive displacement on the loose-edge mesh vertices.
control=bpy.data.objects.new("FWAI VQ04.05 / UNANIMATED SOURCE GRIP DRIVER",None)
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
door=bpy.data.objects.new("FWAI VQ04.05 / STATIONARY DOOR COLLIDER",col_mesh)
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
cache.name="FWAI_VQ04_05"
cache.use_disk_cache=True
# Physically thin visible film, evaluated only AFTER cloth simulation.
solid=sheet.modifiers.new("FWAI / 0.25mm render thickness AFTER cloth","SOLIDIFY")
solid.thickness=.00025
solid.offset=0
# Keep separate SOURCE unaltered. Create a new artifact file.
sc.frame_set(1)
bpy.context.view_layer.objects.active=sheet
sheet.select_set(True)
path=root/"scene"/"FWAI_VQ04_05_CLOTH_BAKED.blend"
path.parent.mkdir(exist_ok=True,parents=True)
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
  "schema":"FWAI_VQ04_05_BAKE_PROOF_V1",
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
(out/"VQ04_05_BAKE_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
print("FWAI_VQ05_BAKE_COMPLETE",json.dumps(manifest),flush=True)
