# P01.05 — Complete at the guarded implementation level

Requirement: schema validation and immutable revision IDs so later agents cannot silently overwrite approved scripts.

Implemented revision_guard.py with strict manifest/agent-result validation, validators for all six data-table row shapes, stable project/revision/SHA-256 IDs, exclusive append-only manifest commits, conflict rejection, revision reset rules and revision-bound receipt checks. New scripts require a new revision and fresh approval. Earlier schemas, table definitions and production workflow behavior are preserved.

Live changes: two new synthetic draft records in existing production_jobs table nBhvxQQ3GZhoHF78 for FWAI-P0105-LIVE-TEST revisions 1 and 2; two exact immutable manifest files under data/manifest-revisions/FWAI-P0105-LIVE-TEST. No table or column changes, no approval records, no paid calls and no publishing.

Tests: 15/15 methods pass. Includes two-process conflict test (one winner, one rejection), approved-script overwrite rejection using synthetic local receipt, seven prior invalid manifests rejected, invalid row relationships/types rejected, new revision pending-review requirement, stale receipt rejection and exact live readback for both new records. Local rejection attempts were not sent to n8n.

Evidence: dependencies.json, preflight-evidence.json, n8n-write-candidates.json, n8n-jobs-before.json, n8n-jobs-after.json, production-preservation.json, test-results.txt, installation-verification.json and SHA256SUMS.

Scope boundary: protection is implemented in the guarded path and exercised with live storage. It is not a native n8n database constraint, authenticated approval service or automatic retrofit of existing workflows. P02/P03 must route new agents through the trusted writer; P01.06 still owns distributed job idempotency, retry/timeouts and recovery policy. Direct administrative writes remain outside this protection.

Status: P01.05 complete after installation verification PASS. P01 is 5/7; phase exit gate remains open. Stopped before P01.06. Ask the owner whether to continue with the next checkpoint.
