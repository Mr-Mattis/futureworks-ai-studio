"""VQ04.03 limited, reversible hand-to-film kinematic reach calibration.

At frame 36 only, solve the EXISTING right-hand IK target so the R-index
fingertip pad center reaches a point 13mm in front of the current film vertex.
Only a kinematic target alignment test: NOT actual two-sided clamping,
friction, adhesive bonding, film physics or a safe thermal tool proof.

No changes are keyed or saved. Source scene and approved asset bytes untouched.
"""
import bpy, math
from mathutils import Vector
import fwai_hand_tool_preview as hands

TARGET="IK TARGET / R HAND"
TIP=hands.PREFIX+"R_index_fingerpad"
FILM="VINYL / partially adhered flexible sheet"
FRAME=36
VERTEX_INDEX=12*29
OFFSET=Vector((0,-.013,0))
_state={"original":None,"calibrated":False}

def _ref():
    if bpy.context.scene.frame_current!=FRAME:
        raise ValueError("Contact calibration is limited to frame 36 (reach pose)")
    if hands.COL not in bpy.data.collections:
        raise ValueError("Hand preview must be loaded")
    target=bpy.data.objects.get(TARGET)
    tip=bpy.data.objects.get(TIP)
    film=bpy.data.objects.get(FILM)
    if target is None or tip is None or film is None:
        raise ValueError("Required IK, hand or film target missing")
    if film.type!="MESH" or len(film.data.vertices)<=VERTEX_INDEX:
        raise ValueError("Film mesh topology has changed")
    return target,tip,film

def _position():
    _target,tip,film=_ref()
    bpy.context.view_layer.update()
    deps=bpy.context.evaluated_depsgraph_get()
    film_eval=film.evaluated_get(deps)
    tip_eval=tip.evaluated_get(deps)
    dest=film_eval.matrix_world@film_eval.data.vertices[VERTEX_INDEX].co + OFFSET
    actual=tip_eval.matrix_world.translation.copy()
    return dest,actual

def measure():
    desired,actual=_position()
    return {"frame":FRAME,"gap_m":round(float((desired-actual).length),6),
       "desired_film_surface_normal_offset_xyz":[round(float(v),5) for v in desired],
       "fingertip_center_xyz":[round(float(v),5) for v in actual],
       "is_contact_physics_certified":False}

def calibrate():
    target,_tip,_film=_ref()
    if _state["calibrated"]:
        active_gap=measure()["gap_m"]
        if active_gap<=.003:
            return "Kinematic fingertip already calibrated: gap="+str(active_gap)+"m"
        # A user can scrub Blender's native timeline outside this add-on.
        # That can reset the animated IK target; do not reuse a stale receipt.
        clear()
    original=target.location.copy()
    try:
        for _i in range(16):
            desired,actual=_position()
            error=desired-actual
            if error.length <=.003:break
            target.location+=error*.65
            if (target.location-original).length>.35:
                raise ValueError("IK target reach exceeds safe 35cm adjustment bound")
        desired,actual=_position()
        gap=(desired-actual).length
        if gap>.003:
            raise ValueError("Fingertip cannot reach film edge within 3mm: gap="+str(round(gap,4))+"m")
    except Exception:
        target.location=original
        bpy.context.view_layer.update()
        raise
    _state["original"]=original
    _state["calibrated"]=True
    return "Frame-36 fingertip kinematic reach achieved, gap="+str(round(gap,5))+"m; not physical grip"

def clear():
    if not _state["calibrated"]:return "No active kinematic contact correction"
    scene=bpy.context.scene
    frame=scene.frame_current
    scene.frame_set(FRAME)
    target=bpy.data.objects.get(TARGET)
    if target is not None:
        target.location=_state["original"]
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    _state["original"]=None
    _state["calibrated"]=False
    return "Restored original right-hand IK target; no source saved"

def inspect():
    gap=measure()["gap_m"]
    valid=_state["calibrated"] and gap<=.003
    return "Frame36 contact target gap="+str(gap)+"m, kinematic_only="+str(bool(valid))
