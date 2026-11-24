import bpy,json
bpy.ops.preferences.addon_enable(module="fwai_vq05_cloth_review")
bpy.ops.wm.save_userpref()
name="fwai_vq05_cloth_review"
ok=name in bpy.context.preferences.addons
print("FWAI_VQ05_INSTALL",json.dumps({"addon":name,"enabled":ok}))
if not ok:raise SystemExit(1)
