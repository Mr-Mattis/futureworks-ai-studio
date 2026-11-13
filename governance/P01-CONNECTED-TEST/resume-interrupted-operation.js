const existing = $input.first()?.json;
const expected = $('P01.07 Prepare interrupted operation').first().json;
if (!existing || existing.record_id !== expected.record_id) throw new Error('P01.07 existing operation missing');
for (const key of Object.keys(expected)) if (existing[key] !== expected[key]) throw new Error('P01.07 interrupted operation conflict: ' + key);
const recovery = JSON.parse(existing.response_json).recovery;
if (recovery.status !== 'dispatching' || recovery.synthetic_only !== true || recovery.provider_calls !== 0 || recovery.amount_microusd !== 0) throw new Error('P01.07 recovery record unsafe');
return [{json:{checkpoint:'P01.07',status:'recovered_existing_operation',record_id:existing.record_id,job_id:existing.job_id,manifest_revision:existing.manifest_revision,manifest_sha256:existing.manifest_sha256,provider_rows_created_this_run:0,provider_calls:0,amount_microusd:0,synthetic_only:true}}];
