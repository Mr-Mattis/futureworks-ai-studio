"""VQ-04.03: editable articulated fingers & concealed forearm squeegee preview.

Approved FWAI-M001 V2 appearance is immutable; this is a reversible engineering
study, not final calibrated physical grip, material adhesion, or tool mechanism.
All Blender modifications are transient and confined to a named preview collection.
No arbitrary scripts, external imports, network endpoints, saves, or paid services.
"""
import bpy, bmesh, math
from pathlib import Path
from mathutils import Vector, Matrix

COL="FWAI LIVE PREVIEW / VQ04.03 HANDS AND TOOLS"
RIG="FWAI-M001 / 6ft5in RIG / VQ03"
FINGERS=("thumb","index","middle","ring","little")
STAGES={1:"OPEN",36:"REACH",72:"PINCH"}
CANON=Path.home()/"Documents"/"futureworks-p04-data"/"character-library"/"FWAI-M001"/"v2.0"/"FWAI-M001_APPROVED_FINAL_MASTER_V2.0.png"
EXPECTED_SHA="480263bdd7637bfb2d90cc2deecdeb616eef03492a35216dbebfd3b1f44c555c"
PREFIX="FWAI GRIP / "
_runtime={"loaded":False}

def _mat(tag):
    settings={
       "plum":((.22,.026,.31),.70,.23),
       "titanium":((.46,.49,.54),.83,.24),
       "graphite":((.024,.029,.043),.52,.36),
       "cyan":((.008,.65,.9),.20,.25),
       "rubber":((.07,.075,.079),.02,.75),
    }
    name="FWAI VQ04.03 / "+tag
    material=bpy.data.materials.get(name)
    if material:return material
    color,metal,rough=settings[tag]
    material=bpy.data.materials.new(name)
    material.use_nodes=True;material.diffuse_color=(*color,1.0)
    bs=material.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*color,1)
    bs.inputs["Metallic"].default_value=metal
    bs.inputs["Roughness"].default_value=rough
    if tag=="cyan":
        bs.inputs["Emission Color"].default_value=(*color,1)
        bs.inputs["Emission Strength"].default_value=1.5
    return material

def _new_empty(col,name,world,parent=None):
    ob=bpy.data.objects.new(PREFIX+name,None)
    col.objects.link(ob)
    ob.empty_display_type="SPHERE";ob.empty_display_size=.014
    ob.matrix_world=Matrix.Translation(Vector(world))
    if parent is not None:
        bpy.context.view_layer.update()
        mat=ob.matrix_world.copy()
        ob.parent=parent
        ob.matrix_world=mat
    ob.hide_render=True
    return ob

def _rod(col,name,start,end,r,tag,parent=None):
    a,b=Vector(start),Vector(end)
    v=b-a
    if v.length<.007:raise ValueError("Refusing zero-length finger segment")
    mesh=bpy.data.meshes.new(PREFIX+name+"_mesh")
    bm=bmesh.new()
    bmesh.ops.create_cone(bm,cap_ends=True,segments=14,
                          radius1=r,radius2=r,depth=v.length)
    bm.to_mesh(mesh);bm.free()
    ob=bpy.data.objects.new(PREFIX+name,mesh)
    col.objects.link(ob)
    ob.data.materials.append(_mat(tag))
    world=Matrix.Translation((a+b)*.5)@v.to_track_quat("Z","Y").to_matrix().to_4x4()
    ob.matrix_world=world
    if parent is not None:
        bpy.context.view_layer.update()
        keep=ob.matrix_world.copy()
        ob.parent=parent;ob.matrix_world=keep
    return ob

