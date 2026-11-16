# P04 Remediation + P05.01–P05.07 — Controlled Development Evidence

**As of November 15, 2026 — development implementation substantially delivered; both locked phase exits remain OPEN.**

This document is not human approval to use real likeness, incur charges,
publish, or activate existing production workflows.

## Branch, scope and protections

- Branch `dev/p04-remediation-p05-video`, rooted in merged PR #9
  (`a37d4dad6df632714f13dfa2ab506cac7aceecc3`).
- Isolated local WSL worktree:
  `~/futureworks-studio/futureworks-p05-video`.
- Existing production worker, Docker Compose, P01 canonical schema,
  P02 ten roles, P03 orchestration, and active n8n production workflows:
  **NOT MODIFIED**.
- No Runway generation API requests, provider API keys, charges or publishing.
- All new development n8n workflows are **inactive**; their Runway
  provider-capable node is explicitly disabled, disconnected, and has no
  Authorization credential, so manual execution cannot spend credits.

## P04 acceptance remediation

The **literal P04 exit requirement** remains: *an approved manifest
automatically produces consistent reference images available to
video-generation workflows*.

Implemented a separate `imaging/p04/approval_gate.py` which requires:

1. A separately human-approved, immutable canonical manifest.
2. An independent strong-key HMAC signature from a real owner reviewer;
   signer identities and keys are NOT bundled in the repository.
3. Specific independent rights, image-quality and character-consistency
   approvals; all ten exact source image SHA256 values and run identity.
4. No authority to spend, publish or activate production even when review
   evidence verifies.

The actual P01 frozen development manifest still says
`approval_state.status=pending_review`. The verifier explicitly refuses it,
even when a synthetic test signature is mathematically correct. **No
approval was fabricated**.

A new, separate, inactive n8n development workflow,
`FWAI-DEV — P04 Signed Review and Managed Credential Gate`
(`XhXS6pgYziLrSIgy`), stores a template for an
`httpTemplatedCustomAuth` credential, with no literal token in source.
Its batch writer is **disabled and disconnected**, and no real credential
has been provisioned. Execution **76** deliberately returned an error
because manifest, rights and QA approvals had not been received. This is
the correct negative acceptance outcome. The original P04 write-adapter
remains inactive; no authenticated live n8n→image writer test is claimed.

## P05 checkpoint evidence

| Checkpoint | Implementation and evidence | True locked status |
| --- | --- | --- |
| P05.01 Runway developer account, credentials and spending controls | Zero-spend default, no provider key or secret in source, `pricing-snapshot.json` with current official unit-rate evidence; NO account/credential provisioning or paid budget authorized. | **Blocked: actual developer account, credentials and budget still needed** |
| P05.02 Text/image-to-video adapters | Pure `RunwayWire` request builder for current `POST /v1/text_to_video` and `POST /v1/image_to_video`, requires real uploaded image URI and API version `2024-11-06`. Parsing uses real-format task UUID/statuses, but there is deliberately no network-capable paid submit path. | **Offline contract implemented; live API untested** |
| P05.03 Three reusable channel templates | `AI_CONCEPT`, `REAL_BUILD`, `HYBRID` templates plus fixed three scene prompts and references. | **Offline implemented/tested** |
| P05.04 Polling/throttling/timeouts/retries | Durable SQLite task identities, mock `PENDING/THROTTLED/RUNNING/SUCCEEDED/FAILED/CANCELLED` handling, due timestamps, exponential-ish bounded backoff and 10-poll review quarantine. Reopen receipt after restart; no duplicate mock submissions. | **Mock-tested; real 429/network behavior pending** |
| P05.05 Preserve expiring media | HTTPS output host allowlist, redirect suppression, 64MB cap, temporary atomic file, ffprobe validation, SHA256 index, no overwrites; injected-transport tests only. Current provider output URLs expire within 24–48h. | **Offline download logic tested; no actual Runway output URL downloaded** |
| P05.06 Continuity and correction requests | Human-blocked `continuity_review`, plus actual FFmpeg 3-point RGB frame sampling of three real local storyboards and cut-distance reporting. Original-shape/motion visual QA remains human dependent. | **Local QC triage run; real generative clip review pending** |
| P05.07 Three-scene cinematic acceptance | Three genuine, reproducible H.264 **Ken-Burns camera-motion storyboards** built locally from prior P04 real AI stills. Four seconds/scene, 24 fps, 960×540, outside Git. This is **NOT** generative text-to-video or image-to-video; no Runway output or approved budget. | **Locked three-generated-clip exit NOT met** |

