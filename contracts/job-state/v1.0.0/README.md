# P01.03 — Job state transitions v1.0.0

The exact locked lifecycle is:

`draft → research → scripted → planned → approved → generating → assembling → qa → ready_for_edit → published`

`transitions.json` is the machine-readable transition table. `job_state.schema.json` defines the snapshot and its transition history; `gate_receipt.schema.json` defines references to verified transition evidence. `job_state.py` is a pure, offline reference implementation. These are new standalone contracts, not changes to production workflows, manifest v1.0.0 or agent-result v1.0.0.

| Transition | Required evidence gates |
| --- | --- |
| draft → research | brief_validated |
| research → scripted | research_complete, script_validated |
| scripted → planned | visual_plan_ready, avatar_plan_ready, budget_plan_ready |
| planned → approved | human_production_approval |
| approved → generating | generation_authorized, budget_authorized |
| generating → assembling | assets_complete |
| assembling → qa | assembly_complete |
| qa → ready_for_edit | technical_qc_pass, creative_qc_pass, disclosure_rights_pass |
| ready_for_edit → published | owner_publish_approval, publication_confirmed |

The state describes lifecycle progress, not an instruction to start a paid job. `published` records confirmed, owner-authorized publication; it does not issue a publish request. Merely being ready for editing never implies publication approval. Synthetic examples reaching published are contract tests, not a real upload.

## Trust boundary and evidence

`create_draft` accepts a reference obtained from a validated production manifest. It validates the reference's structure, not the entire manifest. The reference contains exactly the same schema version, project ID, integer revision and exact-file SHA-256 used by agent-result v1.0.0. Tests compare it with both installed prior contracts.

`transition` takes a trusted job snapshot, the next target, expected state version, the same manifest reference, a map of gate names to receipt IDs, and an explicitly supplied trusted receipt resolver. It resolves every required receipt and checks its job, revision/hash, gate, receipt type, decision and actor. Missing, failed, pending, revoked or mismatched receipts reject the transition. Human approvals require an owner actor; agent claims cannot serve as independently verified evidence.

This function is NOT an authentication system. The future orchestrator must load snapshots and receipts from trusted persistent storage and authenticate the actor that created each receipt. Never accept a resolver or receipt body supplied by an agent or an untrusted request. A string saying `owner` does not establish identity. The only resolver supplied here is a synthetic test fixture. No real approvals are fabricated or recorded.

`budget_authorized` is a reference to a future deterministic budget decision, not the Budget Controller's estimate. This checkpoint neither calculates/reserves funds nor implements approval policy for generation, media identity rights or publication. Those services must issue trustworthy receipts under their later checkpoints. Schema-only checks do not establish factual evidence.

## Rejection, revision and concurrency semantics

Only nine forward edges exist. Skips, backward moves, self-transitions, unknown stages and transitions out of published are rejected. Rejection returns no new snapshot and leaves the original unchanged. Errors do not introduce extra lifecycle stages; recording errors is P01.04, recovery/retries P01.06.

The reference implementation retains one manifest reference throughout the path. It does not edit manifests or merge agent outputs. A revised script cannot silently reuse this job's approval: a separately reviewed revision needs the revision-management protocol in P01.05. Approval receipts are external to the manifest; this contract does not rewrite its embedded approval_state.

`state_version` increments with each transition and must match the supplied expected version and sequential history. This detects stale inputs within the reference API. It is not an atomic database lock: P01.04/P01.06 integration must persist state with an atomic compare-and-set or equivalent locking strategy. This checkpoint does not claim duplicate-job prevention, durable recovery, retry behavior or end-to-end phase completion.

## Verification

Run `PYTHONDONTWRITEBYTECODE=1 python3 test_job_state.py` in this directory. Uses existing Python/jsonschema only; no downloads. Twelve test methods cover all 100 source/target pairs (9 allowed, 91 rejected), every required gate, receipt and approval failure modes, stale state, revision mismatch, history integrity, non-mutation and compatibility with installed P01.01/P01.02 fixtures.

Examples use synthetic receipts only. `example.lifecycle.json` contains all ten snapshots; `example.receipts.json` makes test provenance explicit. No test calls a model, n8n workflow, provider API or publisher.

P01.03 is complete at the state-contract/reference-implementation level. P01.04 is next and remains unstarted. The overall P01 exit gate remains open.