def _ball(col,name,position,r,tag,parent=None):
    mesh=bpy.data.meshes.new(PREFIX+name+"_mesh")
    bm=bmesh.new()
    bmesh.ops.create_uvsphere(bm,u_segments=12,v_segments=8,radius=r)
    bm.to_mesh(mesh);bm.free()
    ob=bpy.data.objects.new(PREFIX+name,mesh)
    col.objects.link(ob)
    ob.data.materials.append(_mat(tag))
    ob.matrix_world=Matrix.Translation(Vector(position))
    if parent is not None:
        bpy.context.view_layer.update()
        keep=ob.matrix_world.copy()
        ob.parent=parent;ob.matrix_world=keep
    return ob

def _required():
    import hashlib
    if not CANON.is_file() or hashlib.sha256(CANON.read_bytes()).hexdigest()!=EXPECTED_SHA:
        raise ValueError("Owner-approved FWAI-M001 V2 master missing or modified")
    rig=bpy.data.objects.get(RIG)
    film=bpy.data.objects.get("VINYL / partially adhered flexible sheet")
    if not rig or rig.type!="ARMATURE" or film is None or film.type!="MESH":
        raise ValueError("Required VQ03 armature or independent vinyl sheet missing")
    for side in ("L","R"):
        if not bpy.data.objects.get("MECH / "+side+"_hand"):
            raise ValueError("Missing mechanical hand anchor "+side)
    return rig,film

def _delete(collection):
    # Linked control objects are only children of our own preview collection.
    for ob in tuple(collection.objects):
        data=ob.data
        bpy.data.objects.remove(ob,do_unlink=True)
        if data is not None and data.users==0:
            if isinstance(data,bpy.types.Mesh):bpy.data.meshes.remove(data)
            elif isinstance(data,bpy.types.Curve):bpy.data.curves.remove(data)
    bpy.data.collections.remove(collection)

