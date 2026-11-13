const result = $('P01.07 Call canonical guards').first().json;
const row = $('P01.07 Read persisted research state').first().json;
function check(ok, message) { if (!ok) throw new Error('P01.07 guarded transition: ' + message); }
const snapshot = JSON.parse(row.snapshot_json);
check(result.status === 'canonical_gates_passed' && result.invalid_manifest_rejected === true && result.invalid_row_rejected === true, 'canonical positive and negative gates');
check(row.is_test === true && row.job_id === 'P0105-LIVE-TEST-R2' && row.state === 'research' && row.state_version === 1, 'persisted synthetic research state');
check(snapshot.state === row.state && snapshot.state_version === row.state_version && snapshot.history.length === 1, 'snapshot matches index');
check(snapshot.history[0].from === 'draft' && snapshot.history[0].to === 'research' && snapshot.history[0].evidence.brief_validated === 'P0107-TEST-R2-brief-validated', 'guarded transition receipt');
check(snapshot.manifest_ref.sha256 === row.manifest_sha256 && row.manifest_sha256 === result.manifest_sha256, 'immutable revision hash');
check(result.synthetic_only === true && result.provider_calls === 0 && result.amount_microusd === 0, 'no provider use or expense');
return [{json:{checkpoint:'P01.07',status:'guarded_transition_persisted',job_id:row.job_id,state:row.state,state_version:row.state_version,manifest_sha256:row.manifest_sha256,invalid_manifest_rejected:true,invalid_row_rejected:true,provider_calls:0,amount_microusd:0,synthetic_only:true}}];
