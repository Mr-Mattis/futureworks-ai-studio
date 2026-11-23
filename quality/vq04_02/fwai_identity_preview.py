"""VQ04.02 visual-identity mechanical detail geometry, read-only canonical binding.

Input JSON can only specify allowlisted named parts as bounded plates, rods, rings,
and coolant tubes. The asset is a *derivative study* of approved FWAI-M001 V2,
not a replacement for or fully faithful reproduction of the immutable master.
"""
import bpy, hashlib, json, math, re
from pathlib import Path
from mathutils import Vector, Matrix

ID="FWAI_M001_V2_IDENTITY_DETAIL_01"
COL="FWAI LIVE PREVIEW / VQ04.02 V2 IDENTITY"
ROOT=Path.home()/"Documents"/"futureworks-vq04-02"/"staging"
MASTER=Path.home()/"Documents"/"futureworks-p04-data"/"character-library"/"FWAI-M001"/"v2.0"/"FWAI-M001_APPROVED_FINAL_MASTER_V2.0.png"
MASTER_SHA="480263bdd7637bfb2d90cc2deecdeb616eef03492a35216dbebfd3b1f44c555c"
RIG="FWAI-M001 / 6ft5in RIG / VQ03"
BONES={"pelvis","spine","neck","helmet","L_thigh","R_thigh","L_upperarm","R_upperarm","L_forearm","R_forearm","L_hand","R_hand"}
MAT={
  "plum":((.18,.018,.26),.76,.22), "plum_light":((.33,.07,.46),.69,.24),
  "graphite":((.025,.032,.045),.58,.38),"titanium":((.42,.47,.53),.81,.24),
  "cyan":((.005,.56,.86),.24,.18),"amber":((.55,.18,.04),.36,.28),
  "vent":((.015,.023,.040),.23,.52),
}
PREFIX="FWAI V2 / "

def triplet(value,name):
    if not isinstance(value,list) or len(value)!=3:raise ValueError(name+" is not xyz")
    if any(type(a) not in (int,float) or not math.isfinite(a) for a in value):raise ValueError(name+" not finite")
    v=Vector((float(value[0]),float(value[1]),float(value[2])))
    if not (-2.7<=v.x<=-.40 and -1.40<=v.y<=-.4 and .35<=v.z<=1.956):
        raise ValueError(name+" outside bounded mech envelope")
    return v

def validate(command):
    if type(command)!=dict or set(command)!={"type","asset_id","sha256"} or command["type"]!="load_identity_preview":
        raise ValueError("Invalid identity-preview request")
    if command["asset_id"]!=ID:raise ValueError("Unknown asset")
    digest=command["sha256"]
    if type(digest)!=str or not re.fullmatch("[0-9a-f]{64}",digest):raise ValueError("Bad digest")
    path=ROOT/(ID+".json")
    if not path.is_file() or path.is_symlink() or path.stat().st_size>131072:raise ValueError("Missing/linked/oversized data file")
    blob=path.read_bytes()
    if hashlib.sha256(blob).hexdigest()!=digest:raise ValueError("Content SHA mismatch")
    if not MASTER.is_file() or hashlib.sha256(MASTER.read_bytes()).hexdigest()!=MASTER_SHA:
        raise ValueError("Immutable approved master mismatch")
    payload=json.loads(blob)
    if type(payload)!=dict or set(payload)!={"schema","asset_id","reference_sha256","units","parts","approved"}:
        raise ValueError("Unexpected manifest keys")
    if payload["schema"]!="FWAI_VQ04_IDENTITY_PREVIEW_V1" or payload["asset_id"]!=ID or payload["reference_sha256"]!=MASTER_SHA or payload["units"]!="METERS" or payload["approved"] is not False:
        raise ValueError("Wrong schema/canonical reference")
    rig=bpy.data.objects.get(RIG)
    if rig is None or rig.type!="ARMATURE" or not BONES.issubset(set(rig.data.bones.keys())):
        raise ValueError("Required metric armature missing")
    if not isinstance(payload["parts"],list) or not 1<=len(payload["parts"])<=120:
        raise ValueError("Incorrect part count")
    names=set()
    rows=[]
    for p in payload["parts"]:
        if type(p)!=dict or set(p)!={"name","shape","bone","material","points","thickness"}:raise ValueError("Unexpected part fields")
        name=p["name"];shape=p["shape"];bone=p["bone"];material=p["material"]
        if type(name)!=str or not re.fullmatch("[a-zA-Z0-9_-]{1,48}",name) or name in names:raise ValueError("Bad/duplicate component name")
        names.add(name)
        if shape not in {"plate","tube","rod","ring"} or bone not in BONES or material not in MAT:
            raise ValueError("Disallowed shape/bone/material")
        t=p["thickness"]
        if type(t) not in (int,float) or not math.isfinite(t) or not .003<=t<=.065:
            raise ValueError("Bad part thickness/radius")
        pts=p["points"]
        count={"plate":(3,9),"rod":(2,2),"tube":(2,12),"ring":(3,3)}[shape]
        if not isinstance(pts,list) or not count[0]<=len(pts)<=count[1]:
            raise ValueError("Bad polygon/path vertices")
        points=[triplet(x,name) for x in pts]
        if len(points)>2 and shape=="ring":
            center,rpoint,orient=points
            if not .028<=(rpoint-center).length<=.16 or not .05<=(orient-center).length<=.25:
                raise ValueError("Invalid ring radius/normal")
        elif shape=="plate":
            # N-gons are planar in world XY? Here design is silhouette in X/Z at a constant y depth.
            if max(v.y for v in points)-min(v.y for v in points)>.015:
                raise ValueError("Armor panel must be approximately planar in x-z")
            if (max(v.x for v in points)-min(v.x for v in points))<.006 or (max(v.z for v in points)-min(v.z for v in points))<.002:
                raise ValueError("Degenerate armor plate")
        else:
            if any((a-b).length<.008 for a,b in zip(points,points[1:])):
                raise ValueError("Degenerate tube segment")
        rows.append((name,shape,bone,material,points,float(t)))
    return rows,rig,digest

