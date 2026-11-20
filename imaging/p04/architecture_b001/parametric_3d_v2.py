"""FWAI-B001 v2: right-side perimeter suspended skybridge to true Helix B.

A *geometry-only* parametric amendment to the owner's beloved v1 structure.
Original v1 remains immutable. This builds actual 3D volumes for the new
walkway, connector, guards, support proxies and upper entry aperture.
No graphics/image rendering, materials, environments, paid APIs or publishing.

Dimension units: feet internally, meters in exported Wavefront OBJ.
Architectural circulation connectivity is only preliminary XY topology;
3D collision, structure, accessibility and safety MUST be reviewed separately.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from . import parametric_3d as v1

V1_SHA="0f8d4d084687245412aca5009a189624f2dfebb98d3cd7191565bf9b74cbd571"
VERSION="FWAI_B001_PARAMETRIC_GEOMETRY_V2"
PI=math.pi
BASE=Path(__file__).resolve().parent
V1_SPEC=BASE/"FWAI-B001_geometry_v1.json"

class SkybridgeRejected(v1.DesignHold):pass

def near(a,b,tolerance=1e-6):
    return math.isclose(a,b,abs_tol=tolerance)

def validate(s):
    if s.get("schema")!=VERSION or s.get("v1_geometry_source_sha256")!=V1_SHA:
        raise SkybridgeRejected("Unknown v2 branch geometry or untracked owner-source")
    if v1.digest(V1_SPEC)!=V1_SHA:
        raise SkybridgeRejected("Original v1 owner-reviewed parametric geometry has changed")
    v1s=json.loads(V1_SPEC.read_text())
    for k in ("balcony","staircase","support","library_style","design_character","coordinates","courtyard","render_permissions"):
        if s.get(k)!=v1s.get(k):
            raise SkybridgeRejected(f"Unauthorized revision to owner-reviewed {k}")
    # v1 remains HOLD; v2 earns only a preliminary connectivity proposal.
    normalized=dict(s)
    normalized["schema"]="FWAI_B001_PARAMETRIC_GEOMETRY_V1"
    normalized["upper_transfer"]=v1s["upper_transfer"]
    original=v1.validate(normalized)
    p=s.get("upper_transfer",{})
    if p.get("status")!="MODELED_WITH_REVIEW_HOLD":
        raise SkybridgeRejected("Design signoff must not be implied")
    if p.get("branching_strategy")!="peripheral_suspended_link_outside_stair_diameter":
        raise SkybridgeRejected("Unrecognized top transfer type")
    if p.get("side")!="right_when_facing_courtyard_from_library":
        raise SkybridgeRejected("Bridge side not approved")
    if p.get("finish")!="peripheral_guarded_curved_walkway_with_radial_B_connection":
        raise SkybridgeRejected("Missing outer branch or radial access")
    st=s["staircase"]; b=s["balcony"]
    rin=p.get("inner_radius_ft"); rout=p.get("outer_radius_ft")
    if any(type(x) not in (int,float) for x in (rin,rout)):
        raise SkybridgeRejected("Bridge radii must be numeric")
    if rin<=st["outer_support_radius_ft"]+.65 or rout-rin<3.5:
        raise SkybridgeRejected("Insufficient bridge-to-stair horizontal separation or walking width")
    if rout>12 or rin<6.9:
        raise SkybridgeRejected("Unsupported peripheral walkway span")
    if not near(p.get("walking_width_ft"),3.5) or not near(rout-rin,p["walking_width_ft"]):
        raise SkybridgeRejected("Walkway not the approved 3.5ft nominal clear width")
    if not near(p.get("start_angle_rad"),-PI/2) or not near(p.get("end_angle_rad"),PI/2):
        raise SkybridgeRejected("Skybridge must wrap right-hand side for 180-degree phase offset")
    if not near(p.get("deck_top_z_ft"),b["floor_elevation_ft"]):
        raise SkybridgeRejected("Upper bridge requires level transition")
    if not (.3<=p.get("deck_thickness_ft",0)<=.7):
        raise SkybridgeRejected("Deck volumetric thickness missing")
    if not near(p.get("guard_center_offset_ft",0),.13):
        raise SkybridgeRejected("Guard posts must be located outside the nominal clear pedestrian band")
    if p.get("entry_A_threshold_x_ft")!=[-1.75,1.75]:
        raise SkybridgeRejected("A transfer width must remain 3.5ft")
    if p.get("entry_B_radial_connector_x_ft")!=[-1.75,1.75]:
        raise SkybridgeRejected("B transfer width must remain 3.5ft")
    cy=st["axis_center_ft"][1];outer_stair=st["outer_walking_radius_ft"]
    by0,by1=p["entry_B_radial_connector_y_ft"]
    if not (by0<=cy+outer_stair-.1 and by1>=cy+rin+.1):
        raise SkybridgeRejected("Radial B connector does not overlap both walking surfaces")
    ay0,ay1=p["entry_A_threshold_y_ft"]
    if not (ay0<=9.5 and ay1>=cy-outer_stair+.1):
        raise SkybridgeRejected("A threshold does not bridge top step")
    if not (cy-rin<=9.3 and cy-rout<=6.0):
        raise SkybridgeRejected("Near upper landing does not overlap curved bridge")
    if (p.get("guard_gap_outer_B_rail_segments")!=10
        or p.get("guard_gap_outer_B_post_count")!=3
        or p.get("guard_gap_bridge_inner_rail_segments_at_each_end")!=8):
        raise SkybridgeRejected("Entry aperture and continuous guard geometry not yet revalidated")
    if p.get("engineering_status")!="tension_anchor_and_load_path_unverified":
        raise SkybridgeRejected("Uncertified design must remain unapproved")
    if s["review_status"]!="DESIGN_PROTOTYPE_V2_OWNER_REVIEW_REQUIRED":
        raise SkybridgeRejected("Human geometry acceptance must remain pending")
    gap=rin-st["outer_support_radius_ft"]
    result=dict(original)
    result.update({
       "status":"BRIDGE_PROVISIONAL_GEOMETRY_TOPOLOGY_PASS",
       "revision":"v2_top_branch_peripheral_right",
       "bridge_centerline_radius_ft":round((rin+rout)/2,3),
       "bridge_clear_radial_width_ft":round(rout-rin,3),
       "outer_bridge_diameter_ft":round(2*rout,3),
       "stair_outer_diameter_unchanged_ft":12.0,
       "minimum_non_entry_horizontal_bridge_to_stair_ribbon_gap_ft":round(gap,3),
       "bridge_arc_turn_degrees":180,
       "near_entrance_overlaps_shared_landing":True,
       "far_connector_overlaps_bridge_and_helix_B_entry":True,
       "entry_B_gate":"GUARD_AND_RIBBON_APERTURE_PROVISIONAL",
       "upper_second_entry":"CONNECTED_IN_PRELIMINARY_XY_TOPOLOGY_ONLY",
       "full_3d_interference_validated":False,
       "load_path_certified":False,
       "public_egress_or_accessibility_validated":False,
       "human_design_approval":False
    })
    return result

def open_helix_B_outer_entry(mesh):
    """Remove first gate spans of B's perimeter guard & ribbon; replace ribbon
    with a later-starting capped segment. A load transfer via bridge gusset
    is added separately; this is still NOT a structural analysis.
    """
    groups=mesh.groups
    counts={}
    kept_faces=[];kept_groups=[]
    removed={}
    to_remove={
       "STAIR_B_OUTER_CURVED_HANDRAIL":10*(4*7-4), # first 10 rail tubes (7-sided)
       "STAIR_B_OUTER_GUARD_STANCHIONS":3*(4*8-4), # first three posts (8-sided)
       "STAIR_B_OUTER_STRUCTURAL_RIBBON":10*8, # initial 10 of 96 mesh strips
    }
    for face,group in zip(mesh.faces,groups):
        idx=counts.get(group,0);counts[group]=idx+1
        if group in to_remove and idx<to_remove[group]:
            removed[group]=removed.get(group,0)+1
            continue
        if group=="STAIR_B_OUTER_STRUCTURAL_RIBBON" and idx>=96*8:
            # original cap triangles are at t=0 and t=1; remove the
            # original t=0 cap; the replacement terminal closure follows.
            # We keep end cap triangles; v2 adds a new cap at t=10/96.
            if idx in (96*8,96*8+1):
                removed[group]=removed.get(group,0)+1
                continue
        kept_faces.append(face);kept_groups.append(group)
    mesh.faces=kept_faces;mesh.groups=kept_groups
    expected=dict(to_remove)
    expected["STAIR_B_OUTER_STRUCTURAL_RIBBON"]+=2  # original endcap removed as well
    if removed!=expected:
        raise SkybridgeRejected("Helix B entry aperture doesn't match expected primitive topology")
    return removed

def portal_endcap(mesh, cx,cy,r,phase,t=.10416666666666667):
    """Close the cut ribbon end face with two triangles, physically modeled."""
    theta=phase+2*PI*t;z=15-15*t;rad=.13/2;h=1.05
    pts=[]
    for rr,zz in ((r-rad,z-h),(r+rad,z-h),(r+rad,z),(r-rad,z)):
        pts.append((cx+rr*math.cos(theta),cy+rr*math.sin(theta),zz))
    mesh.add("STAIR_B_OUTER_RIBBON_CUT_PORTAL_FACE",pts,[(0,1,2),(0,2,3)])

def tube_arc(mesh,group,cx,cy,r,phase1,phase2,z,radius,segments=48):
    for i in range(segments):
        a=phase1+(phase2-phase1)*i/segments
        b=phase1+(phase2-phase1)*(i+1)/segments
        mesh.tube(group,(cx+r*math.cos(a),cy+r*math.sin(a),z),
                  (cx+r*math.cos(b),cy+r*math.sin(b),z),radius,8)

def bridge_model(spec):
    check=validate(spec)
    normalized=dict(spec)
    normalized["schema"]="FWAI_B001_PARAMETRIC_GEOMETRY_V1"
    normalized["upper_transfer"]=json.loads(V1_SPEC.read_text())["upper_transfer"]
    mesh,_=v1.scene(normalized)
    p=spec["upper_transfer"]; s=spec["staircase"]
    cx,cy=s["axis_center_ft"]
    z=p["deck_top_z_ft"];r0=p["inner_radius_ft"];r1=p["outer_radius_ft"]
    a0=p["start_angle_rad"];a1=p["end_angle_rad"]
    n=48
    # Actual spatial floor solids: separate from the original stair diameter.
    for i in range(n):
        first=a0+(a1-a0)*i/n
        last=a0+(a1-a0)*(i+1)/n
        mesh.tread_wedge("PERIPHERAL_SKYBRIDGE_CURVED_DECK",cx,cy,r0,r1,
                         first,last,z,p["deck_thickness_ft"],arc_sections=4)
    # Curved metal edge girders underneath both sides of the path.
    for name,r_edge in (("INNER",r0),("OUTER",r1)):
        tube_arc(mesh,"SKYBRIDGE_"+name+"_TORSION_EDGE_GIRDER",cx,cy,r_edge,a0,a1,z-.53,.19)
        # Set the railing outside the deck edges, protecting 3.5ft of
        # nominal unobstructed radial walking width at the guard line.
        offset=p["guard_center_offset_ft"]*(-1 if name=="INNER" else 1)
        r=r_edge+offset
        # A 3.5ft above-deck handrail with a pedestrian gateway at both ends
        # of the INNER rail; the OUTER rail is continuous.
        for i in range(n):
            if name=="INNER" and (i<8 or i>=n-8):
                continue
            t=i/n;u=(i+1)/n
            theta=a0+(a1-a0)*t;end=a0+(a1-a0)*u
            mesh.tube("SKYBRIDGE_"+name+"_GUARD_HANDRAIL",
                      (cx+r*math.cos(theta),cy+r*math.sin(theta),z+3.5),
                      (cx+r*math.cos(end),cy+r*math.sin(end),z+3.5),.07,8)
        for i in range(n//2+1):
            if name=="INNER" and (i<4 or i>=n//2-3):
                continue
            th=a0+(a1-a0)*i/(n//2)
            x=cx+r*math.cos(th);y=cy+r*math.sin(th)
            mesh.tube("SKYBRIDGE_"+name+"_GUARD_POSTS",(x,y,z),
                      (x,y,z+3.5),.055,8)
    # Canted cross-members UNDER the deck support the inner/outer girders.
    for i in range(4,44,4):
        angle=a0+(a1-a0)*i/n
        mesh.tube("SKYBRIDGE_RADIAL_UNDERDECK_LATTICE",
                   (cx+r0*math.cos(angle),cy+r0*math.sin(angle),z-.64),
                   (cx+r1*math.cos(angle),cy+r1*math.sin(angle),z-.64),.095,8)
    # The original balcony remains 10x6ft; only separate branch circulation
    # geometry is added beyond its perimeter.
    xa,xb=p["entry_A_threshold_x_ft"];ya,yb=p["entry_A_threshold_y_ft"]
    mesh.cuboid("TRANSFER_TO_HELIX_A_ENTRY_THRESHOLD",
                xa,xb,ya,yb,z-.3,z)
    xa,xb=p["entry_B_radial_connector_x_ft"]
    ya,yb=p["entry_B_radial_connector_y_ft"]
    mesh.cuboid("TRANSFER_TO_HELIX_B_RADIAL_LANDING",
                xa,xb,ya,yb,z-p["deck_thickness_ft"],z)
    for x in (xa-p["guard_center_offset_ft"],xb+p["guard_center_offset_ft"]):
        mesh.tube("TRANSFER_TO_HELIX_B_SIDE_GUARD",
                  (x,ya,z+3.5),(x,yb,z+3.5),.07,8)
        for y in (ya,yb):
            mesh.tube("TRANSFER_TO_HELIX_B_GUARD_POST",(x,y,z),(x,y,z+3.5),.06,8)
    removed=open_helix_B_outer_entry(mesh)
    # A real opening replaces the outer B guard at top, where the landing
    # connects. A short portal end plate / transfer beam flags load path.
    phi=s["entry_phase_radians_B"]
    rr=s["outer_support_radius_ft"]
    t=10/96
    portal_endcap(mesh,cx,cy,rr,phi,t)
    th=phi+2*PI*t
    near_ribbon=(cx+rr*math.cos(th),cy+rr*math.sin(th),15-15*t-.85)
    near_bridge=(cx+r0*math.cos(phi),cy+r0*math.sin(phi),z-.57)
    mesh.tube("SKYBRIDGE_TO_HELIX_B_PORTAL_GUSSET_PROXY",near_bridge,near_ribbon,.17,10)
    # Flared guard return follows the new outer entry opening and joins the
    # descending handrail. It is an architectural guard proposal only.
    q0=(xa-p["guard_center_offset_ft"],ya,z+3.5)
    q2=(cx+rr*math.cos(th),cy+rr*math.sin(th),15-15*t+s["guard_height_ft"])
    q1=((q0[0]+q2[0])/2,(q0[1]+q2[1])/2,(q0[2]+q2[2])/2)
    mesh.tube("STAIR_B_ENTRY_FLARED_GUARD_RETURN",q0,q1,.07,8)
    mesh.tube("STAIR_B_ENTRY_FLARED_GUARD_RETURN",q1,q2,.07,8)
    # Decorative detail must have a traceable proposed building load path.
    # The real load-bearing sufficiency of these long suspension ties is
    # intentionally NOT certified.
    for idx,t in enumerate((.30,.68)):
        th=a0+(a1-a0)*t
        attach=(cx+r1*math.cos(th),cy+r1*math.sin(th),z+.12)
        anchor=(3.6+idx*.6,-.55,30.0+idx*1.0)
        mesh.tube("SKYBRIDGE_OVERHEAD_SUSPENSION_TIE_PROXY",anchor,attach,.105,9)
        mesh.cuboid("LIBRARY_UPPER_PRIMARY_ANCHOR_PROXY",
                    anchor[0]-.27,anchor[0]+.27,anchor[1]-.22,
                    anchor[1]+.22,anchor[2]-.3,anchor[2]+.3)
        mesh.tube("SKYBRIDGE_TENSION_CLEVIS_PROXY",
                  (attach[0],attach[1],attach[2]-.15),
                  (attach[0],attach[1],attach[2]+.15),.17,8)
    check.update({
      "new_3d_bridge_surface":"PRODUCED",
      "bridge_deck_sweep_sections":n,
      "bridge_entry_guard_aperture":removed,
      "fully_certified_connection":False,
      "structural_and_safety_clearance":"NOT_TESTED"
    })
    return mesh,check

def build(spec_path,out):
    spec_path=Path(spec_path)
    spec=json.loads(spec_path.read_text())
    m,quality=bridge_model(spec)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    obj=out/"FWAI-B001_parametric_3d_concept_v2.obj"
    obj.write_bytes(m.obj())
    result={
      "schema":"FWAI_B001_3D_GEOMETRY_RECEIPT_V2",
      "design_id":spec["design_id"],
      "spec_sha256":v1.digest(spec_path),
      "v1_source_sha256":V1_SHA,
      "obj_file":obj.name,
      "obj_sha256":v1.digest(obj),
      "obj_units":"meters",
      "model_vertices":len(m.points),
      "model_triangles":len(m.faces),
      "distinct_part_groups":len(set(m.groups)),
      "geometry_quality":quality,
      "owner_visual_acceptance":False,
      "full_collision_qa":"NOT_DONE",
      "stair_code_compliance":"NOT_VALIDATED",
      "structural_load_analysis":"NOT_DONE",
      "physical_construction_authorized":False,
      "materials_rendered":False,
      "environment_rendered":False,
      "paid_api_calls":0,
      "external_upload":False,
      "publishing":False,
      "next_gate":"OWNER_V2_ARCHITECTURAL_REVIEW"
    }
    (out/"FWAI-B001_v2_validation_receipt.json").write_text(json.dumps(result,indent=2))
    return result

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("spec");ap.add_argument("output")
    args=ap.parse_args()
    print(json.dumps(build(args.spec,args.output),indent=2))
