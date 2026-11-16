# P02.02–P02.10 — Nine Local-Agent Development Acceptance

**Status: NINE ROLE IMPLEMENTATIONS VERIFIED in isolated development.**
**P02 phase exit gate: development evidence satisfied; formal owner/merge review remains pending.**
**Production deployment and P03 orchestration are NOT approved.**

Date: November 15, 2026 (America/New_York). This evidence supplements, but does not amend, `governance/MASTER-CHECKLIST-v1.0.md`.

## Controlled scope

The owner challenged the project to implement all nine remaining P02 roles using the same isolation, canonical contract, role-specific acceptance, source-control and no-paid-effects standards accepted at P02.01. Work proceeded from the *merged* PR #1 commit `e1b4ad0314b3969481d500efbc70aa98a9f8b39d` on `dev/p02.01-executive-producer` into an independent `dev/p02.02-p02.10-local-agents` branch and WSL development worktree `/home/mattis983/futureworks-studio/futureworks-p02-agents`. The existing `main` branch was not advanced.

**The eight existing specialist n8n drafts were retained and hardened** rather than replaced. The active production Creative Director (`xs4sxANjgMcQS25p`) was deliberately left untouched, and a separate inactive `FWAI-DEV — P02.02 Creative Director` was created.

## Successful actual Ollama manual executions

All nine accepted artifacts came from actual manual n8n executions using the existing local `qwen3.6:latest` model, not invented fixtures. Their exact candidate payloads and minimal workflow provenance are in `live-runs/`. Every accepted handoff has `status=candidate_requires_canonical_validation`, `dispatch_performed=false`, and `production_approved=false`, `spend_authorized=false`, `publish_authorized=false`.

| Milestone | Role | n8n workflow | Successful execution | Role-specific acceptance evidence |
| --- | --- | --- | --- | --- |
| P02.02 | Creative Director | `C3yCPFrUpzvb97lg` | **59** | Five numbered scenes, 360s total, 171/146/158/149/150 words of narration, fictional `AI_CONCEPT` disclosure, no approval. |
| P02.03 | Research Agent | `qx8tES2dRjMT9kJ9` | **57** | Zero verified claims without sources; unsupported physical-build/cooling claims left unverified. |
| P02.04 | Visual Director | `ltRaS3zusgzjeJAU` | **58** | Ten original planned shots, known scene references, no rendered-media claims. |
| P02.05 | Avatar Director | `Uj3C8kkSV3NMlbvs` | **60** | Four missing assets and three consent requirements identified; no likeness generation. |
| P02.06 | Budget Controller | `Cx2Gx2N3iEwWUURE` | **64** | Zero-cost synthetic forecast, two missing rate disclosures, `approval_required=true`; no authority to spend. |
| P02.07 | Editing Supervisor | `Mc7y7rXWx5PGF9Xe` | **62** | Edit guidance only, `manual_review_required=true`; no claim to have viewed media. |
| P02.08 | Quality Control | `xxpGERneD6wzi61c` | **63** | `overall_verdict=fail` without inspection data; technical audit cannot be faked. |
| P02.09 | Growth Strategist | `WdldwQYxMn4el9I0` | **65** | Zero fabricated performance patterns and five analytics data gaps. |
| P02.10 | SOP & Knowledge | `VPvcZLGOfblpGKCq` | **66** | One proposed documentation change, `owner_approval_required=true`; nothing applied. |

Existing P02.01 Executive Producer retains development acceptance and prior n8n success **54**.

## Failure injection and corrections

- First separate development Creative Director execution **56** produced too little narration for 72-second scenes. The model output was structurally valid but not editorially complete. A deterministic 120–160 spoken-words/minute requirement was added to both n8n validation and the Python role boundary. Retest **59** passed with 144–192 allowed words per 72s scene.
- Initial Budget Controller execution **61** was **rejected by the strengthened validator**: missing rate disclosures and an incorrect assertion that human budget approval was not required. Instructions were tightened without weakening the safety policy; retest **64** passed. No provider calls or budget changes occurred.
- Offline negative tests cover authorization-property injection, missing keys, changed frozen input, invented research/analytics, unapproved budget/SOP status, unsourced QC PASS, short narration, invalid manifest bytes, and canonical-envelope rejection.

