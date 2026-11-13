# P01.05 — Schema validation and immutable revisions v1.0.0

This package implements the validated revision write path for the existing manifest, agent-result, job-state and n8n table contracts. Earlier versioned contracts and running workflows are unchanged. No new service or database is introduced: immutable manifest files live in the project's existing filesystem; n8n remains the job/asset/provider/cost/approval/error record store.

## Revision identity and storage

The business revision ID is `<project_id>:r<revision>:<sha256>`, where SHA-256 hashes the exact UTF-8 manifest file bytes. The existing integer `revision` field is unchanged. Guarded production_jobs rows use the revision ID in the existing `record_id` column, without adding columns or altering schema v1.0.0. The full manifest text and P01.03 snapshot remain stored in n8n.

Manifest files are stored under `data/manifest-revisions/<project_id>/r<revision>.json`. Revision numbers start at 1 and increment consecutively per project. Existing revision files are never opened for writing by this API. An identical commit returns the existing reference; changed bytes at the same project/revision are rejected, including whitespace-only changes. Revision IDs and file hashes are checked on reads. Content editing requires a new integer revision, new hash, new job identity and fresh approval.

`RevisionStore.commit` validates the manifest before storage, takes a per-project filesystem lock, writes and fsyncs a temporary file, makes it read-only, and publishes it with an exclusive hard link. The destination is never replaced. Directory sync completes the commit. The two-process conflict test proves that different contents competing for one revision yield one successful commit and one rejection. This is local filesystem revision protection, not distributed job/expense idempotency.

Every new submission must be pending_review with null approved_revision, approved_by and approval_record_id. Human decisions belong in revision-bound external approval receipts. The manifest is not rewritten to toggle approval. P01.03 can use those receipts to advance the job independently. No import of already-approved legacy manifests is silently performed. A future migration must retain their provenance and exact bytes under an explicitly reviewed import procedure.

## Validation entry points

- `manifest(raw)` enforces strict JSON, the pinned P01.01 schema and its deterministic invariants. Duplicate keys, NaN, Infinity, numeric overflow and unsafe revision integers are rejected. Existing P01.01 optional-key exceptions are caught and rejected; that earlier code is not changed.
- `RevisionStore.prepare_job` commits a valid pending manifest and constructs a P01.03 draft snapshot and P01.04 production_jobs row.
- `RevisionStore.validate_agent_result` runs the existing P01.02 validator against the exact saved manifest, retaining identity, hash, scene and status checks.
- `RevisionStore.validate_row` validates all six P01.04 row layouts, types, version/test identity, job/revision context, embedded JSON and indexed-field consistency. It checks scene references, provider links, safe nonnegative integer USD amounts, provider/error enums, receipt identity/type/actor shape and generated-asset file/checksum requirements. Full agent errors use the P01.02 error schema.
- `RevisionStore.preflight_insert` rejects a production-job insert conflicting with any supplied existing project/revision, record ID or job ID. It does not expose an update/overwrite operation and only accepts new draft jobs.

The read-only `dependencies.json` hashes pin earlier contract dependencies; changed dependency bytes fail validation rather than silently switching contracts.

Example CLI, producing a candidate row rather than writing to n8n:

```
PYTHONDONTWRITEBYTECODE=1 python3 revision_guard.py MANIFEST.json \
  --store /home/mattis983/futureworks-studio/futureworks-ai-studio/data/manifest-revisions \
  --job-id UNIQUE-JOB-ID
```

For a test add `--test-run-id TEST-RUN-ID`. The CLI marks those rows is_test=true. Future production consumers must exclude test rows explicitly. There is no network/client credential in this package.

## Required integration boundary

This checkpoint supplies and exercises the guarded implementation. Existing local agents and production workflows have not yet been rerouted through it; agent rollout/orchestration remain P02/P03. Direct n8n edits can still bypass these application checks. The exposed table API has no unique constraints or transaction controls, and a read-before-insert preflight is not a distributed lock. Future orchestration must use one trusted writer or equivalent serialized/atomic coordination before enabling concurrent production writes. P01.06 will define the job/retry/recovery policy; no exactly-once provider or expense guarantee is claimed here.

The revision root must be owned by the trusted writer and not exposed as an agent-writable folder. Read-only file modes, hashes and append-only API behavior do not protect against a privileged administrator rewriting both files and records. Hash verification detects disagreement with the saved reference; it does not authenticate an actor. Passed approval receipts require independently authenticated owners/services; a JSON field saying owner does not prove consent. This API validates structure and binding, not human identity.

Existing P01.04 test rows use the old fixture record IDs. They remain unchanged and are not automatically migrated or accepted as new guarded revision rows. The new policy applies to new guarded submissions. Legacy production paths remain working and unchanged.

## Live acceptance

Two synthetic pending manifests for `FWAI-P0105-LIVE-TEST`, revisions 1 and 2, were committed through this API. Two draft/is_test rows were appended to the existing production_jobs table after validation and preflight; no updates were issued. Readback matches every field and exact stored manifest bytes. Deliberate same-revision edits and duplicate identity attempts were rejected before any n8n write. No real human approvals were created: the approved-script protection test uses an explicitly synthetic in-memory receipt only.

15 automated tests cover invalid manifests/JSON, all six row validators, stale receipts, revision conflicts, concurrency, tamper detection, prior-contract compatibility and the live n8n capture. `test_restart_retains_revision_and_tamper_detected` reopens the repository object; it is not a machine restart or full recovery test. The two new draft rows and two manifest files are retained as evidence. Existing jobs, five other new tables, Creative Director archive and all four workflows are unchanged.
