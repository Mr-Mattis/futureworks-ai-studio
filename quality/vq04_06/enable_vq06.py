import bpy
bpy.ops.preferences.addon_enable(module="fwai_vq06_coupled_review")
bpy.ops.wm.save_userpref()
if "fwai_vq06_coupled_review" not in bpy.context.preferences.addons:raise RuntimeError("Not enabled")
print("VQ06 BLENDER ADDON VERIFIED")
