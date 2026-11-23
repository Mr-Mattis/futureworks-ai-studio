# P03 — Master Production Orchestration: Isolated Development Acceptance

**Decision: P03.01–P03.08 implemented and development-verified (8/8 technical).**
**Production deployment, real credentials, provider integration, actual spending, publication, and branch merge: NOT APPROVED.**
**PR review and owner merge authorization: PENDING.**

Date: November 15, 2026, America/New_York. Evidence supplements the original locked
`governance/MASTER-CHECKLIST-v1.0.md`; it does not change scope or skip later phases.

## Verified baseline and branch isolation

- Source branch `dev/p03.01-p03.08-orchestration` was created from merged P02
  branch `dev/p02.01-executive-producer` at `538ca83`.
- Isolated WSL worktree:
  `/home/mattis983/futureworks-studio/futureworks-p03-orchestration`.
- The accepted P02 roles and P01.02 canonical contracts are reused, never
  overwritten. Existing worker, Dockerfile, Compose and production n8n
  workflows are unchanged. No change to `main`.
- Existing active Creative Director `xs4sxANjgMcQS25p` and active production
  worker workflow `Axm40lskQWoxf1XM` remained active/unmodified.
- P03 n8n drafts `F9DwOI01m1c4ld3Y` and `9EzAAns1xeJDPZJe` remain **inactive**.

## P03 checkpoint evidence

| Checkpoint | Implementation | Controlled acceptance |
| --- | --- | --- |
| P03.01 | `FWAI-DEV — P03 Master Production Orchestrator` saved and validated as an inactive n8n SDK workflow; durable independent Python orchestration engine. | Seven-stage replay reaches `awaiting_approval` without external tool dispatch. |
| P03.02 | Webhook creative-brief intake in n8n; canonical project, exact immutable manifest SHA, strict source-validated fields; authenticated general API and opt-in one-shot frozen smoke path. | **n8n execution 69**: actual HTTP Request from n8n into WSL dev engine succeeded; replay-only concept, exact fixed manifest, no public published workflow. |
| P03.03 | Revalidate prior real Executive Producer execution **54** work packages; route to Research, Creative, Visual, Avatar, Budget, Editing and QC with immutable identifiers. | Local seven-role synthetic replay and separate hybrid local Ollama run both complete; no production handoff. |
| P03.04 | P01 manifest/role result validation, P02 role-specific JSON schemas, exact scene/project references and DAG/dependency checks before final handoff. | Malicious role output, missing keys, changed manifest hashes and false authorizations rejected. |
| P03.05 | Sequential Research → Creative, concurrent Visual/Avatar, then Budget → Editing → QC; SQLite claims and atomic durable intents. | 12-process race admits only one task claimant, parallel ready-stage coverage, crash/replay tests. |
| P03.06 | Persistent human, budget and publication approval gates; all remain `pending`; no authority-granting API. | End-to-end tests and n8n final gate enforce false authorization and zero dispatch; deliberate override fails. |
| P03.07 | Durable **mock-only** asynchronous-status polling, bounded retries, failure/review queue and fenced local recovery. | Mock receipts can reach simulated complete or `needs_review` after bounded polling. No real provider API is called; actual provider receipts are P05/P03 deployment integration. |
| P03.08 | JSON status dashboard, stage attempts, costs, assets, blockers/issues, provider/mock queues, pending approvals; authenticated dashboard API and read-only WSL CLI. | n8n execution 69 returned seven stage passes, all pending approvals, zero costs and assets, no dispatch. |

## Live model and transport evidence — distinct tracks

**A. Real n8n transport to WSL, synthetic role replay — execution 69**

- Workflow: `9EzAAns1xeJDPZJe` (`FWAI-DEV — P03 One-Shot Synthetic Transport`).
- n8n result: `success` (not merely pinned HTTP); actual n8n HTTP Request
  contacted temporary isolated WSL server at `/v1/demo-once`.
- One fixed concept: `FWAI-EP-0001` at manifest SHA
  `cf2bbd17b2170755fef18de1be5ea4c08694ee894c8167c70ed322aa9906fe87`.
- Server auto-routed seven durable planning stages by replaying previously
  validated **real P02 Ollama model outputs**, with explicitly synthetic
  per-stage project ID substitution for earlier unrelated dummy projects.
  **This execution did not invoke fresh Ollama models.**
