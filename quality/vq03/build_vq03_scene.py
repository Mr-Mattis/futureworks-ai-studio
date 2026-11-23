"""FWAI VQ03: physically scaled mech blocking, 370Z proxy, vinyl sheet and three poses.
Blender 5.3, no external dependencies, no paid services, no source media overwritten.
The car and mech are *proxies*; official 2D character/car references remain immutable.
"""
import bpy, math, json, hashlib, sys, os
from pathlib import Path
from mathutils import Vector
OUT=Path(sys.argv[sys.argv.index("--")+1]) if "--" in sys.argv else Path.cwd()
OUT.mkdir(exist_ok=True,parents=True)
HEIGHT=1.9558  # 6 ft 5 in; true Blender metric units
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.unit_settings.scale_length=1.0
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1280
scene.render.resolution_y=720
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.render.film_transparent=False
scene.world.color=(0.09,0.11,0.15)
scene.frame_start=1;scene.frame_end=72;scene.render.fps=24
def material(name,c,metal=.0,rough=.4,alpha=1,emit=None):
    m=bpy.data.materials.new(name);m.diffuse_color=(*c,alpha)
    m.use_nodes=True;bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*c,1)
    bs.inputs["Metallic"].default_value=metal;bs.inputs["Roughness"].default_value=rough
    bs.inputs["Alpha"].default_value=alpha
    if emit:
        bs.inputs["Emission Color"].default_value=(*emit,1)
        bs.inputs["Emission Strength"].default_value=3
    return m
plum=material("FWAI canonical obsidian-plum | indicative proxy",(.20,.025,.26),.83,.24)
titanium=material("Machined titanium alloy",(.39,.44,.5),.85,.25)
joint=material("Graphite ceramic actuators",(.025,.03,.045),.65,.34)
cyan=material("Plasma cyan light channel",(.018,.48,.68),.22,.24,emit=(.0,.8,1.0))
white=material("Nissan pearlescent white | proxy",(.78,.81,.84),.45,.22)
glass=material("Automotive tinted glazing",(.016,.037,.05),.47,.12)
tire=material("Tire rubber",(.015,.016,.018),.03,.78)
red=material("Brake caliper red",(.55,.01,.015),.64,.30)
film=material("Satin charcoal flexible automotive vinyl",(.012,.017,.022),.0,.68)
floor=material("Workshop polished concrete",(.09,.105,.12),.22,.33)
steel=material("Workshop industrial steel",(.13,.16,.19),.5,.36)
def box(n,at,size,mat,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=at)
    ob=bpy.context.object;ob.name=n
    ob.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.data.materials.append(mat)
    if bevel:
        mod=ob.modifiers.new("Machined bevel","BEVEL");mod.width=bevel;mod.segments=2
        ob.modifiers.new("Weighted normal","WEIGHTED_NORMAL")
    return ob
def sphere(n,at,r,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=r,location=at)
    o=bpy.context.object;o.name=n;o.data.materials.append(mat)
    bpy.ops.object.shade_smooth();return o
def rod(n,a,b,r,mat):
    v=Vector(b)-Vector(a)
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r, depth=v.length, location=(Vector(a)+Vector(b))/2)
    o=bpy.context.object;o.name=n;o.rotation_euler=v.to_track_quat("Z","Y").to_euler();o.data.materials.append(mat)
    bpy.ops.object.shade_smooth();return o
# Workshop shell
box("WORKSHOP / floor",(.3,.2,-.085),(9,7,.14),floor)
box("WORKSHOP / rear wall",(.5,2.4,2),(9,.10,4),steel)
for x in (-3.5,-1.3,1.1,3.35):
    rod("WORKSHOP / rear girder",(x,2.28,0),(x,2.28,3.7),.045,titanium)
for x in (-2.7,0,2.7):
    lamp=box("WORKSHOP / lightpanel",(x,-.9,3.4),(1.5,.13,.075),cyan,.02)
