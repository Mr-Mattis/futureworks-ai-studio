"""VQ-04.04 constrained partial-door vinyl study and collision diagnostics.

Generates a *new*, independent 0.25-mm film mesh with three authored deformation
states. Verified door-surface clearances and anchored-film coverage are geometry
constraints, not a baked Blender cloth/adhesive simulation or real gripping physics.
The source vinyl is hidden temporarily and restored on clear. No scene autosave.
"""
import bpy
import math
from mathutils import Vector
from pathlib import Path
import hashlib

NAME="FWAI / VQ04.04 NARROW PARTIAL-DOOR FILM"
COL="FWAI LIVE PREVIEW / VQ04.04 FILM CONTACT"
SOURCE="VINYL / partially adhered flexible sheet"
DOOR="NISSAN / door passenger"
MASTER=Path.home()/"Documents"/"futureworks-p04-data"/"character-library"/"FWAI-M001"/"v2.0"/"FWAI-M001_APPROVED_FINAL_MASTER_V2.0.png"
MASTER_SHA="480263bdd7637bfb2d90cc2deecdeb616eef03492a35216dbebfd3b1f44c555c"
NX=25;NZ=17
THICKNESS_M=.00025
DOOR_FRONT_Y=-.379
FILM_SURFACE_Y=-.3812 # center, 2.2mm proud of the door box front
FILM_MIN_X=-1.04
FILM_MAX_X=.16
FILM_MIN_Z=.60
FILM_MAX_Z=1.00
ADHERED_FROM_X=-.37
CLIP_FRONT_Y=DOOR_FRONT_Y-.0011
STAGES={1:"HOLD",36:"REACH",72:"PARTIAL_APPLY"}
_state={"previous_hide_render":None,"previous_hide_viewport":None}

def _verify():
    if not MASTER.is_file() or hashlib.sha256(MASTER.read_bytes()).hexdigest()!=MASTER_SHA:
        raise ValueError("Approved FWAI-M001 V2 image lock missing or mutated")
    original=bpy.data.objects.get(SOURCE)
    door=bpy.data.objects.get(DOOR)
    if original is None or original.type!="MESH" or door is None or door.type!="MESH":
        raise ValueError("Required source film or door collision proxy absent")
    # The original car MUST remain stationary and unmodified.
    dmin=door.matrix_world@Vector((-0.70,-.019,-.31))
    dmax=door.matrix_world@Vector((.70,-.019,.31))
    if abs(dmin.y-DOOR_FRONT_Y)>.005 or abs(dmax.y-DOOR_FRONT_Y)>.005:
        raise ValueError("Collision proxy moved; recalibration required")
    return original,door

def _coords(frame):
    if frame not in STAGES:raise ValueError("Unknown frame")
    # Left loose edge shifts toward the door in the application state.
    grip={
        1:(-1.04,-.752,.080),    # x, y, upper-edge lift
        36:(-1.06,-.681,.10),
        72:(-.82,-.555,.035)
    }[frame]
    data=[]
    for j in range(NZ):
        v=j/(NZ-1)
        z_base=FILM_MIN_Z+(FILM_MAX_Z-FILM_MIN_Z)*v
        for i in range(NX):
            u=i/(NX-1)
            free=max(0.0,1.0-u/.5583)
            free=(free*free*(3-2*free))  # C1 continuous at partial adherence line
            x=grip[0]+(FILM_MAX_X-grip[0])*u
            # Give film a physically recognizable swept free flap without
            # allowing the anchored part to move into the solid door.
            sag=.012*free*(1-v)**2
            z=z_base+grip[2]*free*(v**2)-sag
            y=FILM_SURFACE_Y+(grip[1]-FILM_SURFACE_Y)*free
            y-=.010*free*(1-free)*math.sin(2*math.pi*v)
            if x>=-.47 and FILM_MIN_Z<=z<=1.03:
                y=min(y,CLIP_FRONT_Y)
            data.append((round(x,6),round(y,6),round(z,6)))
    return data

