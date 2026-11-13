# P01.06 — Idempotency, retries, timeouts and recovery v1.0.0

This version defines the operational rules in policy.json and RECOVERY-PROCEDURES.md. recovery.py supplies an offline decision engine and snapshot schemas. It does not connect to n8n or any paid provider. The code binds a logical operation to an exact manifest revision, request, input assets, provider account, model and generation intent, then decides when to submit, reconcile, poll, download, reuse or stop for review.

A synthetic provider accepted one request before a separate process deliberately exited. Recovery located that existing job, downloaded a synthetic text artifact, recorded one billing event despite duplicate delivery, and reused the completed result on a second restart. See simulation-evidence.json. This proves the local policy path, not a real provider's idempotency guarantee or a complete end-to-end production recovery.

17 automated test methods passed. Tests cover stable identity, unknown submission outcomes, verified native-key replay, bounded attempts, Retry-After, authorization and reservation requirements, deadlines, clock rollback, download retries, billing-event deduplication and the process interruption. Run `PYTHONDONTWRITEBYTECODE=1 python3 test_recovery.py` in this directory. The tests use only installed Python and jsonschema; no packages or paid APIs are downloaded or called.

The transport adapter must persist the returned snapshot before any network action, hold exclusive trusted-writer ownership, enforce actual HTTP/process timeouts, verify provider idempotency or nonacceptance evidence, and reconcile bills. The existing P01.04 tables can carry the operation key, provider ID, reservation and recovery metadata without a schema change. These future integration obligations are spelled out in the recovery procedures. No workflow has been redirected through this policy yet.

The live n8n tunnel became unavailable during the final read-only inventory request. The tool reported `tunnel_client_not_connected`. We cannot claim a fresh post-change live verification. The work in this checkpoint made zero n8n writes or workflow calls, and the earlier read-only inventory showed four workflows and seven tables. Recheck live inventory when the tunnel reconnects. This limitation does not affect the offline tests but is recorded in the checkpoint.

P01.06 is complete as a versioned policy and tested reference implementation. P01.07's dummy manifest through all data-validation gates remains the final phase checkpoint and has not started.
