// P01.07 read-only connected data gate for the existing inactive Production Adapter.
// This branch performs no provider request, approval update, or production write.
const job = $('P01.07 Load test job').first().json;
const hashed = $('P01.07 Hash manifest text').first().json;
const provider = $('P01.07 Load test provider').first().json;
const asset = $('P01.07 Load test asset').first().json;
const cost = $('P01.07 Load test cost').first().json;
const approval = $('P01.07 Load test approval').first().json;
const error = $('P01.07 Load test error').first().json;
function check(ok, message) { if (!ok) throw new Error('P01.07 gate: ' + message); }
function object(value) { return value !== null && typeof value === 'object' && !Array.isArray(value); }
const manifest = JSON.parse(job.manifest_json);
const snapshot = JSON.parse(job.snapshot_json);
const ref = snapshot.manifest_ref;
const records = [job, provider, asset, cost, approval, error];
check(records.every(r => r && r.is_test === true && r.test_run_id === job.test_run_id), 'test isolation');
check(job.project_id === 'FWAI-P0105-LIVE-TEST' && job.job_id === 'P0105-LIVE-TEST-R1', 'selected dummy job');
check(job.state === 'draft' && job.state_version === 0 && snapshot.state === 'draft' && snapshot.state_version === 0 && Array.isArray(snapshot.history) && snapshot.history.length === 0, 'draft snapshot');
check(manifest.schema_version === '1.0.0' && manifest.project_id === job.project_id && manifest.revision === job.manifest_revision, 'manifest identity');
check(manifest.approval_state?.status === 'pending_review' && manifest.approval_state.approved_revision === null, 'manifest approval still pending');
check(manifest.content_type === 'AI_CONCEPT' && typeof manifest.disclosure === 'string' && manifest.disclosure.trim().length > 0, 'fiction disclosure');
check(manifest.target_duration_seconds === 360 && Array.isArray(manifest.scenes) && manifest.scenes.length === 5, 'scene count and target duration');
check(manifest.scenes.reduce((sum, scene) => sum + scene.duration_seconds, 0) === 360, 'scene duration sum');
check(manifest.scenes.every((scene, i) => scene.scene_id === 'S0' + (i + 1) && scene.order === i + 1 && typeof scene.narration === 'string' && scene.narration.trim() && typeof scene.visual_prompt === 'string' && scene.visual_prompt.trim()), 'ordered scene fields');
check(object(manifest.generation_plan) && manifest.scenes.every(scene => Object.entries(scene.media_requirements).every(([kind, needed]) => !needed || manifest.generation_plan[kind]?.enabled === true)), 'media requirements and plan');
check(hashed.manifest_sha256_calculated === job.manifest_sha256, 'exact manifest text SHA-256');
check(ref.schema_version === '1.0.0' && ref.project_id === job.project_id && ref.revision === job.manifest_revision && ref.sha256 === job.manifest_sha256, 'snapshot reference');
check(job.record_id === `${job.project_id}:r${job.manifest_revision}:${job.manifest_sha256}`, 'immutable revision record ID');
for (const row of records.slice(1)) {
  for (const key of ['project_id', 'job_id', 'manifest_revision', 'manifest_sha256', 'test_run_id']) check(row[key] === job[key], `${key} cross-table identity`);
}
check(provider.record_id === 'P0107-TEST-provider_jobs' && provider.provider_job_id === null && provider.status === 'not_submitted', 'provider not submitted');
check(asset.provider_job_record_id === provider.record_id && asset.scene_id === 'S01' && asset.status === 'planned', 'asset reference');
const assetValue = JSON.parse(asset.asset_json);
check(assetValue.asset_id === asset.asset_id && assetValue.scene_id === asset.scene_id && assetValue.status === asset.status, 'asset JSON/index agreement');
check(cost.provider_job_record_id === provider.record_id && cost.currency === 'USD' && cost.cost_type === 'estimate' && cost.amount_microusd === 0, 'zero estimate and provider link');
const receipt = JSON.parse(approval.receipt_json);
check(approval.decision === 'pending' && receipt.decision === 'pending' && receipt.receipt_id === approval.record_id && receipt.job_id === job.job_id && receipt.manifest_ref.sha256 === ref.sha256, 'no passed live approval');
check(error.status === 'test_only' && error.provider_job_record_id === provider.record_id, 'test-only error record');
return [{json:{checkpoint:'P01.07',status:'connected_data_gates_passed',workflow_id:'yjuRNIatvdTMKuqj',project_id:job.project_id,job_id:job.job_id,manifest_revision:job.manifest_revision,manifest_sha256:job.manifest_sha256,records_checked:records.length,live_state:job.state,live_approval:approval.decision,provider_status:provider.status,paid_calls:0,publication_actions:0,synthetic_only:true}}];