def _material(tag):
    name="FWAI V2 STUDY / "+tag
    m=bpy.data.materials.get(name)
    if m:return m
    rgb,metal,rough=MAT[tag]
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*rgb,1)
    bsdf=m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value=(*rgb,1)
    bsdf.inputs["Metallic"].default_value=metal
    bsdf.inputs["Roughness"].default_value=rough
    if tag=="cyan":
        bsdf.inputs["Emission Color"].default_value=(.0,.8,1,1)
        bsdf.inputs["Emission Strength"].default_value=2.2
    return m

def _plate(name,points,thick):
    n=len(points)
    verts=[tuple(v) for v in points]+[tuple(v+Vector((0,thick,0))) for v in points]
    faces=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    mesh=bpy.data.meshes.new(PREFIX+name+"_mesh")
    mesh.from_pydata(verts,[],faces);mesh.update()
    return mesh

def _path(name,points,radius,closed=False):
    curve=bpy.data.curves.new(PREFIX+name+"_curve","CURVE")
    curve.dimensions="3D";curve.resolution_u=2;curve.bevel_depth=radius;curve.bevel_resolution=3
    sp=curve.splines.new("POLY")
    sp.points.add(len(points)-1)
    for i,v in enumerate(points):
        sp.points[i].co=(*v,1.0)
    sp.use_cyclic_u=closed
    return curve

def _create(name,shape,bone,material,points,thickness,rig,collection):
    if shape=="plate":data=_plate(name,points,thickness)
    elif shape=="ring":
        center,rpoint,orient=points
        radial=rpoint-center
        normal=(orient-center).normalized()
        tangent=normal.cross(radial).normalized()*radial.length
        vecs=[center+radial*math.cos(2*math.pi*i/20)+tangent*math.sin(2*math.pi*i/20) for i in range(20)]
        data=_path(name,vecs,thickness,True)
    else:data=_path(name,points,thickness,False)
    obj=bpy.data.objects.new(PREFIX+name,data)
    collection.objects.link(obj)
    obj.data.materials.append(_material(material))
    keep=obj.matrix_world.copy()
    obj.parent=rig;obj.parent_type="BONE";obj.parent_bone=bone
    obj.matrix_world=keep
    obj["FWAI_PREVIEW_ASSET"]=ID
    obj["FWAI_APPROVED"]=False
    return obj

def _drop(col):
    for obj in tuple(col.objects):bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.collections.remove(col)

def load(command):
    rows,rig,digest=validate(command)
    staging=bpy.data.collections.get(COL+" / staging")
    if staging:raise ValueError("An earlier stage needs investigation")
    staged=bpy.data.collections.new(COL+" / staging")
    bpy.context.scene.collection.children.link(staged)
    try:
        for row in rows:_create(*row,rig,staged)
        bpy.context.view_layer.update()
    except Exception:
        _drop(staged)
        raise
    old=bpy.data.collections.get(COL)
    if old:_drop(old)
    staged.name=COL
    staged["FWAI_SHA256"]=digest
    staged["FWAI_APPROVED"]=False
    return "Loaded "+str(len(rows))+" V2 identity detail objects (study only, approval HOLD)"

def clear():
    c=bpy.data.collections.get(COL)
    if c is None:return "No identity preview loaded"
    n=len(c.objects);_drop(c)
    return "Cleared "+str(n)+" V2 identity-study parts"

def inspect():
    c=bpy.data.collections.get(COL)
    return "Identity-study parts: "+str(len(c.objects) if c else 0)
