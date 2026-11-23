"""Correct the three VQ03 proxy helmet fins to the user-approved 6ft5in datum.

Unsaved, reversible, restricted to three explicit objects. Original mesh data is
retained and can be restored; no file, approved master or 3D scene is overwritten.
"""
import bpy
from mathutils import Vector
CAP=1.9558
NAMES=tuple("MECH / swept helmet fin "+str(n) for n in range(3))
_originals={}

def _max_height(obj):
    dg=bpy.context.evaluated_depsgraph_get()
    evaluated=obj.evaluated_get(dg)
    return max((evaluated.matrix_world@v.co).z for v in evaluated.data.vertices)
def inspect():
    rows=[]
    for n in NAMES:
        ob=bpy.data.objects.get(n)
        if ob is None:raise ValueError("Missing approved proxy fin "+n)
        rows.append((n,round(_max_height(ob),6)))
    return rows
def apply():
    if _originals:return "Height guard already active: max "+str(round(max(z for _,z in inspect()),5))+" m"
    fins=[]
    for n in NAMES:
        ob=bpy.data.objects.get(n)
        if ob is None or ob.type!="MESH" or ob.data.users!=1:
            raise ValueError("Missing or shared fin mesh: "+n)
        fins.append(ob)
    newmeshes=[]
    try:
        for ob in fins:
            dup=ob.data.copy()
            newmeshes.append((ob,dup))
            old=ob.data
            bpy.context.view_layer.update()
            evaluated=ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
            world_mat=evaluated.matrix_world.copy()
            inv=world_mat.inverted()
            for v in dup.vertices:
                world=world_mat@v.co
                if world.z>CAP:
                    world.z=CAP
                    v.co=inv@world
            ob.data=dup
            _originals[ob.name]=old
        bpy.context.view_layer.update()
        maximum=max(z for _,z in inspect())
        # Evaluate actual mesh vertices, not Blender bound-box cache.
        if maximum>CAP+.00002:raise RuntimeError("Height guard did not enforce 1.9558m")
        return "Corrected three helmet fins to <= 1.9558 m (unsaved/reversible)"
    except Exception:
        for ob,dup in newmeshes:
            if ob.name in _originals:ob.data=_originals.pop(ob.name)
            if dup.users==0:bpy.data.meshes.remove(dup)
        raise

def clear():
    count=0
    for name,original in tuple(_originals.items()):
        ob=bpy.data.objects.get(name)
        if ob is not None:
            clone=ob.data
            ob.data=original
            count+=1
            if clone.users==0:bpy.data.meshes.remove(clone)
        _originals.pop(name,None)
    bpy.context.view_layer.update()
    return "Restored "+str(count)+" original untouched helmet-fin meshes"
