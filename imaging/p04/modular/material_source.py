"""P04.06 FWAI-T001: deterministic mechanical 2.5D material source.

Approved geometry is immutable and SHA-pinned. Generates ONLY the isolated
technology under neutral virtual product-lighting, never an environment.
This is a material look-development source, not physically validated CAD.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import json,hashlib,math,random
R=Path.home()/"Documents"/"futureworks-p04-data"
SRC=R/"p04-06-modular-preview"/"FWAI-T001_geometry_spec.json"
MECH=R/"p04-06-modular-preview"/"FWAI-T001_mechanical_detail.json"
OUT=R/"p04-06-material-lookdev"
OUT.mkdir(exist_ok=True,parents=True)
APPROVED_G="7bc0379c02632018e78dfbea6eab467071ec0ffe9f97b3c9522c1634bf51b77e"
APPROVED_M="07dc8ea721e2d2d69d47585bc67268c31a2ceb9d96e0724a5ffc55fd17465c5f"
def sha(b):return hashlib.sha256(b).hexdigest()
assert sha(SRC.read_bytes())==APPROVED_G and sha(MECH.read_bytes())==APPROVED_M,"Owner-approved assets changed"
g=json.loads(SRC.read_text());m=json.loads(MECH.read_text())
assert g["environment"] is None and g["purpose"]=="civilian_orbital_construction"
assert len(g["fabrication_arms"])==len(m["arms"])==6
S=2;W,H=896,512
rng=random.Random(4614)
def P(pt):return (round((W/2+pt[0]*8)*S),round((H/2-pt[1]*8)*S))
def bbox(center,rad):
 x,y=P(center);q=round(rad*8*S);return [x-q,y-q,x+q,y+q]
def polyline(d,points,width,fill,joint="curve"):
 d.line([P(p) for p in points],fill=fill,width=round(width*S),joint=joint)
def disk(d,point,r,color):d.ellipse(bbox(point,r),fill=color)
def bolt(d,pt,r=.21,shade=(200,214,221)):
 disk(d,pt,r,shade); x,y=P(pt);w=r*8*S
 d.line((x-w*.45,y+w*.22,x+w*.45,y-w*.22),fill=(55,69,78),width=max(2,round(2*S)))
def structure(photo_tone):
 img=Image.new("RGB",(W*S,H*S),(22,27,34))
 d=ImageDraw.Draw(img)
 nodes=g["ring"]
 colors={"frame":(95,110,122),"edge":(205,216,216),"reflect":(164,180,185),"core":(83,103,113),
 "dark":(41,54,67),"panel":(125,142,149),"copper":(165,111,63),"seal":(23,36,43),"glow":(74,181,174)}
 if photo_tone=="ceramic_titanium":
  colors.update(frame=(114,123,126),edge=(230,229,215),reflect=(187,196,192),core=(98,107,110),panel=(168,176,170))
 # Truss shadows with light from upper left, no external scene.
 def offset(pt):return (pt[0]+.37,pt[1]-.37)
 for i in range(6):
  a=nodes[i]; b=nodes[(i+1)%6]
  polyline(d,[offset(a),offset(b)],38,(5,10,16))
  polyline(d,[a,b],34,colors["dark"])
  polyline(d,[a,b],25,colors["frame"])
  polyline(d,[a,b],15,colors["reflect"])
  polyline(d,[a,b],4,colors["edge"])
  # four precisely spaced nested fastener tabs and truss panel seams
  for j in range(1,5):
   t=j/5
   center=(a[0]*(1-t)+b[0]*t,a[1]*(1-t)+b[1]*t)
   v=(b[0]-a[0],b[1]-a[1]);L=math.hypot(*v);n=(-v[1]/L,v[0]/L)
   c1=(center[0]+n[0]*.7,center[1]+n[1]*.7)
   c2=(center[0]-n[0]*.7,center[1]-n[1]*.7)
   polyline(d,[c1,c2],2,colors["seal"]);bolt(d,c1,.13);bolt(d,c2,.13)
 for node in nodes:
  polyline(d,[(0,0),node],20,colors["dark"])
  polyline(d,[(0,0),node],13,colors["panel"])
  polyline(d,[(0,0),node],4,colors["edge"])
 # radiator array: short planar heat-exchanger fins rooted at six anchor locations
 for i,node in enumerate(nodes):
  ux=node[0]/20;uy=node[1]/20
  perpendicular=(-uy,ux)
  root=(node[0]*.87,node[1]*.87)
  for k in range(-3,4):
   c=(root[0]+perpendicular[0]*k*.55,root[1]+perpendicular[1]*k*.55)
   q=(c[0]-ux*2.3,c[1]-uy*2.3)
   polyline(d,[c,q],3,colors["edge"] if k%2 else colors["copper"])
 # Machinery arms
 for i,arm in enumerate(g["fabrication_arms"]):
  a,b,c=arm["joints"]
  polyline(d,[offset(a),offset(b),offset(c)],25,(5,9,12))
  polyline(d,[a,b,c],22,colors["dark"])
  polyline(d,[a,b,c],17,colors["frame"])
  polyline(d,[a,b,c],12,colors["reflect"])
  polyline(d,[a,b,c],5,colors["edge"])
  # sealed shoulder, replaceable elbow bearing, industrial tool head
  for pt,r in ((a,1.2),(b,1.0),(c,.68)):
   disk(d,pt,r,colors["dark"])
   disk(d,pt,r*.78,colors["edge"])
   disk(d,pt,r*.47,colors["copper"])
   disk(d,pt,r*.21,colors["seal"])
   for ang in (0,math.pi/2,math.pi,3*math.pi/2):
    bolt(d,(pt[0]+r*.58*math.cos(ang),pt[1]+r*.58*math.sin(ang)),.12)
  # cable conduit follows link but remains visibly separate
  dx=b[0]-a[0];dy=b[1]-a[1];L=math.hypot(dx,dy);norm=(-dy/L,dx/L)
  path=[(pt[0]+norm[0]*.46,pt[1]+norm[1]*.46) for pt in (a,b)]
  polyline(d,path,4,colors["seal"])
  polyline(d,path,1,colors["glow"])
  # fabrication end effector twin collimators
  dx=c[0]-b[0];dy=c[1]-b[1];L=math.hypot(dx,dy)
  if L>0:
   u=(dx/L,dy/L);v=(-u[1],u[0])
   for side in (-1,1):
    start=(c[0]+side*v[0]*.28,c[1]+side*v[1]*.28)
    end=(start[0]+u[0]*.7,start[1]+u[1]*.7)
    polyline(d,[start,end],5,colors["edge"])
 # central hub and airlock projection with scale-appropriate 2m hatch
 disk(d,(0,0),4.1,colors["seal"])
 disk(d,(0,0),3.75,colors["frame"])
 disk(d,(0,0),3.25,colors["panel"])
 disk(d,(0,0),2.8,colors["dark"])
 disk(d,(0,0),2.0,colors["reflect"])
 disk(d,(0,0),1.0,colors["seal"])
 disk(d,(0,0),.8,colors["copper"])
 for ang in [k*math.pi/6 for k in range(12)]:
  bolt(d,(3.4*math.cos(ang),3.4*math.sin(ang)),.17)
 # seam line between pressure module and metallic truss; separate central access hatch
 polyline(d,[(-1,-1.2),(1,-1.2)],3,colors["seal"])
 polyline(d,[(-1,-1.2),(-1,1.2)],3,colors["edge"])
 polyline(d,[(1,-1.2),(1,1.2)],3,colors["edge"])
 # matte metal grain / subtle microtexture restricted to foreground machinery.
 # Source remains an isolated studio cutout, no planet/stars/architecture.
 import numpy as np
 pix=np.asarray(img).astype("int16")
 noise=np.asarray([rng.randrange(-4,5) for _ in range(W*S*H*S)],dtype="int16").reshape(H*S,W*S,1)
 pix=np.clip(pix+noise,0,255).astype("uint8")
 img=Image.fromarray(pix).resize((W,H),Image.Resampling.LANCZOS)
 return img
entries=[]
for name in ("graphite_alloy","ceramic_titanium"):
 image=structure(name)
 path=OUT/f"FWAI-T001_MATERIAL_SOURCE_{name}_896x512.png"
 image.save(path,optimize=True)
 entries.append({"type":name,"file":path.name,"sha256":sha(path.read_bytes()),"resolution":[896,512]})
report={"schema":"FWAI_P04_06_MATERIAL_SOURCE_1","design_id":"FWAI-T001","approved_geometry_sha256":APPROVED_G,
 "approved_mechanical_sha256":APPROVED_M,"source_assets":entries,
 "style_target":"physically tangible industrial machinery, not painted concept art",
 "stage":"local_material_source_only","environment":None,"external_upload_authorized":False,
 "publication_authorized":False,"paid_calls":0,"human_visual_approval":False}
(OUT/"MATERIAL_SOURCE_RECEIPT.json").write_text(json.dumps(report,indent=2))
print("TWO_APPROVED_GEOMETRY_BOUND_MATERIAL_SOURCES_READY")
