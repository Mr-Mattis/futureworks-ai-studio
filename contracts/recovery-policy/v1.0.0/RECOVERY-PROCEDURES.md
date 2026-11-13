# P01.06 recovery procedures v1.0.0

These are mandatory integration rules for the future trusted writer and provider adapters. The reference code tests decisions offline; it does not connect providers or change production workflows.

## Identity and deduplication

A logical generation operation has a stable identity: manifest version/project/revision/exact-byte hash, job ID, nullable scene ID, provider and account reference, operation, pinned model/version, request-body SHA-256, ordered input-asset hashes, and generation intent. Hash the exact persisted request bytes after materializing defaults/seeds/output settings; do not reconstruct a different body on replay. Secrets/tokens are excluded and must never be stored in contracts. Account reference identifies the billing scope without containing credentials.

`fwai-op-v1-<SHA256>` is computed from sorted compact UTF-8 JSON of that identity. The exact encoding is specified by recovery.py; other-language implementations must test against its output, not assume RFC8785 compatibility. Identity objects use strings/integers and arrays; request_sha256 binds arbitrary request JSON/file bytes without decimal canonicalization ambiguity. Ordered assets must retain their meaningful order. Transport attempt IDs, timestamps, expiring credentials and refreshed approval receipt IDs do not change the key. A model/prompt/seed/asset/revision change or intentional regeneration changes identity and requires a new approved generation intent and budget reservation.

Use deterministic business IDs for n8n records: provider_jobs.record_id is the operation key; request_reference points to the immutable persisted request. Reservation record_id is `reservation:<operation_key>`; actual charge record_id uses billing_event_key(provider-account, provider-event-ID). Preserve provider job ID once known. Do not merge unrelated invoice events merely because they have the same amount.

## Single writer and write-ahead order

1. Validate P01.01–P01.05 references, gate receipts and the exact request; refuse test records in production.
2. Acquire an exclusive OS lock held by the trusted writer across the entire read/check/write/network/result sequence. Future n8n flows must route mutations through that writer. Do not use an unlocked read-then-insert as a uniqueness guarantee. Do not steal a lock based on time alone; a paused former worker could still submit.
3. Under the lock, read by operation key. More than one matching row is an integrity incident: stop and reconcile. An existing operation is resumed, not created again. Reject same-key/different-request conflicts.
4. Confirm current owner/identity/spend authorization and reserve the worst-case cost once. Budget decision includes already committed actuals and outstanding reservations, including ambiguous requests. All reservation/charge writes are serialized. No reservation or approval means no submission.
5. Persist request, key, policy version, reservation reference, deadline, attempt counter and dispatching intent **before** any network submission. A failed or unconfirmed storage write stops the send.
6. Send the exact request once. Record the provider job ID and result as soon as received. If the process stops in between, the durable dispatching record requires reconciliation; it never means safe-to-resubmit.
7. Save accepted-job polling and download attempt counters before requests too. Keep a durable append-only event trail and reconcile interrupted multi-record writes before resuming. Do not release reservations or mark complete solely because a network call ended.

n8n's exposed data-table tools cannot configure unique constraints or multi-row transactions. The single-writer requirement is therefore a production prerequisite, not a claim that these existing tables provide atomic uniqueness. No trusted-writer service is deployed by this checkpoint; that belongs in P03. P01.06 defines the protocol and reference decisions. P01.07 may exercise them with synthetic components but cannot certify a paid provider's guarantees.

## Default limits

| Activity | Limit |
| --- | --- |
| Submission | 3 total attempts, including the original; only proven nonacceptance or verified native-key replay permits another attempt |
| Polling | 120 requests total per operation, at least 30 seconds apart |
| Download/retrieval | 3 total attempts per operation; all retrieve the same accepted job's artifact |
| Local deterministic task | 2 total attempts; temporary output discarded only after confirming worker exit |
| Connect timeout | 10 seconds |
| Submission response timeout | 60 seconds |
| Poll response timeout | 30 seconds |
| Download timeout | 300 seconds per attempt |
| Local task timeout | 900 seconds per attempt |
| Overall operation deadline | 3,600 seconds from first persisted creation; restart does not reset it |

These are conservative studio defaults, not claims about any vendor's supported durations. Adapters must implement actual transport/process timeouts. A known long-running provider can continue to exist after the studio deadline; stop automated work and reconcile, do not cancel/recreate it implicitly. Any longer limits need a reviewed versioned policy change.

Retry delay is min(300, 5 × 2^(attempt−1) + injected jitter of 0–5 seconds), or a larger valid Retry-After. Never shorten Retry-After to fit the backoff cap. If it exceeds the operation deadline, stop for review. Store the absolute next eligible time so restarts cannot erase backoff. Parse HTTP-date Retry-After in the adapter, accounting for clock skew; reference code accepts validated integer seconds. Clock moving backwards triggers review. Stop a local child, confirm its exit and verify no live duplicate before retrying. The reference engine covers provider-operation decisions; local-task termination remains an adapter requirement.

