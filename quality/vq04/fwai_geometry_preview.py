"""Future Works VQ04 safe in-memory geometry previews for the visible Blender window.

Accepted input is a hash-pinned, local JSON *data* file: no scripts, drivers,
external blends, imports, arbitrary file paths, autosave, or network access.
"""
import bpy
import bmesh
import hashlib
import json
import math
from pathlib import Path
from mathutils import Vector, Matrix

ASSET_ID = "FWAI_M001_LOWER_BODY_DETAIL_V1"
COLLECTION = "FWAI LIVE PREVIEW / VQ04 LOWER BODY"
ROOT = Path.home() / "Documents" / "futureworks-vq04" / "staging"
SCENE_RIG = "FWAI-M001 / 6ft5in RIG / VQ03"
CANONICAL = Path.home() / "Documents" / "futureworks-p04-data" / "character-library" / "FWAI-M001" / "v2.0" / "FWAI-M001_APPROVED_FINAL_MASTER_V2.0.png"
CANON_SHA = "480263bdd7637bfb2d90cc2deecdeb616eef03492a35216dbebfd3b1f44c555c"
PALETTE = {
    "plum": ((0.20, 0.025, 0.26), 0.72),
    "graphite": ((0.027, 0.031, 0.044), 0.42),
    "titanium": ((0.38, 0.43, 0.49), 0.80),
    "cyan": ((0.005, 0.60, 0.88), 0.25),
}
VALID_BONES = {
    "L_thigh", "L_shin", "L_foot",
    "R_thigh", "R_shin", "R_foot",
}
NAME_PREFIX = "FWAI VQ04 / "

def _sha(data):
    return hashlib.sha256(data).hexdigest()

def _triplet(value, name, maxabs=4.5):
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(name + " requires a 3-number list")
    for x in value:
        if type(x) not in (int,float) or not math.isfinite(x) or abs(x) > maxabs:
            raise ValueError(name + " must contain finite bounded coordinates")
    return Vector([float(x) for x in value])

def _validate(command):
    if set(command) != {"type","asset_id","sha256"} or command["type"] != "load_preview":
        raise ValueError("Unexpected preview command keys")
    if command["asset_id"] != ASSET_ID:
        raise ValueError("Unknown preview asset")
    digest = command["sha256"]
    if type(digest) is not str or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("Invalid SHA256 identifier")
    path = ROOT / (ASSET_ID + ".json")
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 128 * 1024:
        raise ValueError("Missing, linked, or oversized preview manifest")
    blob = path.read_bytes()
    if _sha(blob) != digest:raise ValueError("Preview manifest digest changed")
    if not CANONICAL.is_file() or _sha(CANONICAL.read_bytes()) != CANON_SHA:
        raise ValueError("Approved design lock missing or modified")
    payload = json.loads(blob)
    if set(payload) != {"schema","asset_id","canonical_sha256","units","parts","review_only"}:
        raise ValueError("Unexpected manifest keys")
    if payload["schema"] != "FWAI_VQ04_GEOMETRY_PREVIEW_V1" or payload["asset_id"] != ASSET_ID:
        raise ValueError("Manifest schema/asset mismatch")
    if payload["canonical_sha256"] != CANON_SHA or payload["units"] != "METERS" or payload["review_only"] is not True:
        raise ValueError("Manifest must target locked metric preview")
    parts=payload["parts"]
    if not isinstance(parts,list) or not (1 <= len(parts) <= 120):
        raise ValueError("Invalid number of geometry parts")
    seen=set()
    checked=[]
    for p in parts:
        if not isinstance(p,dict) or set(p) != {"name","shape","bone","material","a","b","radius"}:
            raise ValueError("Invalid part fields")
        name=p["name"]
        if type(name) is not str or not (1 <= len(name) <= 48) or not all(c.isalnum() or c in "_- " for c in name):
            raise ValueError("Unsafe part name")
        if name in seen:raise ValueError("Duplicate part name")
        seen.add(name)
        if p["bone"] not in VALID_BONES or p["material"] not in PALETTE or p["shape"] != "rod":
            raise ValueError("Disallowed shape, material or bone")
        a=_triplet(p["a"],"a");b=_triplet(p["b"],"b")
        r=p["radius"]
        if type(r) not in (int,float) or not math.isfinite(r) or not (0.004 <= r <= 0.18):
            raise ValueError("Invalid radius")
        if not (0.015 <= (b-a).length <= 0.8):
            raise ValueError("Invalid rod length")
        checked.append((name,p["bone"],p["material"],a,b,float(r)))
    rig=bpy.data.objects.get(SCENE_RIG)
    if not rig or rig.type!="ARMATURE":raise ValueError("Required metric VQ03 rig not loaded")
    if not VALID_BONES.issubset(set(rig.data.bones.keys())):raise ValueError("Expected rig bones missing")
    return checked, rig, digest

