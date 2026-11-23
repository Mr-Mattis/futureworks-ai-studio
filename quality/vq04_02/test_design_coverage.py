"""Source-grounded design-coverage assertions against the locked FWAI-M001 V2 master.

Coverage checks presence of relevant *study geometry*, not visual identity
accuracy, physical mechanism correctness, or owner creative approval.
"""
from pathlib import Path
import json,hashlib
base=Path.home()/"Documents"
canon=base/"futureworks-p04-data"/"character-library"/"FWAI-M001"/"v2.0"
master=canon/"FWAI-M001_APPROVED_FINAL_MASTER_V2.0.png"
lock=json.loads((canon/"FWAI-M001_FINAL_VISUAL_DESIGN_LOCK_v2.json").read_text())
identity=json.loads((base/"futureworks-vq04-02"/"staging"/"FWAI_M001_V2_IDENTITY_DETAIL_01.json").read_text())
parts=identity["parts"]
name={p["name"] for p in parts}
tests={}
def ck(label,truth):
  tests[label]=bool(truth)
  if not truth:raise AssertionError(label)
ck("canonical_approved_v2",lock["status"]=="OWNER_APPROVED_FINAL_VISUAL_DESIGN" and lock["design_version"]=="2.0")
ck("pixel_immutable_hash_matches",hashlib.sha256(master.read_bytes()).hexdigest()==lock["approved_sha256"])
ck("identity_payload_pinned_to_same_master",identity["reference_sha256"]==lock["approved_sha256"])
ck("no_autopromotion_to_canon",identity["approved"] is False)
ck("swept_fin_helmet",{"helmet_crown_plum","helmet_swept_crest_fin","helmet_titanium_fin"}.issubset(name))
ck("cyan_angular_visor",{"visor_plasma_chevron","helmet_upper_visor_brow"}.issubset(name))
ck("circular_side_sensor",{"helmet_left_sensor","helmet_right_sensor"}.issubset(name))
ck("shoulder_spinal_coolant_tubes",len([n for n in name if "coolant_upper_spine" in n])==6)
ck("vent_slit_geometry_present",len([n for n in name if n.startswith("spine_vent_slit_")])==4)
ck("sealed_forearm_housing_both_sides",all(k in name for k in ("L_flush_tool_door","R_flush_tool_door","L_forearm_tool_shell","R_forearm_tool_shell")))
ck("actuator_servo_rings",all(k in name for k in ("L_shoulder_servo","R_shoulder_servo","L_elbow_servo","R_elbow_servo")))
ck("canonical_palette_in_source",all(k in lock["immutable_visual_design"]["color_material"] for k in ("obsidian-plum","cyan","titanium-gray","graphite")))
ck("no_unapproved_external_release",lock["privacy_and_release"]["paid_services_authorized"] is False and lock["privacy_and_release"]["external_upload_authorized"] is False)
report={"schema":"FWAI_VQ04_02_DESIGN_COVERAGE_AUDIT_V1","tests":tests,"passed":sum(tests.values()),"total":len(tests),
"locked_visual_master_sha256":lock["approved_sha256"],
"limitations":["Only feature presence is checked, not visual matching accuracy",
 "Cooling vents currently represent closed-state geometry; three-state detent animation not implemented",
 "Forearm tools are flush housing proxies, not deployable validated manufacturing tools",
 "Routed coolant is static geometry, not animated physical flow",
 "Nissan vehicle and film interaction still proxies"],
"artistic_identity_approved":False}
out=base/"futureworks-vq04-02"/"evidence";out.mkdir(exist_ok=True)
(out/"VQ04_02_DESIGN_COVERAGE.json").write_text(json.dumps(report,indent=2))
print("FWAI_VQ04_02_DESIGN_COVERAGE",report["passed"],"/",report["total"],"PASS")