# Keep a camera-visible full car proxy: source photo (D4) remains unchanged outside this asset.
# These dimensions are blocking estimates, NOT sourced Nissan factory CAD.
car_length=4.25;wheelbase=2.55
box("NISSAN / sill body proxy",(.52,.58,.58),(car_length,1.70,.68),white,.19)
box("NISSAN / long hood",(1.75,.58,.90),(1.66,1.64,.18),white,.12)
box("NISSAN / roof",(0.06,.67,1.19),(1.63,1.51,.28),white,.23)
box("NISSAN / side window glazing",(-.04,-.18,1.26),(1.42,.040,.22),glass,.035)
box("NISSAN / door passenger",(.23,-.360,.72),(1.40,.038,.62),white,.085)
box("NISSAN / side skirt",(.16,-.31,.25),(2.38,.12,.14),joint,.04)
box("NISSAN / front bumper",(2.55,.58,.49),(.33,1.68,.49),white,.11)
box("NISSAN / rear bumper",(-1.52,.58,.52),(.32,1.68,.45),white,.09)
box("NISSAN / undercarriage",(.5,.6,.24),(3.85,1.34,.26),joint,.05)
for x in (-.9,1.65):
    for y in (-.39,1.53):
        rod("NISSAN / wheel axle marker",(x,y-.06,.42),(x,y+.06,.42),.30,tire)
        rod("NISSAN / rim hub",(x,y-.09,.42),(x,y+.09,.42),.19,titanium)
        sphere("NISSAN / center cap",(x,y-.17,.42),.055,joint)
# Collision proxy matches passenger door; deliberately separate from visible car.
collision=box("COLLISION / passenger door",(.23,-.386,.75),(1.40,.035,.69),white)
collision.hide_render=True
collision.display_type='WIRE'
collision.modifiers.new("Door surface collision","COLLISION")
# Metric 6 ft 5 in mech -- hips + shoulders, helmet reaches HEIGHT exactly
mx=-1.93;my=-.86
hip_z=1.025;shoulder_z=1.535
hip=(mx,my,hip_z)
# Real armature controlling named mechanical limbs
bpy.ops.object.armature_add(enter_editmode=True,location=(0,0,0))
rig=bpy.context.object;rig.name="FWAI-M001 / 6ft5in RIG / VQ03";arm=rig.data
for b in list(arm.edit_bones):arm.edit_bones.remove(b)
def make_bone(name,a,b,parent=None):
    e=arm.edit_bones.new(name);e.head=a;e.tail=b
    if parent:e.parent=arm.edit_bones[parent];e.use_connect=False
    return e
make_bone("pelvis",(mx,my,hip_z),(mx,my,hip_z+.19))
make_bone("spine",(mx,my,hip_z+.19),(mx-.015,my,shoulder_z),"pelvis")
make_bone("neck",(mx-.015,my,shoulder_z),(mx-.02,my,1.74),"spine")
make_bone("helmet",(mx-.02,my,1.74),(mx+.01,my,HEIGHT),"neck")
for side,offset in (("L",-.16),("R",.16)):
    yy=my+offset
    make_bone(side+"_thigh",(mx,yy,hip_z),(mx+.035,yy,.58),"pelvis")
    make_bone(side+"_shin",(mx+.035,yy,.58),(mx+.09,yy,.17),side+"_thigh")
    make_bone(side+"_foot",(mx+.09,yy,.17),(mx+.29,yy,.075),side+"_shin")
    # Shoulder -> elbow -> wrist in front of passenger door
    shoulder=(mx+.05,yy,shoulder_z)
    elbow=(mx+.35,yy,1.40)
    wrist=(mx+.65,yy,1.19)
    make_bone(side+"_upperarm",shoulder,elbow,"spine")
    make_bone(side+"_forearm",elbow,wrist,side+"_upperarm")
    make_bone(side+"_hand",wrist,(wrist[0]+.13,wrist[1],wrist[2]-.025),side+"_forearm")
bpy.ops.object.mode_set(mode="OBJECT")
def bind_bone(ob,bone):
    mw=ob.matrix_world.copy()
    ob.parent=rig;ob.parent_type="BONE";ob.parent_bone=bone;ob.matrix_world=mw
# Visible authored mech parts are articulated rather than re-generated.
for side,offset in (("L",-.16),("R",.16)):
    yy=my+offset
    for bn,a,b,r,material_ in (
        (side+"_thigh",(mx,yy,hip_z),(mx+.035,yy,.58),.092,plum),
        (side+"_shin",(mx+.035,yy,.58),(mx+.09,yy,.17),.068,plum),
        (side+"_foot",(mx+.09,yy,.17),(mx+.29,yy,.075),.065,titanium),
        (side+"_upperarm",(mx+.05,yy,shoulder_z),(mx+.35,yy,1.4),.066,plum),
        (side+"_forearm",(mx+.35,yy,1.4),(mx+.65,yy,1.19),.053,plum),
        (side+"_hand",(mx+.65,yy,1.19),(mx+.78,yy,1.165),.045,titanium)):
        ob=rod("MECH / "+bn,a,b,r,material_);bind_bone(ob,bn)
    for bn,at in ((side+"_thigh",(mx,yy,hip_z)),(side+"_shin",(mx+.035,yy,.58)),(side+"_foot",(mx+.09,yy,.17)),
      (side+"_upperarm",(mx+.05,yy,shoulder_z)),(side+"_forearm",(mx+.35,yy,1.4)),(side+"_hand",(mx+.65,yy,1.19))):
        ob=sphere("MECH / "+bn+" servo",at,.075,joint);bind_bone(ob,bn)
    ob=sphere("MECH / "+side+" circular elbow actuator",(mx+.35,yy,1.4),.082,cyan);bind_bone(ob,side+"_forearm")
    # Fixed elbow/wrist and toe-mounted guide; visual hand contact is a *goal* not proven.