def grid(frame):
    return _coords(frame)

def _make():
    rows=_coords(1)
    verts=rows
    quads=[]
    for j in range(NZ-1):
        for i in range(NX-1):
            a=j*NX+i
            quads.append((a,a+1,a+1+NX,a+NX))
    mesh=bpy.data.meshes.new(NAME+" mesh")
    mesh.from_pydata(verts,[],quads)
    mesh.update()
    ob=bpy.data.objects.new(NAME,mesh)
    # Curve-free surface mesh with 0.25mm thickness and no auto bending.
    return ob

def _material():
    m=bpy.data.materials.get("FWAI / VQ04.04 vinyl cobalt blue")
    if m:return m
    m=bpy.data.materials.new("FWAI / VQ04.04 vinyl cobalt blue")
    m.diffuse_color=(.006,.045,.38,1.0)
    m.use_nodes=True
    bsdf=m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value=(.006,.045,.38,1.0)
    bsdf.inputs["Metallic"].default_value=.05
    bsdf.inputs["Roughness"].default_value=.21
    bsdf.inputs["Coat Weight"].default_value=.55
    bsdf.inputs["Coat Roughness"].default_value=.17
    return m

def _collect():
    return bpy.data.collections.get(COL)

def load():
    source,door=_verify()
    col=_collect()
    if col:
        return inspect()
    stage=bpy.data.collections.new(COL+" / staging")
    bpy.context.scene.collection.children.link(stage)
    obj=None
    try:
        obj=_make()
        stage.objects.link(obj)
        obj.data.materials.append(_material())
        basis=obj.shape_key_add(name="Basis")
        for frame,label in STAGES.items():
            shape=obj.shape_key_add(name="FWAI "+str(frame)+" "+label)
            for k,coord in enumerate(_coords(frame)):
                shape.data[k].co=coord
            for kframe in (1,36,72):
                shape.value=1.0 if kframe==frame else 0.0
                shape.keyframe_insert(data_path="value",frame=kframe,group="VQ04.04 FILM")
        # Unlike the previous 3-mm proxy film, this surface demonstrates a
        # 0.25mm thin material. Modifier is render only, not a solver.
        solid=obj.modifiers.new("FWAI / 0.25mm thin sheet","SOLIDIFY")
        solid.thickness=THICKNESS_M
        solid.offset=0.0
        smooth=obj.modifiers.new("FWAI / normal smoothing only","WEIGHTED_NORMAL")
        obj["FWAI_APPROVED"]=False
        obj["FWAI_NOT_BAKED_CLOTH"]=True
        obj["FWAI_REFERENCE_SOURCE"]=SOURCE
        obj["FWAI_FIXED_ADHESION_BOUNDARY_X"]=ADHERED_FROM_X
        obj["FWAI_UNITS"]="METERS"
        # Safe reversible source show/hide.
        _state["previous_hide_render"]=source.hide_render
        _state["previous_hide_viewport"]=source.hide_get()
        source.hide_render=True
        source.hide_set(True)
        stage.name=COL
        bpy.context.scene.frame_set(36)
        bpy.context.view_layer.update()
        return inspect()
    except Exception:
        if obj:
            bpy.data.objects.remove(obj,do_unlink=True)
        bpy.data.collections.remove(stage)
        source.hide_render=_state["previous_hide_render"] if _state["previous_hide_render"] is not None else source.hide_render
        if _state["previous_hide_viewport"] is not None:source.hide_set(_state["previous_hide_viewport"])
        raise

def inspect():
    col=_collect()
    if not col:return "VQ04.04 film preview absent"
    film=bpy.data.objects.get(NAME)
    if not film:return "Film preview missing"
    return "Narrow vinyl film: "+str(len(film.data.vertices))+" vertices, 0.25mm thick, stages 1/36/72"

