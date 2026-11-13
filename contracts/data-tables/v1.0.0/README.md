# P01.04 — Persistent n8n data tables v1.0.0

Six new tables were created directly through the connected live n8n MCP in the existing personal project `nIsO1QWWbw69iEOr`. The project already contains the studio workflows and Creative Director archive. No workflows were edited or executed. Table IDs are recorded in table-registry.json; exact column definitions are in table-definitions.json.

| Table name | Purpose | Native JSON retained |
| --- | --- | --- |
| FWAI-LOCAL production_jobs v1 | Job, manifest revision/hash, current state and version | manifest_json, snapshot_json |
| FWAI-LOCAL scene_assets v1 | Scene asset identity, kind, readiness and provider-job link | asset_json |
| FWAI-LOCAL provider_jobs v1 | Provider operation, external ID, status and request reference | response_json |
| FWAI-LOCAL costs v1 | Provider-job cost entries, evidence, currency and amount | None |
| FWAI-LOCAL approvals v1 | Approval/validation receipts, actor and decision bound to revision | receipt_json |
| FWAI-LOCAL errors v1 | Stage, severity, retryability, resolution status and error details | details_json |

## Shared columns and relationships

Every table includes `record_id`, `schema_version`, `project_id`, `job_id`, `manifest_revision`, `manifest_sha256`, `is_test`, and `test_run_id`. n8n supplies its own numeric `id`, `createdAt` and `updatedAt` system fields. The business record ID is distinct from the n8n row ID.

Production-job records contain the exact serialized manifest text so its byte hash survives storage. `snapshot_json` preserves the P01.03 object and history. Its indexed state/version must agree with the JSON. All child records carry the same job ID, project ID and input revision/hash. Scene assets additionally refer to manifest scene IDs. `provider_job_record_id` in assets, costs and errors refers to the provider_jobs business `record_id`, not to a vendor ID or n8n numeric row ID. Nullable provider links support records not produced by a provider. An external `provider_job_id` stays null until a provider has actually accepted a job.

JSON objects are serialized into string columns because the connected n8n table interface exposes string, number, boolean and date columns, not JSON columns. Full objects are retained alongside useful searchable fields; no schema fields are silently discarded. Future writers must check agreement between indexed fields and JSON rather than trust whichever one is convenient.

`schema_version=1.0.0` identifies this table mapping. Manifest references remain compatible with production-manifest v1.0.0 and agent-result v1.0.0; the job snapshot and receipt match job-state v1.0.0. The scene asset JSON uses the existing manifest asset shape. details_json can retain a complete agent-result error object.

Cost amounts use integer micro-US-dollars (`amount_microusd`), with `currency=USD`; one USD equals 1,000,000 micro-USD. Estimates, reservations and actual charges must be distinguished by `cost_type` and evidence. Do not sum different cost types as though they were all expenses. Future writers must reject fractional/unsafe integers and implement rounding from provider billing units explicitly. The stored zero is a synthetic estimate, not a charge or budget authorization.

## Scope and enforcement boundaries

This checkpoint establishes live persistent storage, not a production data access layer. The exposed table tools do not configure unique constraints, foreign keys, JSON Schema enforcement or multi-table transactions. No database-level enforcement of those properties is claimed. Column types alone do not enforce lifecycle enums, positive revisions, immutable manifests, unique business IDs, safe cost integers or authorized approvals.

P01.05 will implement validation and revision immutability; P01.06 defines idempotency, retries, timeouts and recovery. Atomic state updates and uniqueness must be addressed before concurrent production writers are enabled. There is no read-then-insert loop claimed to provide exactly-once behavior here. The table creation was performed once after checking the existing inventory; a resumed installation must discover and verify names/IDs before writing.

An approvals row is not authenticated authorization by itself. Future trusted writers/resolvers must verify actor identity, decision, job/revision/hash and current validity. Agent-supplied values are not trusted receipts. Provider request_reference and response_json must not contain credentials; durable asset storage and provider URL expiry handling remain later checkpoints.

## Live acceptance evidence

One synthetic record was inserted into each new table (six total). All have `is_test=true`, `test_run_id=P0104-v1-storage-test-001` and `project_id=FWAI-P0104-STORAGE-TEST`.

- Job remains draft, state version 0, manifest pending review.
- Asset remains planned; no generated file is claimed.
- Provider is synthetic_no_provider, not_submitted, external ID null.
- Cost is a zero-dollar estimate.
- Receipt is pending, not a passed gate or human approval.
- Error is a labeled test_only informational fixture, not a production failure.

These six rows are intentionally retained as acceptance evidence. No existing rows were deleted. Future operational queries must explicitly select `is_test=false`, and writers must set this flag; null must not be treated as production. Tests should select the exact test_run_id. Never promote these fixtures into real approvals or jobs.

Each insert was followed by an independent MCP read with exact value comparison, then a second read confirmed the records remained unchanged. n8n assigned row IDs and timestamps. This demonstrates stored table retrieval across separate requests; no server restart or disaster-recovery test was performed. Seven offline test methods verify the captured live evidence, all six table schemas, exact JSON text/hash preservation, relationships, earlier contract compatibility and non-operational fixture status.

Run `PYTHONDONTWRITEBYTECODE=1 python3 test_storage_evidence.py` to recheck captured evidence without writing anything. It does not itself refresh live n8n evidence.

Existing four workflow definitions/activity timestamps and both Creative Director archive rows were compared before/after and are unchanged. No paid APIs, models, providers or publishers were invoked.
