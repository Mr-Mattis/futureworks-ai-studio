"""Deterministic 3D silhouette/parts study from immutable FWAI-M001 V2 design lock.

This is a bounded, source-referenced interpretive derivative for Blender inspection;
the 2D master is unchanged and artistic acceptance remains explicitly withheld.
"""
from pathlib import Path
import hashlib,json,os,tempfile,math
ROOT=Path.home()/"Documents"/"futureworks-vq04-02"/"staging"
MASTER=Path.home()/"Documents"/"futureworks-p04-data"/"character-library"/"FWAI-M001"/"v2.0"/"FWAI-M001_APPROVED_FINAL_MASTER_V2.0.png"
SHA="480263bdd7637bfb2d90cc2deecdeb616eef03492a35216dbebfd3b1f44c555c"
ASSET="FWAI_M001_V2_IDENTITY_DETAIL_01"
assert MASTER.is_file() and hashlib.sha256(MASTER.read_bytes()).hexdigest()==SHA
parts=[]
def p(name,bone,material,vertices,thickness=.016):
    parts.append({"name":name,"shape":"plate","bone":bone,"material":material,
                  "points":[[round(float(v),5) for v in vert] for vert in vertices],"thickness":thickness})
def c(name,bone,material,coords,r=.014):
    parts.append({"name":name,"shape":"tube","bone":bone,"material":material,
                  "points":[[round(float(v),5) for v in vert] for vert in coords],"thickness":r})
def ring(name,bone,material,x,y,z,r,radius=.009):
    parts.append({"name":name,"shape":"ring","bone":bone,"material":material,
      "points":[[x,y,z],[round(x+r,5),y,z],[x,round(y-.14,5),z]],"thickness":radius})
def face(coords,y):
    return [[x,y,z] for x,z in coords]
# Slim angular architecture. All spatial coordinates in meters in original rig space.
p("chest_pectoral_main","spine","plum",
  face([(-2.094,1.557),(-1.935,1.595),(-1.775,1.497),(-1.803,1.337),(-1.957,1.281),(-2.095,1.352)],-1.075),.032)
p("chest_inset_titanium","spine","titanium",
  face([(-2.043,1.521),(-1.929,1.541),(-1.812,1.466),(-1.851,1.43),(-2.029,1.476)],-1.095),.009)
p("chest_plasma_edge","spine","cyan",
  face([(-2.015,1.461),(-1.886,1.423),(-1.856,1.391),(-1.936,1.419)],-1.11),.007)
# Neck/spinal mechanical carrier makes the helmet physically connected to the chest,
# while upper-back coolant lines terminate into the shoulder hardware.
p("neck_reinforced_carrier","neck","graphite",
  face([(-2.055,1.771),(-1.972,1.796),(-1.932,1.671),(-1.951,1.581),(-2.047,1.604)],-1.065),.027)
p("neck_titanium_rail","neck","titanium",
  face([(-2.046,1.740),(-2.016,1.758),(-1.976,1.631),(-2.001,1.623)],-1.09),.012)
p("neck_cyan_umbilical","neck","cyan",
  face([(-2.025,1.740),(-2.012,1.740),(-1.966,1.628),(-1.977,1.634)],-1.111),.006)
p("upper_spine_yoke","spine","plum",
  face([(-2.235,1.632),(-2.139,1.701),(-2.032,1.628),(-2.061,1.560),(-2.157,1.576)],-1.004),.022)
c("left_coolant_body_return","spine","graphite",
  [(-2.275,-1.10,1.411),(-2.186,-1.10,1.433),(-2.103,-1.10,1.468)],.018)
c("right_coolant_body_return","spine","graphite",
  [(-2.275,-.76,1.411),(-2.186,-.76,1.433),(-2.103,-.76,1.468)],.018)
p("waist_narrow_core","spine","graphite",
  face([(-2.013,1.309),(-1.884,1.299),(-1.858,1.148),(-1.968,1.135)],-1.044),.025)
p("pelvis_carapace","pelvis","plum",
  face([(-2.072,1.109),(-1.936,1.159),(-1.796,1.085),(-1.846,.951),(-2.007,.978)],-1.089),.026)
p("pelvis_vent_trim","pelvis","titanium",
  face([(-2.041,1.070),(-1.942,1.105),(-1.833,1.064),(-1.866,1.047),(-1.959,1.078)],-1.117),.008)
# Shoulder open-wedge cap and backing, plus precision multi-axis servo.
for side,y in (("L",-1.14),("R",-.76)):
    p(side+"_shoulder_backing","spine","graphite",
      face([(-2.003,1.587),(-1.857,1.623),(-1.740,1.514),(-1.79,1.422),(-1.972,1.465)],y+.035),.024)
    p(side+"_shoulder_wing","spine","plum_light",
      face([(-2.035,1.591),(-1.886,1.629),(-1.721,1.529),(-1.762,1.495),(-1.929,1.538)],y),.018)
    p(side+"_shoulder_stripe","spine","cyan",
      face([(-2.005,1.575),(-1.884,1.600),(-1.775,1.532),(-1.892,1.574)],y-.025),.006)
    ring(side+"_shoulder_servo","spine","cyan",-1.825,round(y-.035,5),1.47,.063)
# Hybrid helmet geometry: swept-back tiered segmented fins, jaw, cyan angular visor, side sensors.
p("helmet_jaw","helmet","titanium",
  face([(-2.059,1.837),(-1.914,1.885),(-1.822,1.821),(-1.861,1.752),(-2.011,1.766)],-1.059),.024)
p("helmet_faceplate","helmet","graphite",
  face([(-2.071,1.874),(-1.935,1.902),(-1.800,1.859),(-1.786,1.816),(-1.965,1.801)],-1.077),.019)
