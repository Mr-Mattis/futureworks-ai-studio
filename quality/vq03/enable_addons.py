"""Enable only verified built-in official Blender extensions needed for FWAI VQ03."""
import bpy,importlib.util,json
wanted=("rigify","node_wrangler","fwai_vq03_addon")
status={}
for module in wanted:
    if not importlib.util.find_spec(module):
        status[module]="NOT_INSTALLED";continue
    try:
        bpy.ops.preferences.addon_enable(module=module)
        status[module]="ENABLED" if module in bpy.context.preferences.addons else "ENABLE_FAILED"
    except Exception as exc:status[module]="ERROR:"+type(exc).__name__
bpy.ops.wm.save_userpref()
print("FWAI_VQ03_ADDONS="+json.dumps(status))
