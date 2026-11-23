"""FWAI-B001 architecture v1: pure-Python parametric 3D OBJ, no image render.

Geometry is a CONCEPT, not structural engineering, egress approval or a
construction-ready model. No Blender, web APIs, GPU, environment generation,
physical materials, image synthesis or paid services are invoked.

Coordinates are defined in FEET in the JSON. Wavefront OBJ vertices are
exported in METERS and indexed deterministically.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path

FT=0.3048
TWOPI=2*math.pi

class DesignHold(ValueError): pass

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def validate(s):
    if s.get("schema")!="FWAI_B001_PARAMETRIC_GEOMETRY_V1":
        raise DesignHold("Geometry specification version mismatch")
    b=s["balcony"]; st=s["staircase"]
    if (b["length_ft"],b["depth_ft"],b["floor_elevation_ft"])!=(10,6,15):
        raise DesignHold("Owner's fixed balcony dimensions changed")
    if st["helix_count"]!=2 or not st["two_independent_paths"]:
        raise DesignHold("Two physically distinct walkable helical paths required")
    if st["movement_descending_top_view"]!="counterclockwise" or st["angle_sign"]!="positive_around_z_axis":
        raise DesignHold("User-selected counterclockwise descent changed")
    if st["inner_walking_radius_ft"]>=st["outer_walking_radius_ft"]:
        raise DesignHold("No walking width")
    width=st["outer_walking_radius_ft"]-st["inner_walking_radius_ft"]
    if not math.isclose(width,3.5,abs_tol=1e-7):
        raise DesignHold("User-selected 3.5ft walking width changed")
    if st["outer_support_radius_ft"]>6 or st["inner_support_radius_ft"]<0:
        raise DesignHold("Stair helix exceeds maximum 12ft diameter")
    if st["outer_walking_radius_ft"]<=st["inner_support_radius_ft"]:
        raise DesignHold("Inner ribbon collision")
    if st["outer_support_radius_ft"]<=st["outer_walking_radius_ft"]:
        raise DesignHold("Outer ribbon collision")
    if not math.isclose(st["entry_phase_radians_B"]-st["entry_phase_radians_A"],math.pi,abs_tol=1e-8):
        raise DesignHold("Double helices must be 180 degrees out of phase")
    if st["revolutions"]!=1 or st["treads_per_path"]!=24:
        raise DesignHold("Revision requires new headroom study")
    if not math.isclose(st["riser_height_ft"]*st["treads_per_path"],15,abs_tol=1e-8):
        raise DesignHold("Stair does not connect 15ft elevation")
    walkline_radius=st["inner_walking_radius_ft"]+1
    walkline_depth=walkline_radius*TWOPI/st["treads_per_path"]*12
    narrow_depth=st["inner_walking_radius_ft"]*TWOPI/st["treads_per_path"]*12
    headroom=st["rise_ft"]/2-st["tread_thickness_ft"]
    if headroom<st["clearance_design_target_ft"]:
        raise DesignHold("Analytic overlapping-path headroom below preliminary target")
    if st["central_axis"]!="open_void_no_vertical_column":
        raise DesignHold("No central structural spine was selected")
    if st.get("open_air") is not True or st.get("dna_expression")!="dramatic_true_double_helix_two_walking_paths":
        raise DesignHold("Open-air dramatic double-helix intent changed")
    if s.get("library_style")!="hybrid_monumental_organic_precision_dominant" or s.get("design_character")!="balanced_monumental_and_elegant":
        raise DesignHold("Owner-delegated future architecture language changed")
    if b.get("support")!="cantilever plus overhead tension":
        raise DesignHold("Hybrid balcony support requirement changed")
    perms=s["render_permissions"]
    if perms.get("geometry_only") is not True or any(perms[k] for k in (
        "material_rendering","environment_rendering","image_generation","external_upload","paid_api","publish"
    )):raise DesignHold("Unexpected rendering or publishing permission")
    if s["upper_transfer"]["status"]!="UNRESOLVED_GEOMETRY_HOLD":
        raise DesignHold("Upper far-entry bridge must not be silently accepted")
    return {
       "status":"PRELIMINARY_GEOMETRY_PARAMETERS_PASS",
       "stairs":2,"treads_per_path":24,"total_tread_solids":48,
       "balcony_length_ft":10,"balcony_depth_ft":6,
       "nominal_stair_envelope_diameter_ft":12.0,
       "nominal_walking_width_ft":round(width,3),
       "rise_in":round(st["riser_height_ft"]*12,3),
       "wedge_arc_depth_at_inner_edge_in":round(narrow_depth,3),
       "wedge_arc_depth_12in_from_inner_edge_in":round(walkline_depth,3),
       "other_staircase_elevation_separation_at_same_azimuth_ft":7.5,
       "approx_tread_only_headroom_ft":round(headroom,3),
       "headroom_limits":"Excludes handrail/transition bridge/lattice protrusions and physical compliance",
       "upper_second_entry":"NOT_CONNECTED_NEEDS_DESIGN",
       "accessibility_and_egress":"NOT_VALIDATED",
       "structural_feasibility":"NOT_VALIDATED",
       "real_life_like_visuals":"NOT_RENDERED"
    }

class Mesh:
    def __init__(self):
        self.points=[];self.faces=[];self.groups=[]
    def add(self,group,points,faces):
        start=len(self.points)
        self.points.extend([tuple(p) for p in points])
        for face in faces:
            if len(face)!=3:raise ValueError("Triangulated mesh only")
            if any(i>=len(points) or i<0 for i in face):raise ValueError("invalid face")
            self.faces.append(tuple(start+i for i in face));self.groups.append(group)
    def cuboid(self,group,x0,x1,y0,y1,z0,z1):
        if x0>=x1 or y0>=y1 or z0>=z1:raise ValueError("bad volume")
        p=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
           (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
        quads=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
        self.add(group,p,[tri for a,b,c,d in quads for tri in ((a,b,c),(a,c,d))])
    def tube(self,group,p,q,r,n=10):
        v=[q[k]-p[k] for k in range(3)]
        mag=math.sqrt(sum(x*x for x in v))
        if mag<1e-8:return
        u=[x/mag for x in v]
        axis=(1.,0.,0.) if abs(u[0])<.9 else (0.,1.,0.)
        x=(u[1]*axis[2]-u[2]*axis[1],u[2]*axis[0]-u[0]*axis[2],u[0]*axis[1]-u[1]*axis[0])
        xn=math.sqrt(sum(a*a for a in x));x=tuple(a/xn for a in x)
        y=(u[1]*x[2]-u[2]*x[1],u[2]*x[0]-u[0]*x[2],u[0]*x[1]-u[1]*x[0])
        verts=[]
        for center in (p,q):
            for i in range(n):
                t=TWOPI*i/n
                verts.append(tuple(center[k]+r*(math.cos(t)*x[k]+math.sin(t)*y[k]) for k in range(3)))
        faces=[]
        for i in range(n):
            nxt=(i+1)%n
            faces.extend(((i,nxt,n+nxt),(i,n+nxt,n+i)))
        for i in range(1,n-1):
            faces.append((0,i+1,i));faces.append((n,n+i,n+i+1))
        self.add(group,verts,faces)
    def round_platform(self,group,cx,cy,z,outer_radius,thickness,segments=48):
        points=[];faces=[]
        for zz in (z-thickness,z):
            points.extend([(cx+outer_radius*math.cos(TWOPI*i/segments),
                            cy+outer_radius*math.sin(TWOPI*i/segments),zz) for i in range(segments)])
        points.extend(((cx,cy,z-thickness),(cx,cy,z)))
        for i in range(segments):
            j=(i+1)%segments
            faces.extend(((segments*2+1,segments+i,segments+j),
                          (segments*2,j,i),(i,j,segments+j),(i,segments+j,segments+i)))
        self.add(group,points,faces)
    def tread_wedge(self,group,cx,cy,r0,r1,a0,a1,z,thickness,arc_sections=5):
        points=[]
        for zz in (z-thickness,z):
            for r in (r0,r1):
                for j in range(arc_sections+1):
                    a=a0+(a1-a0)*j/arc_sections
                    points.append((cx+r*math.cos(a),cy+r*math.sin(a),zz))
        n=arc_sections+1
        faces=[]
        # top and bottom annulus slices
        for j in range(arc_sections):
            for base,flip in ((0,True),(2*n,False)):
                a,b,c,d=base+j,base+n+j,base+n+j+1,base+j+1
                faces.extend(((a,c,b),(a,d,c)) if flip else ((a,b,c),(a,c,d)))
        # outer/inner radial profile sides
        for ring in (0,n):
            for j in range(arc_sections):
                a,b=ring+j,ring+j+1
                c,d=ring+2*n+j,ring+2*n+j+1
                faces.extend(((a,b,d),(a,d,c)))
        # radial end caps
        for j in (0,arc_sections):
            a,b=n+j,j;c,d=3*n+j,2*n+j
            faces.extend(((a,b,d),(a,d,c)))
        self.add(group,points,faces)
    def helical_ribbon(self,group,cx,cy,r,start,depth,radial_thickness=.13,height=1.05,N=96):
        # Side-mounted ribbons; no underside crossbeam in walking clearance.
        points=[]
        for i in range(N+1):
            t=i/N;th=start+TWOPI*t;z=15-depth*t
            for rr,zz in ((r-radial_thickness/2,z-height),(r+radial_thickness/2,z-height),
                          (r+radial_thickness/2,z),(r-radial_thickness/2,z)):
                points.append((cx+rr*math.cos(th),cy+rr*math.sin(th),zz))
        faces=[]
        for i in range(N):
            a=4*i;b=4*(i+1)
            for k in range(4):
                l=(k+1)%4
                faces.extend(((a+k,a+l,b+l),(a+k,b+l,b+k)))
        faces.extend(((0,2,1),(0,3,2)))
        end=4*N;faces.extend(((end,end+1,end+2),(end,end+2,end+3)))
        self.add(group,points,faces)
    def obj(self):
        lines=["# FWAI-B001 parametric ARCHITECTURAL CONCEPT / not rendered",
               "# Units: meters; right-handed xyz, z-up; groups = distinct parts"]
        for x,y,z in self.points:
            lines.append(f"v {x*FT:.6f} {y*FT:.6f} {z*FT:.6f}")
        prev=None
        for g,face in zip(self.groups,self.faces):
            if g!=prev:
                lines.append("g "+g);prev=g
            lines.append("f "+" ".join(str(i+1) for i in face))
        return ("\n".join(lines)+"\n").encode()

def scene(spec):
    v=validate(spec);m=Mesh()
    b=spec["balcony"]; s=spec["staircase"]
    z=b["floor_elevation_ft"]; cx,cy=s["axis_center_ft"]
    # Balcony 10 x 6, with two actual openings filled by distinct glazing solids.
    # No double-stacked opaque floor beneath the transparent observation panels.
    for y0,y1 in ((0,1.8),(4.2,6)):
        m.cuboid("BALCONY_OPAQUE_COMPOSITE_SLAB",-5,5,y0,y1,z-.42,z)
    for x0,x1 in ((-5,-3.6),(-2.0,2.0),(3.6,5)):
        m.cuboid("BALCONY_OPAQUE_COMPOSITE_SLAB",x0,x1,1.8,4.2,z-.42,z)
    for x0,x1 in ((-3.6,-2.0),(2.0,3.6)):
        m.cuboid("BALCONY_GLASS_OBSERVATION_PANEL",x0,x1,1.8,4.2,z-.29,z-.05)
    m.cuboid("UPPER_SHARED_TRANSFER_LANDING", -3.7,3.7,6,9.5,z-.42,z)
    for x in (-4.0,4.0):
        m.cuboid("LIBRARY_CANTILEVER_ANCHOR_BEAM",x-.22,x+.22,-1.5,5.75,z-.9,z-.42)
    for x in (-4.5,4.5):
        m.tube("OVERHEAD_TENSION_MEMBER", (x,.0,27),(x,5.8,z+.05),.095)
        m.cuboid("LIBRARY_SUPERSTRUCTURE_ANCHOR_PROXY",x-.22,x+.22,-.35,.0,26.5,27.5)
        m.cuboid("BALCONY_TENSION_CLEVIS_PROXY",x-.28,x+.28,5.4,6.0,z-.15,z+.2)
    # Guard 3.5ft high at sides and front corners; center open to transfer landing.
    for x in (-4.9,4.9):
        for y in (0.3,1.7,3.2,4.7,5.9):
            m.tube("BALCONY_GUARD_POSTS",(x,y,z),(x,y,z+3.5),.055)
        m.tube("BALCONY_GUARD_TOP_RAIL",(x,0.3,z+3.5),(x,5.9,z+3.5),.08)
        m.cuboid("BALCONY_GLAZED_GUARD_INFILL",x-.035,x+.035,0.35,5.85,z+.38,z+3.27)
    for a,bb in ((-5,-3.7),(3.7,5)):
        m.tube("BALCONY_FRONT_GUARD", (a,5.98,z+3.5),(bb,5.98,z+3.5),.085)
    # Structure-only courtyard arrival slab: NOT a generated garden/environment.
    m.round_platform("COURTYARD_COMMON_ARRIVAL_PLATFORM_ONLY",cx,cy,0,7,.22)
    n=s["treads_per_path"];dtheta=TWOPI/n
    for j,name in enumerate(("A","B")):
        phase=s["entry_phase_radians_A"] if j==0 else s["entry_phase_radians_B"]
        for i in range(n):
            a0=phase+dtheta*i;a1=phase+dtheta*(i+1)
            step_z=s["rise_ft"]-(i+1)*s["riser_height_ft"]
            m.tread_wedge(f"STAIR_{name}_TREAD_{i+1:02d}",cx,cy,
                 s["inner_walking_radius_ft"],s["outer_walking_radius_ft"],
                 a0,a1,step_z,s["tread_thickness_ft"])
        for side,rr in (("INNER",s["inner_support_radius_ft"]),
                        ("OUTER",s["outer_support_radius_ft"])):
            m.helical_ribbon(f"STAIR_{name}_{side}_STRUCTURAL_RIBBON",cx,cy,rr,phase,s["rise_ft"])
            # Helical rail runs 3.5ft above treads; 96 segments each, separate from ribbons.
            for i in range(96):
                def rail(i):
                    t=i/96; th=phase+TWOPI*t
                    return (cx+rr*math.cos(th),cy+rr*math.sin(th),
                            s["rise_ft"]-s["rise_ft"]*t+s["guard_height_ft"])
                m.tube(f"STAIR_{name}_{side}_CURVED_HANDRAIL",rail(i),rail(i+1),.06,7)
            for i in range(n+1):
                t=i/n; th=phase+TWOPI*t
                x=cx+rr*math.cos(th);y=cy+rr*math.sin(th)
                zz=s["rise_ft"]-s["rise_ft"]*t
                m.tube(f"STAIR_{name}_{side}_GUARD_STANCHIONS",
                       (x,y,zz-.45),(x,y,zz+s["guard_height_ft"]),.055,8)
        # Spatial open-lattice diagonals on the OUTSIDE of the walking envelope.
        rr=s["outer_support_radius_ft"]
        for i in range(0,n,2):
            t=i/n;th=phase+TWOPI*t
            q=(i+1.2)/n;end=phase+TWOPI*q
            p0=(cx+rr*math.cos(th),cy+rr*math.sin(th),s["rise_ft"]-s["rise_ft"]*t-.75)
            p1=(cx+rr*math.cos(end),cy+rr*math.sin(end),s["rise_ft"]-s["rise_ft"]*q+.85)
            m.tube(f"STAIR_{name}_OPEN_PRECISION_LATTICE",p0,p1,.07,7)
    return m,v

def build(spec_path,destination):
    source=Path(spec_path);spec=json.loads(source.read_text())
    model,quality=scene(spec)
    out=Path(destination);out.mkdir(parents=True,exist_ok=True)
    obj=out/"FWAI-B001_parametric_3d_concept_v1.obj"
    obj.write_bytes(model.obj())
    receipt={
      "schema":"FWAI_B001_3D_GEOMETRY_RECEIPT_V1","source_sha256":digest(source),
      "obj_file":obj.name,"obj_sha256":digest(obj),
      "obj_units":"meters","model_vertices":len(model.points),"model_triangles":len(model.faces),
      "distinct_part_groups":len(set(model.groups)),"parametric_quality":quality,
      "material_render_created":False,"environment_created":False,"paid_calls":0,
      "human_design_approval":False,"milestone":"OWNER_ARCHITECTURE_REVIEW",
      "hold":"Upper B-entry bridge not modeled/validated; no public safety/code approval"}
    (out/"FWAI-B001_3d_validation_receipt.json").write_text(json.dumps(receipt,indent=2))
    return receipt

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("spec");p.add_argument("output")
    args=p.parse_args()
    print(json.dumps(build(args.spec,args.output),indent=2))
