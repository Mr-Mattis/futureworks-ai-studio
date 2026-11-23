import bpy,json
bpy.ops.preferences.addon_enable(module="fwai_live_bridge_addon")
bpy.ops.wm.save_userpref()
print("FWAI_LIVE_ADDON_ENABLED", "fwai_live_bridge_addon" in bpy.context.preferences.addons)
