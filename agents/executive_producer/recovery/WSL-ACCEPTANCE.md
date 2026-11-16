# P02.01.07–P02.01.09 — WSL development acceptance evidence

Date: November 15, 2026 (America/New_York). This record supplements the historical
proof and cloud-session records. It does not amend MASTER-CHECKLIST-v1.0.md.

## Acceptance status

**P02.01.07: verified complete for the isolated, zero-cost development integration.**
**P02.01.08: implementation and acceptance evidence consolidated.**
**P02.01.09: development branch ready for draft merge review; owner approval pending.**

P02.01 as a whole remains pending owner acceptance. P02.02 is not started.
No production deployment, migration, paid-provider authorization or publication
has been approved or performed. Production validation is explicitly unverified.

## Environment and source

Remote Desktop Commander reached authorized device El_Corredor and its running
WSL2 Ubuntu 24.04.4 distribution. The prior cloud terminal was a separate Debian
environment; its isolation failure did not mean the WSL machine was inaccessible.

The main checkout and detached Executive Producer worktree were initially clean.
No existing atomic worktree existed. Git fetched the named remote branches and
created /home/mattis983/futureworks-studio/futureworks-atomic-proof on
dev/p02.01-atomic-proof. Initial local and remote HEAD both equaled
a425acdd5aded8ba6b4014420e2d8ab0b10e500d. No local changes were overwritten.

Implemented source commits:

- 124a612378dc360820d37478d6be46798fe0884d — transactional development worker.
- bdc44e318c54b8dff1c3c750f0a9b424621c169e — canonical n8n reconciliation and test runners.

These commits retain the original SQLite proof and its eleven tests. The shared
claim primitive now participates in a caller-owned transaction so identity and
durable work intent commit together. A separate project/revision table pins
manifest bytes even across different logical run IDs.

## Verified tests

The actual final terminal transcript is WSL-TEST-RESULTS.txt.

| Test group | Command | Result |
| --- | --- | --- |
| Existing Executive Producer and isolation | sh agents/executive_producer/run-isolated-tests.sh | 21 passed |
| Original atomic claim proof | python3 -B -m unittest -v test_atomic_claim.py, inside Bubblewrap, recovery directory | 11 passed |
| Worker integration and exact n8n wrapper | sh worker/run-isolated-dev-tests.sh | 22 passed |
| Six existing P01 contract suites | sh agents/executive_producer/reconciliation/run-contract-regressions.sh | 65 passed |
| Total | Four isolated invocations | **119 passed, zero failures** |

Python 3.12.3, /usr/bin/node and Bubblewrap were available in WSL. Each invocation
used a separate network namespace, cleared environment, read-only development
source and private temporary storage. No Docker socket, credentials, production
database or actual production home was mounted. For legacy absolute contract paths,
the P01 runner aliases only this checkout's read-only contracts under a private
namespace path; it does not mount the real home directory.

The worker tests verify:

- A synchronized barrier releases twelve independent processes into full submission:
  one durable job, eleven duplicates. Twelve consumers then process it once.
- This also passes using the exact candidate from successful n8n execution 54.
- A process exits after submission commit without enqueue; another process finds
  the durable queued intent. A separate process exits after ownership acquisition;
  explicit token-fenced recovery resumes the same job and rejects stale owners.
- Repeat recovery, duplicate submissions, changed plans, invalid metadata,
  conflicting revisions and changed revision bytes under a different run ID are
  rejected without creating extra jobs.
- Transaction failure after identity insertion rolls back the claim and work
  intent together. Failed handoff validation rolls back reservations.
- Deterministic operation keys remain unique and persist through recovery.
  The fixture has 25 required enabled operations: five scenes times image, video,
  voice, sound effects and captions. Every reservation remains not_submitted.
- Injected ambiguous operation outcomes move the job to needs_review; replay
  cannot enqueue it, and recovery/old-owner completion are rejected.
- Canonical handoffs remain blocked and preserve planning blockers. All three
  authorization flags stay false. No provider client or publication capability
  exists in the adapter.

## Failures found and corrected

Initial new worker tests had three incorrect 30/60-operation expectations; the
fixture actually requests 25/50 operations. These assertions were corrected after
the failed run was observed, not counted as passing.

Adding full canonical envelope validation exposed a short test run ID that the
reference claim helper allowed but the P01 contract rejects. The adapter now
validates canonical run metadata before storing a claim, with a rejection test.