def load():
    _required()
    if bpy.data.collections.get(COL):
        return inspect()
    staging_name=COL+" / staging"
    if bpy.data.collections.get(staging_name):
        raise ValueError("Unresolved staging transaction; inspect before retry")
    col=bpy.data.collections.new(staging_name)
    bpy.context.scene.collection.children.link(col)
    try:
        for side in ("L","R"):
            base=bpy.data.objects["MECH / "+side+"_hand"]
            anchor=base.matrix_world.translation.copy()
            # Unmodified hand mesh is still part of the original mech.
            # Preview coordinates are authored at frame 36 and parented to
            # the existing hand anchor, so they follow arm motion.
            center=anchor+Vector((.066,-.026 if side=="R" else -.03,-.014))
            mount=_new_empty(col,side+"_palm_mount",center,base)
            palm=_rod(col,side+"_palm_armor",
                      center+Vector((-.045,0,.012)),
                      center+Vector((.042,0,.012)),.031,"plum",mount)
            _ball(col,side+"_palm_servo",center,.038,"titanium",mount)
            for finger_index,finger in enumerate(FINGERS):
                # Four slim fingers above the gripping edge and a separately
                # articulated opposable thumb below it.
                if finger=="thumb":
                    yshift=-.043
                    zshift=-.055
                    lengths=(.052,.039,.031)
                else:
                    yshift=(-.014 if side=="R" else -.012)
                    zshift=(finger_index-2)*.026
                    lengths=(.067,.048,.034)
                root=center+Vector((.033,yshift,zshift))
                parent=mount
                for joint_index,length in enumerate(lengths):
                    end=root+Vector((length,0,-.006 if finger=="thumb" else .002))
                    pivot=_new_empty(col,side+"_"+finger+"_joint"+str(joint_index),root,parent)
                    pivot.rotation_mode="XYZ"
                    _rod(col,side+"_"+finger+"_phalanx"+str(joint_index),root,end,
                         .014 if joint_index==0 else .011 if joint_index==1 else .009,
                         "graphite" if joint_index==2 else "titanium",pivot)
                    _ball(col,side+"_"+finger+"_hinge"+str(joint_index),root,
                          .014 if joint_index==0 else .012,
                          "cyan" if joint_index==0 else "plum",pivot)
                    root=end
                    parent=pivot
                _ball(col,side+"_"+finger+"_fingerpad",root,.013,"rubber",parent)
        # One compact sealed forearm cassette, as approved by V2.
        # Linear slide is parented to the existing LEFT forearm. Only squeegee
        # stage is modeled; heat gun and knife remain concealed/NOT modeled.
        forearm=bpy.data.objects["MECH / L_forearm"]
        forearm_world=forearm.matrix_world.translation.copy()
        rail_start=forearm_world+Vector((.025,-.027,-.018))
        slide=_new_empty(col,"tool_slider",rail_start,forearm)
        _rod(col,"tool_integrated_rail",rail_start+Vector((-.064,0,0)),
             rail_start+Vector((.050,0,0)),.023,"graphite",forearm)
        _rod(col,"squeegee_linear_cartridge",rail_start,
             rail_start+Vector((.115,0,0)),.016,"titanium",slide)
        _rod(col,"squeegee_tip_bridge",
             rail_start+Vector((.120,0,-.042)),
             rail_start+Vector((.120,0,.045)),.019,"rubber",slide)
        _ball(col,"tool_active_indicator",rail_start+Vector((.012,-.025,.012)),
              .013,"cyan",slide)
        # Distinct three-phase poses. All finger controls animate as real
        # independent nested hinge pivots, not image-generation guesses.
        for frame in (1,36,72):
            amount={1:0.0,36:0.35,72:1.0}[frame]
            for side in ("L","R"):
                for finger in FINGERS:
                    for joint_index in range(3):
                        pivot=bpy.data.objects[PREFIX+side+"_"+finger+"_joint"+str(joint_index)]
                        pivot.rotation_mode="XYZ"
                        # Genuine hinge articulation; thumb opposes the other
                        # digits. Rotation relative to initial attachment.
                        bend=(-.33 if finger=="thumb" else .30)*amount*(1.0+joint_index*.32)
                        pivot.rotation_euler.y=bend
                        pivot.keyframe_insert(data_path="rotation_euler",frame=frame,group="FWAI GRIP")
            # Keep the initial local coordinate; moving .075m is a mechanical
            # preview only and intentionally does not project a tool through the car.
            if frame==1:base_slide_x=slide.location.x
            slide.location.x=base_slide_x+{1:0,36:.025,72:.075}[frame]
            slide.keyframe_insert(data_path="location",frame=frame,group="FWAI TOOL")
        bpy.context.scene.frame_set(36)
        bpy.context.view_layer.update()
        col["FWAI_OWNER_APPROVED"]=False
        col["FWAI_CONTACT_CERTIFIED"]=False
        col["FWAI_CLOTH_SOLVED"]=False
        col["FWAI_REVIEW_ONLY"]=True
    except Exception:
        _delete(col)
        raise
    col.name=COL
    _runtime["loaded"]=True
    return inspect()

def inspect():
    col=bpy.data.collections.get(COL)
    if col is None:return "Hand/tool preview absent"
    joints=[x for x in col.objects if "_joint" in x.name and x.type=="EMPTY"]
    fingers=[x for x in col.objects if "_phalanx" in x.name and x.type=="MESH"]
    return "Hand/tool preview: "+str(len(joints))+" finger joints, "+str(len(fingers))+" segment meshes"

def clear():
    col=bpy.data.collections.get(COL)
    if col is None:return "Hand/tool preview already cleared"
    n=len(col.objects)
    _delete(col)
    _runtime["loaded"]=False
    return "Cleared "+str(n)+" unsaved preview objects"

def set_stage(stage):
    if type(stage)!=int or stage not in STAGES:
        raise ValueError("Grip stage must be one of 1, 36, 72")
    if bpy.data.collections.get(COL) is None:
        raise ValueError("Hand/tool preview not loaded")
    bpy.context.scene.frame_set(stage)
    return "Hand/tool phase "+STAGES[stage]+" (frame "+str(stage)+")"
