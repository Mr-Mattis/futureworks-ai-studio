# P02.01.07 continuation: verified tests and integration assessment

Status: **OPEN — development integration not implemented; isolation prerequisite blocked.**
This record supplements EVIDENCE-P02.01.07.md; historical unverified-test statements
there describe the earlier session. The master checklist is unchanged.

## Source and execution evidence

- Remote branch `dev/p02.01-atomic-proof` and checked-out HEAD both resolved to
  `1b3d4600acaa5a5fcf1bd6fd75beb6a71127b4ea` before this documentation change.
- Fresh authenticated clone under `/workspace/work/futureworks-ai-studio`;
  dedicated worktree `/workspace/work/futureworks-atomic-proof`. Initial status clean.
  Existing Windows/WSL checkout and its uncommitted changes were not accessible or altered.
- Environment: Debian 13 cloud Linux, Python 3.12.14; **not the owner's WSL**.
- From `agents/executive_producer/recovery`:
  `python3 -B -m unittest -v test_atomic_claim.py`: **11 tests passed**, 0.266 seconds.
  Includes 12-process claim and provider-reservation races, replay, interruption,
  hash/revision conflicts, invalid metadata, parent/key conflicts and no-authority checks.
  Test storage is temporary SQLite, not a production database. These tests were run
  directly in the cloud shell, without Bubblewrap; they are not an offline-isolation
  or WSL acceptance result. No provider API or live service was invoked by this suite.
- `sh agents/executive_producer/run-isolated-tests.sh`: blocked before test execution
  because `/usr/bin/node` is missing. An independent Bubblewrap namespace probe
  failed with `bwrap: setting up uid map: Read-only file system`.
  Per the Executive Producer README's instruction, "If namespace setup fails,
  stop; there is no fallback to running tests against the host network."
  The planner/canonical regression suite was not run outside its required isolation.
  No namespace workaround or privilege escalation was attempted.

## Existing worker compatibility

Reviewed `worker/worker.py`, `worker/Dockerfile`, and `compose.yaml` at the pinned HEAD.

The existing POST /jobs assigns a random 12-hex UUID for every submission. Its
thread lock protects only one process; JSON writes are direct and not transactional.
The queue is process-local, with one daemon consumer. Startup requeues queued jobs
and marks running jobs needs_review, without automatically retrying them. This
protects abrupt-restart handling but does not establish cross-process exclusion.
Provider exceptions during an ordinary run become failed jobs; provider receipts
are not durably recorded before polling. A submission timeout can therefore leave
an unknown billable result. No automatic resubmission was observed in this code,
but resubmitting the same brief creates another random logical job.

Paid generation uses ENABLE_PAID_GENERATION, credential-presence checks and a Runway
estimate cap. These are not canonical per-operation approval receipts or an aggregate
budget for all providers. Upload readiness remains false. The worker image copies
only worker.py; it cannot import the repository's claim module as currently built.
Compose supplies provider credentials and production output mounts, so it must not
be reused as the isolated development test environment.

## Minimal integration design (not deployed)

1. Add a separate development adapter and entry point, with explicit temporary
   database/output paths and no imports of the legacy worker's provider pipeline.
   Leave the existing endpoint, image and compose untouched. No JSON migration yet;
   rollback is stopping the development entry point and retaining its database.
2. Validate exact canonical manifest bytes and immutable revision/hash references
   before accepting `(project_id, run_id)` as logical identity. Do not derive identity
   from the manifest hash alone: a reused run ID with changed bytes must conflict.
   Derive operation keys from that identity plus stable scene, provider and operation
   identities; do not accept arbitrary caller keys as the only duplicate defense.
3. Persist request, immutable payload and pending execution intent in one transaction.
   Treat any in-memory queue as a wake-up hint. Use a durable outbox so a crash after
   claim commit but before enqueue cannot strand the job. Independent consumers need
   atomic ownership tokens and fenced state updates, not only a request primary key.
4. Do not use `claim(..., interrupted=True)` as a generic restart detector: the current
   proof only resumes requests already inserted as interrupted. A crash after a
   normal claim leaves claimed state. Recovery needs explicit safe-state transitions;
   elapsed time alone cannot prove another worker stopped or a provider did not accept.
5. Reserve each provider operation before any possible side effect. Keep the current
   proof's not_submitted-only constraint for zero-cost tests. Future submission support
   needs separately reviewed durable submitting/unknown/receipt states; a lost response
   or crash after intent must require reconciliation, never automatic paid resubmission.
   Reservation uniqueness is not provider-side exactly-once delivery.
6. Keep all authorization false and omit dispatch/publication capabilities. Require
   canonical approval and budget enforcement separately before any future paid path.
7. Test simultaneous full submissions, crash-after-commit-before-enqueue, fenced
   consumer recovery, repeated recovery and provider ambiguity in isolated storage.
   Re-run planner and canonical regressions under the approved isolation first.

## n8n reconciliation assessment

Read current definitions through the n8n connector; neither workflow was changed or run.

- Executive Producer `HBvqaDLfhurpNLlu`: inactive, 8 nodes, version
  `43661066-75d9-4c81-b965-2fb98f7a84b9`.
- Recovery harness `QBVsaXHigHIP5cbi`: inactive, 9 nodes, version
  `665638b3-0e7a-4b38-a1a5-cd795129064e`.
- Execution metadata rechecked: 42–44 succeeded; 45–47 succeeded; 48 error;
  49–52 succeeded. No execution payload was revalidated here and no new execution
  IDs were generated. Metadata alone does not establish expected rejection details.
- Importantly, 49–52 ran in separate, non-overlapping intervals (about one second
  apart). They do not provide a simultaneous-writer test, even if launched closely.

Tracked workflow.inactive.json is a six-node Basic LLM Chain candidate with a
configure-locally model placeholder, strict proposal validation and a blocked
canonical-validation handoff. The live draft instead uses an AI Agent node,
qwen3.6:latest, an Ollama credential reference, a manual role fixture, and an
executeWorkflowTrigger. Its schema permits additional properties and its role
labels/creative_constraints representation differ from the tracked profile.
The live validator checks exact five-scene identity and seven specialist owners,
but uses gate text substring checks; it does not provide the tracked dependency
graph checks. It emits succeeded with an empty top-level blockers list even when
the output contains planning blockers, and uses a baseline instance identity
rather than the current workflow ID. Authorization remains false.

These are semantically different candidates, not interchangeable exports. This
source-controlled assessment records the divergence without replacing the stronger
canonical candidate with a live snapshot. Behavioral reconciliation remains pending:
define a reviewed mapping, preserve blockers and registry identity semantics, then
test malformed inputs and Python/JavaScript agreement under required isolation.
No credentials or workflow credential references have been copied into source.
The recovery harness uses lookup followed by insert/update in n8n data tables;
it has no connection to this SQLite proof and cannot establish atomicity.

## Remaining acceptance and next action

Obtain an approved environment with working user/network namespaces, system Node,
Python/jsonschema and access to the owner's development WSL worktree. Run the
required isolated regressions there before implementing and testing the adapter.
WSL source verification, development-worker integration, provider-ambiguity tests,
canonical workflow reconciliation and owner acceptance remain unverified.
P02.01.07 stays open; P02.01.08/.09 and P02.02 have not been advanced.
No production code, workflow, database, deployment or authorization state was changed;
no spending, publishing, merge or paid provider operation was performed.