One wrapper test incorrectly treated the word credential in role instructions as
a credential value. It now checks mutation types and credential fields structurally.
No credentials were copied into source. Initial isolated node-config validation
also needed model/parser subnode descriptors; validation passed once those existing
connections were represented correctly.

## Worker compatibility and rollback

See worker/README-development.md and CONTINUATION-20261115.md for the original
JSON-worker assessment. The new adapter is a separate Python/CLI development
entry point. The existing HTTP /jobs endpoint, JSON job storage, startup
needs_review policy, worker image and compose are unchanged. No migration occurs.

The durable queue and token checks run in SQLite transactions on one shared local
filesystem. This is not a multi-host/network-filesystem design. Development
completion means a blocked planning handoff, not completed generation.

Stopping the separate development entry point leaves legacy production unaffected.
Retain its isolated database for investigation if needed. A production migration,
rollback plan and real per-provider reconciliation implementation require a
separate review before introducing any live side effects.

## n8n reconciliation and actual executions

Reviewed the existing definitions before editing. Kept workflow
HBvqaDLfhurpNLlu inactive and changed only this explicitly identified development
workflow. Its credential references were left unchanged. The recovery harness
QBVsaXHigHIP5cbi was not changed or executed in this continuation.

The old live draft differed from the six-node tracked synthetic candidate: it used
an AI Agent node, legacy role labels/field types, substring gate checks and an
empty top-level blockers list. Reconciliation retains the canonical schema,
shared validate-plan.js checks, exact five-scene identity, seven role assignments,
dependency validation, human-owned gates and false authorization.

The manual fixture is now the canonical synthetic manifest, and input preparation
rejects alterations to that frozen context. The orchestrator trigger is disabled
and disconnected: this development acceptance path is not an unrestricted intake
or a P03 orchestrator. The existing node ID/name for the planning role remains,
but its type now matches the tracked Basic LLM Chain architecture.

- Execution 53: failed closed at structured parsing with Invalid JSON in model
  output. It made no downstream dispatch and was not repaired automatically.
- The development draft was aligned to the tracked Basic LLM Chain and given a
  16,384-token local context. Parser auto-fix and node retries remain disabled.
  The precise contribution of agent formatting versus context size was not
  isolated; no stronger root-cause claim is made.
- Execution 54: succeeded using existing local qwen3.6:latest, with five scenes,
  seven specialist packages, blockers and false authority.
- The exact final candidate and minimal provenance are in
  reconciliation/execution-54.json. No runtime resume token, credential reference
  or unrelated execution payload was retained.
- The final worker tests ingest those exact candidate bytes, revalidate through
  canonical Python contracts, race submissions/consumers and persist one blocked
  handoff without duplicate reservations. This is a controlled artifact handoff,
  not an automatically deployed n8n-to-worker service.

reconciliation/build_live_patch.py records the credential-free change from the
original snapshot. live-before.redacted.json preserves the earlier parameter/
connection configuration without credential references. For rollback, restore
those parameters/connections using the existing credentials; do not blindly import
the redacted evidence as a credential-bearing deployment.

Final live version: 34b0350a-b43b-4848-b0cb-94eb91c31242. Fresh readback matched all
six source-controlled parameter blocks; credential equality was checked in memory.
live-readback.json records those checks and confirms inactive state, no tool
connections and the disabled/disconnected orchestrator entry.

Previously reported executions 42–52 remain historical evidence. In particular,
49–52 ran in non-overlapping intervals and do not establish simultaneous-writer
safety. The synchronized multiprocessing tests provide that development evidence.

## Governance and limits

Protected worker.py, Dockerfile, compose.yaml and locked master checklist bytes
were compared against origin/main and matched. Accepted contract sources were
unchanged and passed their regression suites. Only the identified inactive n8n
development draft was modified. No production datastore or working production
workflow was changed. No paid API, identity-generation or publishing call occurred.

Common token/private-key signature scanning found no matches in changed files;
this is a bounded check, not a claim of perfect secret detection. The branch
contains no environment file, production database, private media or credentials.

Real provider-side exactly-once behavior is **not verified**. The safe behavior
implemented here is reservation plus refusal to submit or retry. A synthetic
ambiguity flag cannot substitute for a real provider receipt/status reconciliation
test. Such a test must be authorized separately before enabling a provider path.

The existing GitHub Actions job covers the eleven atomic tests; the full 119-test
result is independently executed WSL evidence, not a claim that CI ran all suites.
Production acceptance, permanent service wiring and full P02.01 owner acceptance
remain pending. Review the draft PR; do not merge without owner authorization.