## Repeatable WSL isolation and regression evidence

All tests ran on authorized WSL Ubuntu with working `/usr/bin/node`, Python 3.12 and Bubblewrap user/network namespace isolation. Read-only development source, cleared environment and private temporary storage excluded host credentials, production mounts, Docker sockets and service networks.

| Test group | Execution | Passed |
| --- | --- | ---: |
| Executive Producer | `sh agents/executive_producer/run-isolated-tests.sh` | 21 |
| P02.01 development-worker and n8n bridge | `sh worker/run-isolated-dev-tests.sh` | 23 |
| P01 canonical contracts | `sh agents/executive_producer/reconciliation/run-contract-regressions.sh` | 65 |
| Atomic claim concurrency | Existing recovery suite inside isolated Bubblewrap | 11 |
| All nine specialists, exact Node.js VM wrappers, real-result canonical validation | `sh agents/p02_roles/run-isolated-tests.sh` | 21 |
| **TOTAL** | Five isolated runs | **141; zero failures** |

The nine-specialist suite specifically replays source-controlled Code-node scripts under a networkless Node VM, and validates each actual Ollama candidate with the accepted P01.02 Python validator. It **does not substitute** for a permanent n8n-to-worker service.

## Saved designs and rollback

- `baseline-workflow-inventory.json`: nine-role discovery, original schema and synthetic fixtures.
- `prehardening-workflows.redacted.json`: eight original inactive drafts, without credentials.
- `posthardening-workflows.redacted.json`: nine final inactive definitions and connections, without credentials.
- `build_specialist_patches.py`: reproducible credential-free hardening operations for the eight existing development roles.
- `creative_director.inactive.sdk.js`: validated Workflow SDK source of the separately created Creative Director development workflow.
- `role_validation.py`: strict role policies and canonical blocked handoffs.
- `test_role_validation.py`, `check_wrapper.cjs`, `test_n8n_wrappers.py`, `test_live_results.py`, `run-isolated-tests.sh`: deterministic regressions.
- `live-runs/`: nine accepted model outputs and minimal provenance.

Do **not** re-import the credential-stripped snapshots as live deployments; the Ollama credential references remain in n8n. The eight preexisting development workflows stayed inactive and their orchestrator entry points were disabled and disconnected. The Creative Director development workflow is manual-only and inactive. No workflow has publishing, provider-submission, HTTP, tool or database write nodes.

## Scope boundaries

The P02 exit criterion is **ten locally modeled, individually tested planning roles with explicit no-spend/no-publish gates**, not production orchestrator activation. Outputs are **blocked candidates** pending independent canonical processing and human approvals. Real assets, real-source research, verified costs, approved likeness/voice use, production QC and actual YouTube Analytics were deliberately absent.

The eight prior drafts and new Creative Director provide planning output only; the P03 master orchestrator, authenticated permanent handoff, provider receipt reconciliation and production state progression remain gated future work. A local test does not establish provider exactly-once delivery. The `qwen3.6:latest` tag may change when the model updates; revalidate before a later promotion.

The working production webhook, active Creative Director, Python production worker, Dockerfile, Compose, accepted P01 contracts and locked checklist were not changed in this phase. Spending, publishing, likeness generation, production activation and merging are **not authorized** by this report.

**Next gate:** draft pull request, formal code/security review and owner acceptance of the development P02 exit criterion. Do not advance to P03 or merge without explicit authorization.

## Current installed Ollama model fingerprint

A read-only inspection of the Windows host's local Ollama `GET /api/tags` endpoint after the successful runs reported:

- Name: `qwen3.6:latest`
- Digest: `07d35212591fc27746f0a317c975a6d68754fb38e9053d82e25f06057af28522`

This is a **post-run installed-model fingerprint**, not an inference-time signed attestation. Keep it for later regression comparison; do not assume a mutable `latest` tag still identifies these model bytes after an update. No model was installed, updated or restarted during this inspection.

Formal PR #2 non-approving review: GitHub review ID `5913894431`. The draft remains unmerged and does not authorize P03 advancement.
