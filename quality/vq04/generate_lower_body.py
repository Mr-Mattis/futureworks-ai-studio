"""Deterministic, data-only mech lower-body geometry improvement payload.
All units in meters. Does not rewrite approved FWAI-M001 V2 design imagery.
"""
from pathlib import Path
import json,hashlib,math,os,tempfile
ASSET="FWAI_M001_LOWER_BODY_DETAIL_V1"
CANON_SHA="480263bdd7637bfb2d90cc2deecdeb616eef03492a35216dbebfd3b1f44c555c"
OUT=Path.home()/"Documents"/"futureworks-vq04"/"staging"
parts=[]
mx,my=-1.93,-.86
def v(vs):return [round(float(x),5) for x in vs]
def rod(name,side,bone,material,a,b,r):
    parts.append({"name":side+"_"+name,"shape":"rod","bone":side+"_"+bone,
        "material":material,"a":v(a),"b":v(b),"radius":r})
for side,off in (("L",-.16),("R",.16)):
    yy=my+off
    hip=(mx,yy,1.025);knee=(mx+.035,yy,.58);ankle=(mx+.09,yy,.17)
    # Front/back paired structural rails with two-tone cylindrical actuators.
    for index,delta in enumerate((-.064,.064)):
        rname="front" if index==0 else "rear"
        rod("thigh_guard_"+rname,side,"thigh","plum",
            (mx+.006,yy+delta,.96),(mx+.025,yy+delta,.64),.036)
        rod("thigh_actuator_"+rname,side,"thigh","titanium",
            (mx+.008,yy+delta*.75,.92),(mx+.02,yy+delta*.75,.70),.020)
        rod("shin_guard_"+rname,side,"shin","plum",
            (mx+.049,yy+delta,.53),(mx+.083,yy+delta,.24),.033)
        rod("shin_telescope_"+rname,side,"shin","titanium",
            (mx+.056,yy+delta*.65,.49),(mx+.074,yy+delta*.65,.30),.016)
    # Cyan linear coolant lighting routed down the existing leg surfaces.
    rod("coolant_thigh",side,"thigh","cyan",
        (mx-.035,yy-.075,.96),(mx+.011,yy-.075,.70),.011)
    rod("coolant_shin",side,"shin","cyan",
        (mx+.007,yy-.075,.51),(mx+.075,yy-.075,.25),.009)
    # Concentric segmented pivot rings. These visually emphasize actual knee hinge.
    for label,(x,y,z),rad,bone,material in (
        ("knee",knee,.102,"thigh","titanium"),
        ("ankle",ankle,.071,"shin","graphite")):
        for i in range(8):
            t0=2*math.pi*i/8;t1=2*math.pi*(i+1)/8
            a=(x+rad*math.cos(t0),y-.080,z+rad*math.sin(t0))
            b=(x+rad*math.cos(t1),y-.080,z+rad*math.sin(t1))
            rod(label+"_pivot_arc_"+str(i),side,bone,material,a,b,.011 if label=="knee" else .009)
    # Foot deck and traction pads remain attached to the foot bone.
    for i in range(4):
        x=mx+.13+i*.051
        rod("toe_traction_"+str(i),side,"foot","graphite",
            (x,yy-.07,.065),(x,yy+.07,.065),.013)
    for label,x in (("heel",mx+.08),("toe",mx+.32)):
        rod("foot_brace_"+label,side,"foot","plum",
            (x,yy-.072,.080),(x,yy+.072,.080),.024)
    # Hip and knee ladder bars for plausibly engineered actuator housing.
    for label,x,z,bone in (("hip",mx,1.00,"thigh"),("knee",mx+.035,.58,"thigh")):
        rod(label+"_brace",side,bone,"graphite",
            (x,yy-.08,z),(x,yy+.08,z),.015)
    # Foot-to-ankle cylinder mimics return springs and braces.
    rod("ankle_strut",side,"foot","titanium",
        (mx+.106,yy-.05,.18),(mx+.185,yy-.05,.095),.018)
payload={"schema":"FWAI_VQ04_GEOMETRY_PREVIEW_V1","asset_id":ASSET,
    "canonical_sha256":CANON_SHA,"units":"METERS","parts":parts,"review_only":True}
OUT.mkdir(parents=True,exist_ok=True)
dst=OUT/(ASSET+".json")
blob=(json.dumps(payload,indent=2)+"\n").encode("utf-8")
fd,temp=tempfile.mkstemp(prefix=".fwai-payload-",suffix=".json",dir=OUT)
with os.fdopen(fd,"wb") as f:
    f.write(blob);f.flush();os.fsync(f.fileno())
os.replace(temp,dst)
print(json.dumps({"asset":ASSET,"parts":len(parts),"bytes":len(blob),"sha256":hashlib.sha256(blob).hexdigest(),
    "path":str(dst),"safety":"data-only, unsaved preview, approved V2 canonical SHA pinned"},indent=2))
