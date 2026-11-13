# P01.06 completion record

Locked requirement: Define idempotency rules, retry limits, timeouts and recovery procedures for interrupted AI-generation jobs.

Implemented: versioned policy.json; operation identity and snapshot JSON Schemas; deterministic offline decision engine; explicit write-ahead/single-writer, budget reservation, provider reconciliation, retry and billing procedures. No provider-specific guarantee was assumed. Existing P01.01–P01.05 contracts, tables and workflows were not modified.

Acceptance evidence: 17/17 tests pass. An actual local process exited with code 17 after a synthetic provider accepted a request but before local provider-ID recording. Recovery used the original key, found the existing mock job and completed with one submission and one billing event; a second recovery reused the result. Result checksum and duplicate billing-event handling were verified. No real provider call, expense or publication occurred.

The live n8n tunnel stopped polling during final read-only verification (`tunnel_client_not_connected`). Initial inventory found four workflows and seven tables. No n8n mutations were attempted in this checkpoint. A fresh live inventory comparison remains pending when the tunnel is available; do not claim post-change verification.

The reference policy is not yet wired into the production webhook or local agents. Actual transport timeouts, provider support, authenticated approvals, serialized writes and durable recovery need adapter/orchestrator integration. The overall P01 exit gate remains open pending P01.07 and later integration. P01.06 satisfies its definition-and-test checkpoint; it does not certify live exactly-once provider behavior.

Status: P01.06 complete at the policy/reference level after installation tests. P01 is 6/7. Stop before P01.07 and ask the owner whether to continue.