p("helmet_crown_plum","helmet","plum",
  face([(-2.241,1.939),(-2.079,1.926),(-1.940,1.945),(-1.819,1.887),(-2.018,1.867)],-1.060),.016)
p("helmet_swept_crest_fin","helmet","plum_light",
  face([(-2.287,1.947),(-2.161,1.942),(-2.058,1.909),(-2.127,1.900)],-1.090),.009)
p("helmet_titanium_fin","helmet","titanium",
  face([(-2.184,1.938),(-2.090,1.938),(-1.989,1.889),(-2.076,1.893)],-1.112),.009)
p("helmet_upper_visor_brow","helmet","plum",
  face([(-1.985,1.884),(-1.843,1.867),(-1.787,1.843),(-1.843,1.849)],-1.122),.010)
p("visor_plasma_chevron","helmet","cyan",
  face([(-1.976,1.858),(-1.878,1.844),(-1.817,1.822),(-1.856,1.803),(-1.924,1.826)],-1.133),.008)
p("helmet_angled_lower_bezel","helmet","titanium",
  face([(-1.932,1.813),(-1.854,1.789),(-1.883,1.769),(-1.965,1.785)],-1.116),.009)
ring("helmet_left_sensor","helmet","cyan",-2.009,-1.13,1.813,.046,.009)
ring("helmet_right_sensor","helmet","graphite",-2.025,-.72,1.813,.050,.012)
# Upper-back coolant conduits curve across shoulders/neck, avoid inventing unapproved routes.
for side,y in (("L",-1.10),("R",-.76)):
    for i,dx in enumerate((0,.042,.084)):
        c(side+"_coolant_upper_spine_"+str(i),"spine","cyan",[
          (-2.27-dx,y,1.41),(-2.27-dx,y,1.49),(-2.245-dx,y,1.58),
          (-2.21-dx,y,1.67),(-2.14-dx,y,1.729),(-2.065-dx,y,1.74)],.010)
        # Tube retaining clamps and dark intake sleeves at a stable spine bone location.
        ring(side+"_tube_intake_"+str(i),"spine","graphite",-2.27-dx,round(y-.02,5),1.42,.029,.008)
# Closing vents as baseline; detent movement is separately engineered later.
for i in range(4):
    z=1.395+i*.047
    p("spine_vent_slit_"+str(i),"spine","vent",
      face([(-2.143,z+.029),(-2.081,z+.027),(-2.064,z+.011),(-2.139,z+.014)],-1.119),.008)
    p("spine_vent_edge_"+str(i),"spine","titanium",
      face([(-2.15,z+.031),(-2.084,z+.030),(-2.073,z+.027),(-2.145,z+.027)],-1.132),.005)
# Two slim articulated arms, sealed tool interface rather than loose floating tooling.
for side,y in (("L",-1.135),("R",-.745)):
    p(side+"_bicep_shell",""+side+"_upperarm","plum",
      face([(-1.954,1.566),(-1.839,1.538),(-1.564,1.413),(-1.612,1.369),(-1.892,1.475)],y),.021)
    p(side+"_bicep_titanium_ridge",side+"_upperarm","titanium",
      face([(-1.906,1.520),(-1.828,1.510),(-1.633,1.428),(-1.701,1.437)],y-.025),.009)
    ring(side+"_elbow_servo",side+"_upperarm","cyan",-1.582,round(y-.028,5),1.391,.045,.008)
    p(side+"_forearm_tool_shell",side+"_forearm","plum_light",
      face([(-1.633,1.447),(-1.518,1.400),(-1.265,1.211),(-1.286,1.174),(-1.578,1.357)],y),.027)
    p(side+"_flush_tool_door",side+"_forearm","graphite",
      face([(-1.438,1.327),(-1.340,1.258),(-1.295,1.202),(-1.392,1.273)],y-.033),.009)
    p(side+"_tool_release_led",side+"_forearm","cyan",
      face([(-1.380,1.288),(-1.305,1.230),(-1.323,1.226),(-1.388,1.277)],y-.043),.005)
    # Tool housing physically integrated in forearm; no external dangling tray.
    c(side+"_linear_tool_rail",side+"_forearm","titanium",
      [(-1.567,y-.012,1.373),(-1.47,y-.012,1.314),(-1.370,y-.012,1.253)],.009)
# Distinctive streamlined side armor fins and light strip around hip, not redesign of master.
for side,y in (("L",-1.13),("R",-.73)):
    p(side+"_hip_cowl","pelvis","plum_light",
      face([(-2.096,1.112),(-1.999,1.130),(-1.874,1.058),(-1.937,.984),(-2.087,1.021)],y),.020)
    p(side+"_hip_joint_light","pelvis","cyan",
      face([(-2.061,1.056),(-1.982,1.077),(-1.951,1.055),(-2.022,1.042)],y-.024),.006)
    ring(side+"_hip_servo","pelvis","titanium",-1.940,round(y-.010,5),1.034,.054,.009)

data={"schema":"FWAI_VQ04_IDENTITY_PREVIEW_V1","asset_id":ASSET,"reference_sha256":SHA,
      "units":"METERS","parts":parts,"approved":False}
ROOT.mkdir(exist_ok=True,parents=True)
serialized=(json.dumps(data,indent=2)+"\n").encode("utf-8")
temp=ROOT/("."+ASSET+".tmp")
temp.write_bytes(serialized)
os.replace(temp,ROOT/(ASSET+".json"))
print(json.dumps({"asset_id":ASSET,"parts":len(parts),"bytes":len(serialized),
                  "sha256":hashlib.sha256(serialized).hexdigest(),"visual_approval":False},indent=2))