## Failure classification

| Observation | Required response |
| --- | --- |
| Local validation/rights/approval/budget failure | No call. Block until corrected; do not auto-retry. |
| Authentication or invalid request (401/403/validation 4xx) | Stop; fix credentials/input through authorized procedure. No blind retry. |
| 429 or 5xx with documented authoritative proof no job was created | Same operation/key, bounded backoff, current approval and reservation required. |
| 429/5xx without nonacceptance proof; timeout; broken connection; ambiguous response | Submission outcome unknown. Reconcile by key or request evidence. Keep reservation. |
| Known provider job ID | Poll/retrieve that job. Never generate again because a poll failed. |
| Poll transport failure/throttle | Count request, wait at least poll interval/Retry-After, retry read within poll/deadline limits. |
| Provider terminal generation failure | Record outcome/cost. Regeneration requires a new intent and new approved budget; not an automatic submission retry. |
| Artifact URL expired | Refresh URL for existing provider job, within retrieval limits; do not regenerate. |
| Download partial/corrupt | Preserve diagnostic details; retry same artifact within download limit. Never expose partial file as final. |
| Deadline/attempt limit reached | Stop automated action; reconcile existing provider/charge before any next generation. |
| User cancellation | Request cancellation only if supported/authorized; reconcile actual outcome and billing. Cancellation is not evidence of zero cost. |

Transport libraries, n8n node retries and provider SDK retries must be disabled or explicitly incorporated into these counters; nested invisible retries would defeat the limits. An aborted HTTP request does not prove the provider stopped work.

## Unknown outcome and native idempotency

Default: native idempotency is unsupported until verified in the future provider integration. No vendor capability is assumed here. If available, record the exact contract/reference, account scope, key behavior, request-match behavior, retention/expiry and any limits. Replay must reuse the same key and bytes, remain inside the verified window with response-timeout plus clock-skew margin, respect submission limits, and recheck authorization. Never change a request under an existing key.

Without that guarantee, query by key or captured request metadata. If an existing job is found, bind its ID and resume polling. If authoritative proof of nonacceptance is obtained, bounded same-intent retry is permitted. A mere not-found response from an eventually consistent list is not proof. If the provider offers neither a safe lookup nor idempotent replay, stop for manual review. Expired retention windows never authorize a new key automatically.

## Restart and reconciliation runbook

1. Start only the trusted recovery worker after confirming exclusive ownership; preserve original manifests, requests, counters, deadlines and keys. Verify hashes and schema versions. Corrupt/missing/conflicting data goes to manual review.
2. For prepared work with no dispatch intent, recheck current gates and the reservation, then schedule the first attempt.
3. For dispatching work without job ID, use the unknown-outcome rules above. A crash immediately before send and a crash immediately after remote acceptance are indistinguishable; favor reconciliation over duplication.
4. For a known accepted job, resume read-only polling. Never replace its ID or reset counters. After success, retrieve existing output.
5. Download into an operation-specific temporary file; flush/fsync, validate content/type/duration and checksum, then atomically promote to final storage. Reuse a final artifact only after its checksum is reverified on disk. Reconcile a file promoted before its asset row was saved rather than generating again.
6. Reconcile billing independently even when the artifact is complete. Apply each stable provider billing event once. A duplicate matching event is a no-op; conflicting amount/key demands review. If a provider supplies no stable billing event ID, do not invent deduplication certainty—hold for reconciliation. Verify final charges before releasing reservation. Estimated costs are not actual charges; never sum reservations and actuals for the same settled operation twice.
7. Save the recovery outcome and references in existing provider_jobs.response_json, errors.details_json, scene_assets and costs as appropriate. Mark the full production lifecycle forward only after P01.03 gates pass. Completion of one provider operation never implies ready_for_edit or published.

## Existing table mapping and compatibility

Recovery status is operation metadata, not a replacement for P01.03's ten lifecycle states. Store a versioned `recovery` object under provider_jobs.response_json, and corresponding event evidence under errors.details_json. P01.04/P01.05 allow those JSON objects without a column change. `request_reference`, `provider_job_id`, stable record IDs and cost evidence link the pieces.

For ambiguous submissions, the top-level provider status reflects only the last confirmed tracking state; consumers MUST inspect recovery.status=dispatching and must not infer safe resubmission from not_submitted alone. Do not write a queued/running/succeeded top-level status without a known provider ID. When polling stops at its limit, retain the last confirmed provider status and record the stopped/review-required recovery state separately; do not invent a terminal provider failure. Conflicting table and recovery identities are validation errors.

The existing revision guard enforces common row/reference consistency. The new snapshot schema and recovery.validate enforce key/counter/status consistency. Actual authentication, budget authority, storage durability and adapter guarantees must be independently established by integration. These records do not grant themselves permission.
