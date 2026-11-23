import bpy,json
from mathutils import Vector
def itemmax(obj):
    evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    if evaluated.type!="MESH":return None
    return max((evaluated.matrix_world@v.co).z for v in evaluated.data.vertices)
result={}
for frame in (1,36,72):
    bpy.context.scene.frame_set(frame)
    rows=[(itemmax(obj),obj.name) for obj in bpy.data.objects if obj.type=="MESH" and obj.name.startswith("MECH /")]
    rows.sort(reverse=True)
    result[frame]=[(round(height,5),name) for height,name in rows[:8]]
print("FWAI_HEIGHT_ALL_FRAMES",json.dumps(result))
