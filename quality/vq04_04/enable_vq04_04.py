import bpy,json
for mod in ("rigify","node_wrangler","fwai_live_bridge_addon"):
    bpy.ops.preferences.addon_enable(module=mod)
bpy.ops.wm.save_userpref()
result={m:m in bpy.context.preferences.addons for m in ("rigify","node_wrangler","fwai_live_bridge_addon")}
print("FWAI_VQ04_04_ADDONS",json.dumps(result))
if not all(result.values()):raise SystemExit(1)
