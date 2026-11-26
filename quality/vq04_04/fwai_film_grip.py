"""VQ04.04 film/hand interface: actual mesh-distance diagnostics and bounded IK.

Checks 10 fingertip-pad center-to-BVH distances at stages 1,36,72.
Calibrates only frame36 right-index pad to within 3mm of a user-visible
free-film-edge TARGET offset by its nominal sphere radius and safety gap.
Not two-sided pinch physics: reports unresolved clearance and thumb contact.
All updates to original IK goals are transient and reversible.
"""
import bpy, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import fwai_film_contact as film
import fwai_hand_tool_preview as hand
TARGET="IK TARGET / R HAND"
PAD="FWAI GRIP / R_index_fingerpad"
VERTEX=16*film.NX # upper-left grip corner, free edge
RADIUS=.013
FACE_CLEARANCE=.0013
OFFSET=Vector((0,-(RADIUS+FACE_CLEARANCE),0))
_state={"original":None,"calibrated":False,"thumb_initial":None,"thumb_calibrated":False,"proxy":None,"ik":None,"original_constraint_target":None}

def _required():
    if film.COL not in bpy.data.collections or hand.COL not in bpy.data.collections:
        raise ValueError("VQ04.04 film and articulated hands must both be loaded")
    original=bpy.data.objects.get(TARGET)
    if not original:raise ValueError("Right-hand IK target missing")
    return original,bpy.data.objects[film.NAME]

def _nearest_deps(frame):
    if bpy.context.scene.frame_current != frame:
        bpy.context.scene.frame_set(frame)
    dg=bpy.context.evaluated_depsgraph_get()
    _target,obj=_required()
    evaluated=obj.evaluated_get(dg)
    bvh=BVHTree.FromObject(obj,dg,epsilon=0.0)
    return evaluated,bvh

def diagnose(frame):
    if frame not in (1,36,72):raise ValueError("Unexpected pose frame")
    f,bvh=_nearest_deps(frame)
    inverse=f.matrix_world.inverted()
    rows=[]
    for side in ("L","R"):
        for digit in hand.FINGERS:
            ob=bpy.data.objects[hand.PREFIX+side+"_"+digit+"_fingerpad"].evaluated_get(bpy.context.evaluated_depsgraph_get())
            center=ob.matrix_world.translation.copy()
            projected=bvh.find_nearest(inverse@center,1.0)
            if projected is None:raise ValueError("Film BVH nearest-surface query failed")
            point,normal,face,dist=projected
            distance=(center-f.matrix_world@point).length
            rows.append({"digit":side+"_"+digit,"center_to_film_m":round(distance,6),
              "surface_clearance_m":round(distance-RADIUS-film.THICKNESS_M*.5,6),
              "penetrating":distance<RADIUS+film.THICKNESS_M*.5-.00005})
    return {"frame":frame,"pads":rows,
       "penetrating_pad_count":sum(r["penetrating"] for r in rows),
       "min_surface_clearance_m":min(r["surface_clearance_m"] for r in rows),
       "physical_finger_force_verified":False,"full_mesh_collision_verified":False}

def _goal():
    if bpy.context.scene.frame_current!=36:raise ValueError("IK target search only at frame36")
    _target,obj=_required()
    dg=bpy.context.evaluated_depsgraph_get()
    ev=obj.evaluated_get(dg)
    corner=ev.matrix_world@ev.data.vertices[VERTEX].co
    # Frame36 film free-upper corner is well outside adhered door zone.
    return corner+OFFSET

def _film_point():
    _target,ob=_required()
    eval_ob=ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return eval_ob.matrix_world@eval_ob.data.vertices[VERTEX].co

def _thumb_report():
    surface=_film_point()
    thumb=bpy.data.objects[hand.PREFIX+"R_thumb_fingerpad"]
    index=bpy.data.objects[PAD]
    bpy.context.view_layer.update()
    thumb_world=thumb.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation.copy()
    index_world=index.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation.copy()
    thumb_target=surface+Vector((0,RADIUS+FACE_CLEARANCE,0))
    thumb_gap=(thumb_world-thumb_target).length
    right_side=(index_world.y < surface.y-RADIUS) and (thumb_world.y > surface.y+RADIUS)
    return {"frame":36,"thumb_target_gap_m":round(thumb_gap,6),
      "opposing_sides":right_side,"thumb_center_xyz_m":[round(float(v),6) for v in thumb_world],
      "index_center_xyz_m":[round(float(v),6) for v in index_world],
      "film_center_xyz_m":[round(float(v),6) for v in surface],
      "two_sided_geometry_pass":thumb_gap<=.003 and right_side,
      "pinch_force_newtons":None,"grip_physically_validated":False}

def measure():
    goal=_goal()
    pad=bpy.data.objects[PAD].evaluated_get(bpy.context.evaluated_depsgraph_get())
    actual=pad.matrix_world.translation.copy()
    return {"frame":36,"gap_to_offset_target_m":round((goal-actual).length,6),
      "film_target_xyz_m":[round(float(v),6) for v in goal],
      "right_index_pad_center_xyz_m":[round(float(v),6) for v in actual],
      "radius_m":RADIUS,"physical_grip_verified":False}

