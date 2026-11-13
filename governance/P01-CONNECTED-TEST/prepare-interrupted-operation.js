const gate = $input.first()?.json;
if (!gate || gate.status !== 'connected_data_gates_passed' || gate.synthetic_only !== true || gate.live_state !== 'draft' || gate.live_approval !== 'pending' || gate.provider_status !== 'not_submitted') throw new Error('P01.07 validated dummy gate required');
const record = {
  record_id:'P0107-INTERRUPT-OP-001',
  schema_version:'1.0.0',
  project_id:gate.project_id,
  job_id:gate.job_id,
  manifest_revision:gate.manifest_revision,
  manifest_sha256:gate.manifest_sha256,
  is_test:true,
  test_run_id:'P0105-v1-revision-test-001',
  provider:'synthetic_no_provider',
  operation:'interruption_storage_test',
  provider_job_id:null,
  status:'not_submitted',
  request_reference:'fixture:P0107-INTERRUPT-OP-001:no-network',
  response_json:JSON.stringify({recovery:{schema_version:'1.0.0',status:'dispatching',synthetic_only:true,attempts:1,provider_calls:0,amount_microusd:0}})
};
return [{json:record}];