body=box("MECH / chest armor",(mx-.01,my,1.39),(.31,.38,.39),plum,.07);bind_bone(body,"spine")
body=box("MECH / pelvic shell",(mx,my,1.05),(.30,.40,.18),plum,.065);bind_bone(body,"pelvis")
head=sphere("MECH / helmet structure",(mx-.02,my,1.83),.10,titanium);bind_bone(head,"helmet")
visor=box("MECH / angular cyan visor",(mx+.115,my-.04,1.84),(.065,.20,.048),cyan,.018);bind_bone(visor,"helmet")
for j in range(3):
    a=(mx-.075-j*.024,my,1.92+j*.014);b=(mx-.17-j*.06,my,1.945-j*.006)
    ob=rod("MECH / swept helmet fin "+str(j),a,b,.025,plum);bind_bone(ob,"helmet")
tip=box("MECH / exact 1.9558m crest tip",(mx-.02,my,HEIGHT-.006),(.018,.018,.012),plum)
bind_bone(tip,"helmet")
# Height witness is a real-world dimension independently checkable in Blender
rod("METRIC / 1.9558m height witness",(mx-.42,my-.6,0),(mx-.42,my-.6,HEIGHT),.008,cyan)
# IK targets independently keyframed, active constraints on 2-bone legs and forearms.
targets={}
for side,offset in (("L",-.16),("R",.16)):
    foot_loc=(mx+.29+(-.12 if side=="L" else .12),my+offset,.075)
    hand_loc=(mx+.78,my+offset,1.165)
    for kind,loc,chain,eff in (("FOOT",foot_loc,3,side+"_foot"),("HAND",hand_loc,3,side+"_hand")):
        bpy.ops.object.empty_add(type="SPHERE",radius=.065,location=loc)
        target=bpy.context.object;target.name="IK TARGET / "+side+" "+kind;targets[side+"_"+kind]=target
        con=rig.pose.bones[eff].constraints.new("IK");con.target=target;con.chain_count=chain;con.use_stretch=False
        target.hide_render=True
# Minimal manufacturable-looking sheet, not an image overlay:
# a discretized mesh partially conforms to the door at right and remains slack at left
# with hand-pulled edge and spatial fold harmonics.
NX=28;NZ=14
verts=[];faces=[]
for iz in range(NZ+1):
    v=iz/NZ
    for ix in range(NX+1):
        u=ix/NX
        # +x toward door anchor, -x toward mech holding loose film
        x=-.92 + 1.80*u
        z=.55 + .69*v
        door_y=-.404
        loose=-.76
        adhesion=min(1,max(0,(u-.48)/.30))
        yy=(1-adhesion)*loose+adhesion*door_y+.055*math.sin(u*math.pi*5)*math.sin(v*math.pi*3)*(1-adhesion)
        verts.append((x,yy,z))
for iz in range(NZ):
    for ix in range(NX):
        a=iz*(NX+1)+ix
        faces.append((a,a+1,a+NX+2,a+NX+1))