- Result: seven stages `passed`; status `awaiting_human_approval`;
  all three approval records `pending`; `costs_usd=0`,
  `assets_ready=0`, `dispatch_performed=false`, and all authorization
  flags false. Full redacted result: `evidence/n8n-execution-69.json`.
- The one-shot endpoint is **not an authenticated general public endpoint**;
  it accepts one exact dummy fixture and is disabled by default. It was
  enabled only during the controlled smoke test. The development bridge was
  stopped and its ephemeral token invalidated immediately after execution.
- The main n8n orchestrator source is stored with credential placeholders;
  it cannot be activated until approved n8n secret-backed credentials are
  provisioned. It was also tested by n8n execution **67** with pinned HTTP
  results (not actual network), which passed the approval gate; execution
  **68** correctly rejected an unauthorized webhook.
  
**B. Local Ollama live routing — WSL run `P03-HYBRID-OLLAMA-001`**

- Seven-stage local pipeline completed **successfully** using the actual
  installed `qwen3.6:latest` model for **six newly inferred role results**:
  Research, Visual, Avatar, Budget, Editing and QC.
- Creative Director role output was the **previously generated**, validated
  n8n P02.02 execution **59**, reused **only after exact immutable manifest
  reference and project identity checks**; it was not freshly generated.
- Executive Producer plan came from previously validated execution **54**
  and was revalidated against the exact P01 manifest.
- Final: seven planning stages passed on first attempt, with durable
  role-specific canonical P01.02 envelopes, three pending approval gates,
  zero spending, zero assets and false dispatch/authorization flags.
  Evidence: `evidence/live-hybrid-seven-stage.json`.
- Earlier **fully fresh** run `P03-FRESH-OLLAMA-20261115-001`
  successfully generated Research but **twice rejected** short Creative
  narration, then stopped in `needs_review`. This is a verified
  fail-closed negative test, **not** a passing complete fresh inference.

## Offline regression acceptance

Last complete retained source and WSL test rounds:

| Suite | Count | Result |
| --- | ---: | --- |
| P01 six canonical contracts | 65 | passed |
| P02.01 Executive Producer | 21 | passed |
| P02.01 development-worker/bridge | 23 | passed |
| P02.01 atomic concurrency/recovery | 11 | passed |
| P02.02–P02.10 nine-role suite | 21 | passed |
| P03 engine, API, exact n8n VM source, one-shot transport and asynchronous mock polling | 49 | passed |
| **TOTAL** | **190** | **zero failures** |

Bubblewrap used `--unshare-all`, read-only checkout binding, cleared
environment, private `/tmp`, no network, production mounts, host
credentials or Docker sockets. The live local Ollama run was **separate**
from the networkless suites and was explicitly constrained to the
owner's local inference endpoint.

## Real-world limitations intentionally deferred

- No production orchestrator activation or automatic handling of arbitrary
  user briefs. The one-shot n8n end-to-end run accepted only one fixed
  approved synthetic manifest.
- The durable model pipeline and webhook transport are separately validated;
  a secure persistent n8n → development worker connection with managed
  credentials needs a new gated integration proof. The generic n8n master
  workflow is **not yet configured with real secure credentials**.
- P03 mock provider polling does **not** establish real provider-side
  exactly-once behavior, live asynchronous receipts, actual charges,
  live video generation, or real performance analytics. Those remain
  locked to later P04–P12 approvals.
- Creative Director live generation still needs hardening for short narration
  before arbitrary new concepts can consistently complete without cache.
- All real user approval workflows and production release processes remain
  explicitly outside this isolated development proof.

### Additional asynchronous recovery hardening

The latest isolated P03 regression suite has **49** tests (two additional
tests over the initial 47). P03.07 now uses a bounded, temporary,
**actual background polling thread** for *mock-only* receipts, persisted
`next_poll_at` backoff, exactly two attempts, and durable restart
continuation. Tests verify background scheduling, crash-safe resumption and
unresolved status quarantine, without opening provider HTTP connections.
The full P01–P03 local regression total is therefore **190 passed**.

## Disposition

**P03.01–P03.08: 8/8 locally implemented and technically verified in isolated
development**, including one real n8n-to-WSL synthetic transport replay and
one successful seven-stage hybrid local Ollama planning path. The locked P03
development exit scenario reaches the correct pending approval gate with no
manual execution of individual nodes, paid calls, or publishing.

**Owner and merge approval remain pending.** Keep the PR in draft. Do not
advance into P04 production/image generation or turn on P03 live intake
without explicit authorization and credential/backup review.