def _material(key):
    name="FWAI VQ04 PREVIEW / "+key
    mat=bpy.data.materials.get(name)
    if mat is not None:return mat
    rgb,metal=PALETTE[key]
    mat=bpy.data.materials.new(name)
    mat.diffuse_color=(*rgb,1.0)
    mat.use_nodes=True
    node=mat.node_tree.nodes.get("Principled BSDF")
    node.inputs["Base Color"].default_value=(*rgb,1.0)
    node.inputs["Metallic"].default_value=metal
    node.inputs["Roughness"].default_value=0.24 if key!="graphite" else 0.48
    if key=="cyan":
        node.inputs["Emission Color"].default_value=(*rgb,1.0)
        node.inputs["Emission Strength"].default_value=1.8
    return mat

def _rod(collection,name,bone,material,a,b,radius,rig):
    direction=b-a
    bm=bmesh.new()
    bmesh.ops.create_cone(bm,cap_ends=True,cap_tris=False,segments=16,
                          radius1=radius,radius2=radius,depth=direction.length)
    mesh=bpy.data.meshes.new(NAME_PREFIX+name+" mesh")
    bm.to_mesh(mesh);bm.free()
    obj=bpy.data.objects.new(NAME_PREFIX+name,mesh)
    collection.objects.link(obj)
    obj.data.materials.append(_material(material))
    rotation=direction.to_track_quat("Z","Y").to_matrix().to_4x4()
    world=Matrix.Translation((a+b)/2) @ rotation
    obj.matrix_world=world
    bpy.context.view_layer.update()
    keep=obj.matrix_world.copy()
    obj.parent=rig
    obj.parent_type="BONE"
    obj.parent_bone=bone
    obj.matrix_world=keep
    obj["FWAI_PREVIEW_SOURCE"]=ASSET_ID
    obj["FWAI_PREVIEW_BONE"]=bone
    return obj

def _drop_collection(collection):
    for obj in tuple(collection.objects):
        bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.collections.remove(collection)

def load(command):
    checked,rig,digest=_validate(command)
    # Transaction: original preview stays until new preview was successfully built.
    name=COLLECTION+" / staging"
    existing=bpy.data.collections.get(name)
    if existing is not None:
        raise ValueError("A previous preview staging transaction needs inspection")
    collection=bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    try:
        for part in checked:_rod(collection,*part,rig)
        bpy.context.view_layer.update()
    except Exception:
        _drop_collection(collection)
        raise
    old=bpy.data.collections.get(COLLECTION)
    if old:_drop_collection(old)
    collection.name=COLLECTION
    collection["FWAI_SHA256"]=digest
    collection["FWAI_APPROVED"]=False
    return "Loaded "+str(len(checked))+" live mechanical preview parts (unapproved)"

def clear():
    col=bpy.data.collections.get(COLLECTION)
    if col is None:return "No preview geometry loaded"
    count=len(col.objects)
    _drop_collection(col)
    return "Cleared "+str(count)+" preview parts; original scene unchanged"

def inspect():
    col=bpy.data.collections.get(COLLECTION)
    num=len(col.objects) if col else 0
    return "Live preview parts: "+str(num)+", scene frame: "+str(bpy.context.scene.frame_current)
