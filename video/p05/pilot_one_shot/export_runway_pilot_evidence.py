"""Produce public-safe P04/P05 real-pilot evidence, never publish media or secrets."""
import hashlib,json,pathlib,sys
import runway_three_clip_pilot as pilot
import correct_approved_manifest as approval
def build():
    approval.verify()
    journal=pilot.begin()
    if journal.get("paid_submission_count")!=3:raise RuntimeError("Exactly three submissions required")
    starting=journal.get("starting_credit_balance")
    ending=pilot.balance()
    if starting is None:raise RuntimeError("Starting credits missing")
    billed=starting-ending
    if billed<0 or billed>pilot.MAX_TOTAL_CREDITS:raise RuntimeError("Budget cap violated or balance unverified")
    results=[]
    for scene in pilot.PINNED:
        row=journal["scenes"][scene]
        if row["state"]!="archived":raise RuntimeError("Missing complete clip "+scene)
        file=pathlib.Path(row["clip_file"])
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest()!=row["clip_sha256"]:
            raise RuntimeError("Clip archive hash mismatch "+scene)
        data=row["media"]
        if not 4.0<=float(data["duration_seconds"])<=6.5 or data["width"]!=1280 or data["height"]!=720:
            raise RuntimeError("Unexpected video duration/resolution "+scene)
        results.append({"scene_id":scene,"source_asset_id":pilot.PINNED[scene][0],
                        "source_sha256":pilot.PINNED[scene][1],
                        "runway_task_id":row["task_id"],
                        "clip_sha256":row["clip_sha256"],
                        "size_bytes":row["bytes"],
                        "media":data,"verified_real_generation":True,
                        "human_continuity_review":"PENDING"})
    assert len(set(x["runway_task_id"] for x in results))==3
    report={
      "phase":"P05","pilot":"RUNWAY_GEN45_3X5_REAL_20261116","scope":"owner authorized three selected original P04 images, max $5, no publishing",
      "source_manifest_sha256":hashlib.sha256(pilot.MANIFEST.read_bytes()).hexdigest(),
      "approved_manifest_v2_sha256":hashlib.sha256(approval.V2.read_bytes()).hexdigest(),
      "scope_record_sha256":hashlib.sha256(approval.RECORD.read_bytes()).hexdigest(),
      "provider":"Runway Developer API","model":"gen4.5",
      "version":"2024-11-06",
      "clips":results,
      "starting_credit_balance":starting,"ending_credit_balance":ending,
      "measured_spend_credits":billed,"measured_spend_usd":billed/100,
      "maximum_authorized_credits":pilot.MAX_TOTAL_CREDITS,"maximum_authorized_usd":5,
      "runway_http_submissions":journal["paid_submission_count"],
      "all_media_locally_archived":True,
      "human_continuity_approval":False,"production_approved":False,
      "publication_approved":False,
      "p04_authenticated_n8n_handoff":"NOT_YET_TESTED",
      "phase_closed":False}
    path=pilot.OUT/"P04_P05_REAL_PILOT_REDACTED_EVIDENCE.json"
    path.write_text(json.dumps(report,indent=2))
    print("3_REAL_RUNWAY_CLIPS_ARCHIVED_PASSED","spent",billed,"credits ($"+str(billed/100)+")","balance",ending)
    print(path)
if __name__=="__main__":build()
