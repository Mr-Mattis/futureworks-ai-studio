import bpy,json
for key in ("rigify","node_wrangler","fwai_live_bridge_addon"):
    bpy.ops.preferences.addon_enable(module=key)
bpy.ops.wm.save_userpref()
print("FWAI_VQ04_02_ADDON_ENABLED",json.dumps({name:name in bpy.context.preferences.addons for name in ("rigify","node_wrangler","fwai_live_bridge_addon")}))
