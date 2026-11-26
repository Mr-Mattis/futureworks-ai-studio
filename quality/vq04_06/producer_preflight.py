"""Future Works AI Studio — EP001 autonomous-production safety/control plane.

Reads exact existing EP001 production manifest, immutable latest owner mech master,
canonical Nissan source references, local shot receipts and VQ04.06 all-frame proof.
Outputs a machine-readable shot slate without falsely approving footage or
spending Runway credits. Local automation may continue only with allowed operations.
"""
import json,hashlib,datetime
from pathlib import Path
home=Path.home()
root=home/"Documents"/"futureworks-vq04-06"
out=root/"evidence";out.mkdir(parents=True,exist_ok=True)
pre=home/"Documents"/"futureworks-p04-data"/"FWAI-M001_EP001_PREPRODUCTION"
manifest_path=pre/"03_RUNWAY_PROMPTS"/"PRODUCTION_MANIFEST.json"
prod=json.loads(manifest_path.read_text(encoding="utf-8"))
assert prod["project"]=="Future Works AI Studio"
assert prod["episode_id"]=="FWAI-M001-EP001"
assert len(prod["shots"])==6 and all(prod["shots"][i]["start_s"]==5*i and prod["shots"][i]["end_s"]==5*(i+1) for i in range(6))
latest=Path(prod["owner_master_visual_asset_on_El_Corredor"])
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert latest.is_file() and sha(latest)==prod["owner_latest_mech_master_sha256"],"Owner master changed"
car=pre/prod["car_primary_reference"]
assert car.is_file()
assert prod["authorization"]=={
 "local_keyframe_creation":True,
 "paid_runway_api":False,
 "external_runway_upload":False,
 "publish":False,
 "production_workflow_activation":False}
s01qa_path=pre/"05_LOCAL_KEYFRAMES"/"S01"/"FWAI_EP001_S01_D4_E_F_QA_REPORT.json"
qa=json.loads(s01qa_path.read_text(encoding="utf-8"))
assert qa["visual_master_sha256"]==sha(latest)
assert qa["status"]=="HOLD_OWNER_REVIEW"
coupled=json.loads((out/"VQ04_06_COUPLING_DIAGNOSTICS.json").read_text())
acceptance=json.loads((out/"VQ04_06_ACCEPTANCE.json").read_text())
assert acceptance["all_pass"] and coupled["max_door_surface_intrusions"]==0
local_proof=out/"VQ04_06_MECH_COUPLED_CLOTH_3SEC.mp4"
assert local_proof.is_file()
# No fraudulent per-shot approvals: S01 is explicitly HOLD, all others have
# no required per-shot accepted image/video in this preproduction pack.
shots=[]
for x in prod["shots"]:
 sid=x["shot_id"]
 sh={"shot_id":sid,"start_s":x["start_s"],"end_s":x["end_s"],
    "name":x["name"],"shot_minutes_authorized_for_runway":0,
    "approved_keyframe":False,"completed_i2v":False,
    "scene_consistency_verified":False,"owner_creative_approval":False,
    "local_draft_work_permitted":True,
    "status":"BLOCKED_FOR_FINAL_VIDEO",
    "next_local_task":"Build reference-locked 16:9 keyframe and deterministic local camera/physics preview"}
 if sid=="S01":
    sh["existing_best_local_candidate"]="candidate F"
    sh["existing_QA_status"]=qa["status"]
    sh["blocking_issues"]=qa["warnings"]
    sh["next_local_task"]="Repair second hand/film grip and 5-8% full-car safe margin against unchanged workshop plate"
 elif sid in ("S02","S03"):
    sh["supporting_physics_proof"]="VQ04.06 mechanical hand-driven thin-film 3-second clip"
    sh["next_local_task"]="Align shot camera to approved S01 workshop/car/mech; physically consistent film tool contact and shot framing"
 elif sid=="S04":
    sh["next_local_task"]="Build flush heat-tool deploy with no flame; maintain vehicle door and cyan coolant identity"
 elif sid=="S05":
    sh["next_local_task"]="Build guarded trim and continuous offcut geometry; never cut Nissan paint"
 elif sid=="S06":
    sh["next_local_task"]="Build completed charcoal wrap door with unchanged pearl-white rest of NISMO; whole car/mech visible"
 shots.append(sh)
data={
 "schema":"FWAI_EP001_AUTONOMOUS_PRODUCTION_GATES_V1",
 "episode":prod["episode_id"],"project":"Future Works AI Studio",
 "runtime_policy":{
  "local_development_tests_legal_to_run_without_further_permission":True,
  "authorized_to_call_paid_runway":False,
  "authorized_to_upload_keyframes_to_runway":False,
  "authorized_to_publish":False,
  "authorized_to_edit_n8n_production":False,
  "authorized_to_delete_user_assets":False,
  "require_authorized_credit_cap_before_cloud_run":True,
  "require_owner_visual_acceptance_before_publication":True
 },
 "target":{"seconds":30,"fps":24,"frame_count":720,"aspect":"16:9","shots":6,"shot_seconds":5},
 "identity":{"latest_owner_master_sha256":sha(latest),"primary_car_reference_sha256":sha(car),
   "latest_mech_visual_takes_priority_over_old_board":True},
 "current_local_proof":{
   "video":str(local_proof),"sha256":sha(local_proof),
   "seconds":3,"frame_count":72,
   "real_cloth_baked":True,
   "rig_tip_driven":True,
   "clearance_stable_72_frames":coupled["max_door_surface_intrusions"]==0,
   "force_or_adhesion_certified":False,
   "visual_fidelity_approved":False,
   "engineering_acceptance":acceptance
 },
 "shots":shots,
 "released_final_30s_video_exists":False,
 "all_six_keyframes_owner_approved":False,
 "paid_service_actions_performed":0,
 "publish_actions_performed":0,
 "global_status":"LOCAL_DEVELOPMENT_AUTONOMOUS; PAID_RENDER_AND_CREATIVE_RELEASE_GATED"
}
(out/"FWAI_EP001_AUTONOMOUS_PRODUCTION_GATES.json").write_text(json.dumps(data,indent=2))
print("FWAI_EP001_PRODUCTION_PREFLIGHT",len(shots),"shots","local_proof_ready",True,"final_output",False)
