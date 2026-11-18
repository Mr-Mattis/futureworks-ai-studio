"""P04.06 deterministic subject-first geometry/engineering acceptance.

Creates a vector orthographic blueprint and transparent subject silhouette;
it does NOT synthesize photoreal photographs or infer physical feasibility.
No ComfyUI, paid provider, network, production, or publishing operations.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
from xml.etree import ElementTree as ET

NS="http://www.w3.org/2000/svg"
ET.register_namespace("",NS)
class GeometryRejected(ValueError): pass
def digest(raw:bytes)->str: return hashlib.sha256(raw).hexdigest()
def dist(a,b):return math.hypot(a[0]-b[0],a[1]-b[1])
def check(spec):
    if spec.get("schema")!="FWAI_TECH_GEOMETRY_1":raise GeometryRejected("Unsupported schema")
    if spec.get("scene_type")!="isolated_subject" or spec.get("environment") is not None:
        raise GeometryRejected("Technology stage may not contain environment")
    if spec.get("military") is not False or spec.get("purpose")!="civilian_orbital_construction":
        raise GeometryRejected("Purpose not authorized")
    diameter=spec.get("truss_ring_diameter_m")
    if type(diameter) not in (int,float) or not 15<=diameter<=60:raise GeometryRejected("Unreasonable bounding diameter")
    ring=spec["ring"]
    if len(ring)!=6 or any(len(p)!=2 or any(type(v) not in (int,float) for v in p) for p in ring):
        raise GeometryRejected("Six numeric outer nodes required")
    if min(dist(p,(0,0)) for p in ring)<0.35*diameter or max(dist(p,(0,0)) for p in ring)>0.55*diameter:
        raise GeometryRejected("Six nodes must form defined scaled perimeter")
    if any(dist(ring[i],ring[j])<diameter*.3 for i in range(6) for j in range(i+1,6)):
        raise GeometryRejected("Duplicate or collapsed structural anchors")
    arms=spec.get("fabrication_arms",[])
    if len(arms)!=6 or set(a.get("anchor") for a in arms)!=set(range(6)):
        raise GeometryRejected("Six independently anchored manipulators required")
    for arm in arms:
        joints=arm.get("joints",[])
        if len(joints)!=3 or any(len(j)!=2 for j in joints):raise GeometryRejected("Each arm needs 3 joints")
        if dist(joints[0],ring[arm["anchor"]])>0.001:raise GeometryRejected("Manipulator detached from truss")
        lengths=[dist(joints[i],joints[i+1]) for i in range(2)]
        if any(l<1.0 or l>diameter*.45 for l in lengths):
            raise GeometryRejected("Invalid actuation linkage span")
        if any(dist(j,(0,0))>diameter*.65 for j in joints):
            raise GeometryRejected("Manipulator outside defined subject footprint")
    bay=spec.get("crew_access",{})
    if bay.get("type")!="maintenance_airlock" or not 1.6<=bay.get("width_m",0)<=2.5:
        raise GeometryRejected("Human-scale hatch/airlock reference missing")
    if bay.get("location")!="central_hub":raise GeometryRejected("Hatch must attach to machine")
    if len(spec.get("radiators",[]))!=6:raise GeometryRejected("Six thermal radiators required")
    for node in spec["radiators"]:
        if node not in range(6):raise GeometryRejected("Radiator anchor not on structure")
    if spec.get("weapons") or spec.get("camouflage"):raise GeometryRejected("Military features forbidden")
    return {"status":"GEOMETRY_QA_PASS","design_id":spec["design_id"],
            "truss_ring_diameter_m":diameter,"fabrication_arms":6,"hinged_segments":12,
            "radiators":6,"crew_access_width_m":bay["width_m"],
            "environment_excluded":True,"real_world_feasibility":"NOT_VALIDATED",
            "manufacturing_certified":False,"human_visual_approval":False,
            "production_approved":False}
def el(tag,parent,**attrs):
    return ET.SubElement(parent,f"{{{NS}}}{tag}",{k.replace("_","-"):str(v) for k,v in attrs.items()})
def diagram(spec,*,mask=False):
    check(spec)
    # Model in meters; SVG viewport is engineering coordinates scaled to pixels.
    size=1200; scale=19; cx=cy=600
    svg=ET.Element(f"{{{NS}}}svg",{"width":"1200","height":"1200","viewBox":"0 0 1200 1200",
        "role":"img","aria-label":"Orthographic orbital construction platform geometry blueprint"})
    def pos(p):return (round(cx+p[0]*scale,2),round(cy-p[1]*scale,2))
    def line(a,b,**kw):
        x1,y1=pos(a);x2,y2=pos(b)
        return el("line",svg,x1=x1,y1=y1,x2=x2,y2=y2,**kw)
    def circle(p,r,**kw):
        x,y=pos(p);return el("circle",svg,cx=x,cy=y,r=r*scale,**kw)
    def label(p,s,color="#d6edff",size=17):
        x,y=pos(p);t=el("text",svg,x=x,y=y,fill=color,font_size=size,
                        font_family="DejaVu Sans");t.text=s
    nodes=spec["ring"]
    ringcoords=" ".join(",".join(str(v) for v in pos(n)) for n in nodes)
    el("polygon",svg,points=ringcoords,fill=("#ffffff" if mask else "#253d50"),
       stroke=("#ffffff" if mask else "#81b8ca"),stroke_width=18 if mask else 9)
    for i in range(6):
        line((0,0),nodes[i],stroke="#ffffff" if mask else "#5d8997",stroke_width=11 if mask else 6)
        circle(nodes[i],.75,fill="#ffffff" if mask else "#d0d4d2",stroke="none")
        if not mask:label((nodes[i][0]*1.09,nodes[i][1]*1.09),f"R{i+1}",size=15)
    circle((0,0),4.2,fill="#ffffff" if mask else "#9fb4b5",
           stroke="none" if mask else "#153b4d",stroke_width=5)
    for a in spec["fabrication_arms"]:
        joints=a["joints"]
        for first,second in zip(joints,joints[1:]):
            line(first,second,stroke="#ffffff" if mask else "#dad5c8",
                 stroke_width=36 if mask else 17,stroke_linecap="round")
        for j in joints[1:]:
            circle(j,.68,fill="#ffffff" if mask else "#efb86c",stroke="none")
    for i in spec["radiators"]:
        n=nodes[i]; out=(n[0]*1.10,n[1]*1.10)
        line(n,out,stroke="#ffffff" if mask else "#8ec0ca",stroke_width=24 if mask else 10)
    if not mask:
        label((-29,28),"FWAI-T001  |  ORBITAL LATTICE WEAVER",size=22)
        label((-29,25.7),"TOP VIEW  •  ISOLATED SUBJECT  •  SPECULATIVE",size=14)
        label((-28,-27),"40 m truss ring diameter | 2.0 m human-scale airlock",size=16)
        line((-28,-25),(-23,-25),stroke="#ffffff",stroke_width=5)
        label((-28,-23),"5 m scale",size=15)
        label((-29,-29),"NOT A PHYSICS OR STRUCTURAL CERTIFICATION",size=13)
    return ET.tostring(svg,encoding="utf-8",xml_declaration=True)
def produce(spec_path,out_dir):
    source=Path(spec_path)
    spec=json.loads(source.read_text())
    result=check(spec)
    output=Path(out_dir);output.mkdir(parents=True,exist_ok=True)
    artifacts={}
    for key,mask in (("blueprint",False),("subject_mask",True)):
        f=output/(spec["design_id"]+"_"+key+".svg")
        raw=diagram(spec,mask=mask);f.write_bytes(raw)
        artifacts[key]={"path":f.name,"sha256":digest(raw)}
    record={"schema":"FWAI_TECH_GEOMETRY_RECEIPT_1",
            "source_sha256":digest(source.read_bytes()),"geometry":result,"artifacts":artifacts,
            "next_gate":"MECHANICAL_FUNCTION_QA",
            "environment_generation_allowed":False,
            "material_rendering_allowed":False,
            "owner_approval_required":True}
    (output/(spec["design_id"]+"_geometry_receipt.json")).write_text(json.dumps(record,indent=2))
    return record
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("spec");p.add_argument("output")
    a=p.parse_args();print(json.dumps(produce(a.spec,a.output),indent=2))