mesh=bpy.data.meshes.new("Flexible vinyl sheet topology 29x15")
mesh.from_pydata(verts,[],faces);mesh.update()
sheet=bpy.data.objects.new("VINYL / partially adhered flexible sheet",mesh)
bpy.context.collection.objects.link(sheet);sheet.data.materials.append(film)
for polygon in sheet.data.polygons: polygon.use_smooth=True
sheet.modifiers.new("Thin flexible sheet thickness","SOLIDIFY").thickness=.003
sheet.modifiers.new("Film contact simulation candidate (disabled for deterministic shape-key render)","CLOTH").show_render=False
sheet.modifiers[-1].show_viewport=False
# Actual cloth modifier present for a follow-on physics bake. Shape keys control
# frames deterministically, so this is NOT falsely claimed as a cloth physics solve.
sheet.shape_key_add(name="A | hold film prior to install")
for phase,stretch,bend in (("B | crouch and pull",-.15,.12),("C | film contact",.08,-.02)):
    key=sheet.shape_key_add(name=phase)
    for vi,co in enumerate(verts):
        u=(vi%(NX+1))/NX;v=(vi//(NX+1))/NZ
        influence=(1-u)**1.7
        key.data[vi].co.x=co[0]+stretch*influence
        key.data[vi].co.y=co[1] + bend*influence + math.sin(u*6*math.pi+v*2*math.pi)*.028*influence
        key.data[vi].co.z=co[2]-(.11 if phase.startswith("B") else .03)*influence*(1-v)
phase_frames=[1,36,72]
for frame in phase_frames:
    scene.frame_set(frame)
    rig.pose.bones["pelvis"].location.z=(-.10 if frame==36 else -.03 if frame==72 else 0)
    rig.pose.bones["pelvis"].keyframe_insert(data_path="location",frame=frame)
    for side in ("L","R"):
        target=targets[side+"_FOOT"]
        target.location.x=mx+.29+(-.12 if side=="L" else .12)
        target.keyframe_insert(data_path="location",frame=frame)
        hand=targets[side+"_HAND"]
        hand.location.x=mx+.78+(.10 if frame==36 else .23 if frame==72 else 0)
        hand.location.z=1.165-(.14 if frame==36 else .03 if frame==72 else 0)
        hand.keyframe_insert(data_path="location",frame=frame)
    a=sheet.data.shape_keys.key_blocks[1]
    b=sheet.data.shape_keys.key_blocks[2]
    a.value=(1 if frame==36 else 0);b.value=(1 if frame==72 else 0)
    a.keyframe_insert(data_path="value",frame=frame)
    b.keyframe_insert(data_path="value",frame=frame)
# Camera: whole Nissan and 6ft5in mech are fully inside established frame.
bpy.ops.object.camera_add(location=(3.1,-9.9,2.1))
camera=bpy.context.object;camera.name="CAMERA / locked 3-4 studio overview"
direction=Vector((.15,.53,1.10))-camera.location
camera.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
camera.data.type="ORTHO";camera.data.ortho_scale=7.0;scene.camera=camera
for x,y,z,power,size in ((-2,-3,4,950,5),(2,-2,4,1100,4),(0,3,3.8,1250,3)):
    bpy.ops.object.light_add(type="AREA",location=(x,y,z))
    ob=bpy.context.object;ob.name="WORKSHOP / softbox"
    ob.data.energy=power;ob.data.shape="DISK";ob.data.size=size
# Native scene saved before rendering; GUI can open it and inspect/edit targets and modifiers.
scene.frame_set(1)
blend=OUT/"FWAI_VQ03_MECH_NISSAN_VINYL.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
artifacts=[]
for frame,label in ((1,"A_HOLD"),(36,"B_CROUCH"),(72,"C_CONTACT")):
    scene.frame_set(frame)
    path=OUT/("VQ03_"+label+".png")
    scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True)
    artifacts.append({"frame":frame,"label":label,"render":path.name,
       "sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
manifest={"schema":"FWAI_VQ03_DEVELOPMENT_POC_V1","canonical_visual_id":"FWAI-M001 v2.0",
 "canonical_reference_sha256":"480263bdd7637bfb2d90cc2deecdeb616eef03492a35216dbebfd3b1f44c555c",
 "mech_height_m":HEIGHT,"height_inches":77.0,"height_validation_tolerance_m":.00001,
 "car_proxy_length_m":car_length,"car_proxy_wheelbase_m":wheelbase,
 "vehicle_identity":"370Z NISMO indicative 3D blocking proxy; original photograph remains separate and protected",
 "vinyl_topology":[NX+1,NZ+1],"adhesion_band_u":[.48,.78],
 "rig":"FWAI-M001 / 6ft5in RIG / VQ03",
 "pose_frames":phase_frames,"render_files":artifacts,"blend":blend.name,
 "blend_sha256":hashlib.sha256(blend.read_bytes()).hexdigest(),
 "physical_cloth_solver_approved":False,"filming_approved":False,"paid_calls":0,
 "creative_approval":False,"auto_publish":False,
 "limitations":["geometry is an illustrative procedural mech, not 3D reconstruction of approved identity",
 "Nissan is approximated proxy and is not automotive CAD",
 "vinyl controlled by shape keys, cloth modifier not baked and collision unvalidated",
 "hands near sheet do not yet have rig-driven hard contact constraints"]}
(OUT/"VQ03_PROOF_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
print("FWAI_VQ03_COMPLETE",OUT, "frames",len(artifacts),"HEIGHT_METERS",HEIGHT)