def calibrate():
    target,fo=_required()
    if bpy.context.scene.frame_current!=36:raise ValueError("Calibration limited to frame36")
    if _state["calibrated"]:
        if measure()["gap_to_offset_target_m"]<=.003 and _thumb_report()["two_sided_geometry_pass"]:
            return "VQ04.04 two-sided geometric staging still calibrated, no force solver"
        clear()
    original=target.location.copy()
    rig=bpy.data.objects.get(hand.RIG)
    if not rig:raise ValueError("FWAI armature missing")
    constraints=[c for bone in rig.pose.bones for c in bone.constraints
                 if hasattr(c,"target") and c.target==target and c.type=="IK"]
    if len(constraints)!=1:
        raise ValueError("Expected exactly one R-hand IK constraint")
    constraint=constraints[0]
    # Use a temporary unanimated IK override. Keyframed source remains
    # untouched; render-time frame evaluation can no longer silently erase
    # the calibrated pose, unlike mutating an animated empty.location.
    proxy=bpy.data.objects.new("FWAI / VQ04.04 temporary right-hand IK goal",None)
    bpy.context.scene.collection.objects.link(proxy)
    proxy.empty_display_type="SPHERE"
    proxy.empty_display_size=.023
    proxy.hide_render=True
    proxy.matrix_world=target.matrix_world.copy()
    constraint.target=proxy
    bpy.context.view_layer.update()
    try:
        for _ in range(22):
            bpy.context.view_layer.update()
            desired=_goal()
            current=bpy.data.objects[PAD].evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation
            err=desired-current
            if err.length<=.0025:break
            proxy.location+=err*.64
            if (proxy.location-target.location).length>.32:
                raise ValueError("Required IK adjustment exceeds 32cm bounded reach")
        if measure()["gap_to_offset_target_m"]>.003:
            raise ValueError("Could not reach target within 3mm")
        state=diagnose(36)
        candidate=next(p for p in state["pads"] if p["digit"]=="R_index")
        if candidate["penetrating"]:
            raise ValueError("Target configuration penetrates film with right-index pad")
    except Exception:
        constraint.target=target
        bpy.data.objects.remove(proxy,do_unlink=True)
        bpy.context.view_layer.update()
        raise
    # Stage an independent opposable thumb pad on the OTHER side of the film.
    # This is a constrained geometric fit, not a contact force or friction solver.
    thumb_root=bpy.data.objects[hand.PREFIX+"R_thumb_joint0"]
    thumb_initial=thumb_root.location.copy()
    try:
        center=_thumb_report()
        surface=Vector(center["film_center_xyz_m"])
        desired=surface+Vector((0,RADIUS+FACE_CLEARANCE,0))
        actual=Vector(center["thumb_center_xyz_m"])
        delta=desired-actual
        if delta.length>.082:
            raise ValueError("Thumb contact requires >82mm root adjustment: unsafe")
        parent=thumb_root.parent
        if parent is None:raise ValueError("Thumb control missing parent")
        parent_inverse=parent.matrix_world.inverted().to_3x3()
        thumb_root.location+=parent_inverse@delta
        bpy.context.view_layer.update()
        pair=_thumb_report()
        if not pair["two_sided_geometry_pass"]:
            raise ValueError("Thumb cannot form nonpenetrating two-sided geometric grip")
        collision=diagnose(36)
        byname={entry["digit"]:entry for entry in collision["pads"]}
        if byname["R_index"]["penetrating"] or byname["R_thumb"]["penetrating"]:
            raise ValueError("Fingerpad sphere intersects film at geometric pinch")
    except Exception:
        thumb_root.location=thumb_initial
        constraint.target=target
        bpy.data.objects.remove(proxy,do_unlink=True)
        bpy.context.view_layer.update()
        raise
    _state.update(original=original,calibrated=True,thumb_initial=thumb_initial,thumb_calibrated=True,
                  proxy=proxy,ik=constraint,original_constraint_target=target)
    return "Two-sided geometric staging: index gap="+str(measure()["gap_to_offset_target_m"])+"m; thumb gap="+str(_thumb_report()["thumb_target_gap_m"])+"m; NO force solver"

def clear():
    if not _state["calibrated"] and not _state["thumb_calibrated"]:return "No film target correction active"
    # Reset even if invoked by a Blender frame-change handler.
    # No scene.frame_set() calls here: they would recurse during frame change.
    if _state["ik"] is not None and _state["original_constraint_target"] is not None:
        _state["ik"].target=_state["original_constraint_target"]
    proxy=_state.get("proxy")
    if proxy and bpy.data.objects.get(proxy.name):
        bpy.data.objects.remove(proxy,do_unlink=True)
    thumb=bpy.data.objects.get(hand.PREFIX+"R_thumb_joint0")
    if thumb and _state["thumb_initial"] is not None:
        thumb.location=_state["thumb_initial"]
    bpy.context.view_layer.update()
    _state.update(original=None,calibrated=False,thumb_initial=None,thumb_calibrated=False,
                  proxy=None,ik=None,original_constraint_target=None)
    return "Restored original R IK goal, no scene saved"

def inspect():
    return "VQ04.04 film+finger target gap="+str(measure()["gap_to_offset_target_m"])+"m; calibrated="+str(_state["calibrated"] and measure()["gap_to_offset_target_m"]<=.003)
