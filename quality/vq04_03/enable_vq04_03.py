import bpy, json
for name in ("rigify","node_wrangler","fwai_live_bridge_addon"):
    bpy.ops.preferences.addon_enable(module=name)
bpy.ops.wm.save_userpref()
result={name:name in bpy.context.preferences.addons for name in ("rigify","node_wrangler","fwai_live_bridge_addon")}
print("FWAI_VQ04_03_ADDON_ENABLED",json.dumps(result))
if not all(result.values()):raise SystemExit(1)
