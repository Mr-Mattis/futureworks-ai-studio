"""Enable reviewed Blender 5.3 add-ons for the local Future Works live geometry bridge."""
import bpy,json
names=("rigify","node_wrangler","fwai_live_bridge_addon")
result={}
for name in names:
    try:
        bpy.ops.preferences.addon_enable(module=name)
        result[name]="ENABLED" if name in bpy.context.preferences.addons else "FAILED"
    except Exception as ex:result[name]=type(ex).__name__
bpy.ops.wm.save_userpref()
print("FWAI_VQ04_BLENDER_EXTENSIONS",json.dumps(result))
if not all(s=="ENABLED" for s in result.values()):raise SystemExit(1)