def set_stage(frame):
    if type(frame) is not int or frame not in STAGES:
        raise ValueError("Unknown film stage")
    if not _collect():raise ValueError("Film preview not loaded")
    bpy.context.scene.frame_set(frame)
    return "Film stage "+STAGES[frame]+" (frame "+str(frame)+")"

def _evaluated(frame):
    if not _collect():raise ValueError("Film preview not loaded")
    bpy.context.scene.frame_set(frame)
    dg=bpy.context.evaluated_depsgraph_get()
    ob=bpy.data.objects[NAME].evaluated_get(dg)
    # Evaluated mesh includes Solidify so use original mesh with its shape keys
    # via to_mesh(), select nearest surface in world space for diagnostics.
    from mathutils.bvhtree import BVHTree
    tmp=ob.to_mesh(preserve_all_data_layers=False,depsgraph=dg)
    points=[ob.matrix_world@v.co for v in tmp.vertices]
    ob.to_mesh_clear()
    return points

def diagnose(frame):
    _verify()
    if frame not in STAGES:raise ValueError("Unsupported diagnosis frame")
    points=_coords(frame)
    # Coverage count: all material points located over proxy door x/z bounds.
    in_door=[(x,y,z) for x,y,z in points if -.47<=x<=.93 and .41<=z<=1.03]
    # Front-door AABB collision: to be clear, y must be at least 1.1mm
    # toward the camera (negative) from the front face at y=-0.379.
    violating=[(x,y,z) for x,y,z in in_door if y>CLIP_FRONT_Y+.000001]
    closest=min((DOOR_FRONT_Y-y for x,y,z in in_door),default=None)
    adherent=[(x,y,z) for x,y,z in in_door if x>=ADHERED_FROM_X]
    anchored_min=min((DOOR_FRONT_Y-y for x,y,z in adherent),default=None)
    anchored_max=max((DOOR_FRONT_Y-y for x,y,z in adherent),default=None)
    allx=[p[0] for p in points];allz=[p[2] for p in points]
    film_bbox=(min(allx),max(allx),min(allz),max(allz))
    door_area=1.4*.62
    # This is an estimate of covered area from projected BBOX of the portion
    # over the door, not a calibrated wetted surface area.
    bbox_area=(max(x for x,y,z in in_door)-min(x for x,y,z in in_door))*(
          max(z for x,y,z in in_door)-min(z for x,y,z in in_door)) if in_door else 0
    return {"frame":frame,"vertex_count":len(points),"door_vertices":len(in_door),
            "door_proxy_front_y_m":DOOR_FRONT_Y,"min_door_clearance_m":round(closest,6),
            "door_penetrating_vertices":len(violating),
            "anchored_clearance_min_m":round(anchored_min,6),
            "anchored_clearance_max_m":round(anchored_max,6),
            "film_bbox_xmin_xmax_zmin_zmax_m":film_bbox,
            "door_projected_coverage_fraction_upper_estimate":round(bbox_area/door_area,4),
            "clearance_is_proxy_test_only":True,
            "not_real_cloth_simulation":True,"adhesive_force_validated":False}

def clear():
    col=_collect()
    if not col:return "Film preview already cleared"
    original=bpy.data.objects.get(SOURCE)
    if original:
        if _state["previous_hide_render"] is not None:
            original.hide_render=_state["previous_hide_render"]
        if _state["previous_hide_viewport"] is not None:
            original.hide_set(_state["previous_hide_viewport"])
    for ob in tuple(col.objects):
        data=ob.data
        bpy.data.objects.remove(ob,do_unlink=True)
        if data and data.users==0:bpy.data.meshes.remove(data)
    bpy.data.collections.remove(col)
    _state["previous_hide_render"]=None
    _state["previous_hide_viewport"]=None
    return "Removed partial-door preview and restored legacy vinyl visibility (no save)"
