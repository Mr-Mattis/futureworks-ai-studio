import bpy,math
from mathutils import Vector
sc=bpy.context.scene;sc.frame_set(36)
items=[]
dg=bpy.context.evaluated_depsgraph_get()
for obj in bpy.data.objects:
    if obj.type not in {"MESH","CURVE"} or not obj.name.startswith("MECH /"):
        continue
    e=obj.evaluated_get(dg)
    m=e.matrix_world
    # bound_box world corners
    heights=[(m@Vector(v)).z for v in e.bound_box]
    if heights:items.append((round(max(heights),5),obj.name))
items.sort(reverse=True)
print("FWAI_VQ04_HEIGHT_AUDIT",items[:16])