### Real no-cost preview evidence (not provider generation)

Output retained only on owner's PC:

`C:\Users\yashi\Documents\futureworks-p05-data\storyboard-previews`

Three independently FFprobe-validated actual H.264 preview MP4s were created
from P04 images S01, S02, S03. `PREVIEW_EVIDENCE.json` stores source
image hashes, output video hashes, codecs, frame counts and file names.
`CONTINUITY_REVIEW.json` records representative RGB frame samples, intercut
differences and human-review requirements. Source-controlled copies of
only these metadata documents are in `video/p05/evidence/`. **No video or
source image bytes were uploaded to Git.**

### Actual n8n evidence

- `FWAI-DEV — P05 Cinematic Video Zero-Budget Orchestrator`
  workflow `IAkOGqIN72HnqBWe`; manual execution **75 SUCCESS**.
- Three scene intents validated; no real provider submissions, no video
  generations, no actual spending, and all production/spend/publish authority
  flags false. Exit accurately reported `OPEN`.
- The Runway HTTP Request node exists only as a **disabled and disconnected
  development sketch**, without an authentication header, and therefore
  cannot make accidental chargeable calls.
- P04 review workflow execution **76 ERROR (EXPECTED)** after detecting the
  not-approved manifest. Zero batch submissions resulted.

### Official external contracts

Runway reference pages verified on November 15, 2026:

- `https://docs.dev.runwayml.com/api/`: video endpoints, HTTP Bearer
  authentication, version header `2024-11-06`, GET task receipt.
- `https://docs.dev.runwayml.com/assets/outputs/`: expiring output
  URLs, generally 24–48 hours, must be archived promptly.
- `https://docs.dev.runwayml.com/guides/pricing/`: Gen-4.5
  **12 credits/second** and **$0.01/credit** baseline. Three 5-second clips
  would have an estimated **180 credits / $1.80** generation cost excluding
  taxes and other potential fees; estimate is **not an authorized budget**.
  Actual spend cap stays **zero**.

## Security and regression evidence

- Original merged P01–P04 suite: **226** passing isolated tests.
- P04 additional approval tests: **7** Bubblewrap-isolated tests passing.
- P05 video contract, download, async mock, and exact n8n Code-node tests:
  **31** Bubblewrap-isolated tests passing.
- **Total verified across P01–P05: 264 isolated passing tests; zero failures.**
  The initial aggregate test command had a path-binding typo for the
  11-test atomic suite; all other cross-phase suites passed, and the
  atomic suite was rerun separately in the same strict Bubblewrap
  read-only environment (11/11 passed). No unsandboxed fallback was used.

## Exit and next gate

**P04 remediation development delivered; phase exit OPEN:**
actual owner-signed approved image/rights/consistency review, managed n8n
credential provisioning, authenticated live submission, and delivery to
the next service under that approval still must be demonstrated.

**P05.01–P05.07 development scaffolding and no-cost simulation implemented; full
P05 exit OPEN:** no Runway developer credential or approved spend,
no real Runway generated clips or permanent provider receipts, and no
three-scene provider clip review. The three local FFmpeg preview MP4s are
not a substitute for this requirement.

**PR review and merge are separate authorization gates**. Do not merge,
activate, provision paid credentials, generate paid clips, or advance P06
without explicit owner instruction.
