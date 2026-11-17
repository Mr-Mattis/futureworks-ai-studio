# Future Works AI Studio — P04/P05 Sequential Acceptance Update
**Date:** 2026-11-17 • **Branch:** dev/p04-ten-design-batch • **Scope:** isolated development; no production activation, external uploads or new paid calls.

## Gate 4 — P05 cinematography vocabulary → isolated n8n agent handoff: PASS

- Actual 90-term MOV/ANG/FRM/OPT source installed in `video/p05/catalog`, SHA256 `9629346c7633b37f09c6bba740600f6486e73e553f59001adcb39c34da2c6bbc`.
- Authenticated read-only local adapter `video/p05/camera_preview_server.py` runs on WSL port 18742.
- New inactive manual n8n workflow `SzxdcflH3cH6j29i`: authenticated GET (uses existing protected Custom Auth credential) → deterministic three-scene code validation. **Execution #79 PASS** with 3 canonical S01/S02/S03 scene plans, exact original P04 image hashes, validated camera codes, 5-second duration, `paid_provider_calls=0`, `production_activated=false`, `publication_authorized=false`.
- The original Visual Director, P05 production adapter and active Creative Director workflows were not altered. **Full live Visual Director/Cinematographer runtime routing is still OPEN**; staging integration alone does not satisfy production routing.

## Gate 5 — authenticated local P04 10-image batch writer: technical acceptance PASSED, creative gate FAILED

- ComfyUI on Windows remains loopback-only `127.0.0.1:8188`; local Radeon 9070 XT used for 10 actual images.
- New inactive manual n8n workflow `uioiNtH6e3ArHNoz` authenticates to the dedicated WSL protected local-only writer on port 18743 using n8n-managed Custom Auth.
- Real n8n execution **#80** initiated the worker, but its HTTP acknowledgement failed with 503 due PowerShell process-launch wait/timeout. **The worker nonetheless started and recorded durable receipt before work.** The Windows render log and Comfy UUID receipts prove actual progress. The launcher code was changed to a detached ack for future runs. NEVER blindly retry unknown jobs.
- Manual execution **#81 PASS**: authenticated idempotent replay recognized the existing batch and did not start a second generation.
- Ten real local Comfy GPU outputs `FUT_01...FUT_10_1920x1080.png`, using pinned Realistic Vision V6 + independent VAE + RealESRGAN x4, were generated. All ten have validated SHA256, PNG dimensions and actual task UUIDs; source evidence `imaging/p04/evidence/P04_V5_VERIFIED_ASSETS.json`. Human review dashboard `C:\Users\yashi\Documents\futureworks-p04-data\collection-v5-ai-civilization\P04_V5_OFFLINE_VISUAL_APPROVAL.html`.
- New inactive n8n manual audit workflow `ZsiQELAmJi03WfMl` execution **#82 PASS**: read all 10 SHA256-verified local completion receipts, no provider spend, publication disabled, and explicitly returned `semantic_visual_quality=REJECTED_PENDING_NEW_DESIGN`.
- **Critical quality finding:** V5 architecture is insufficiently prompt-faithful. The 10 images are photographically sharp but depict ordinary portrait subjects, fish, corridors or architecture instead of the specified machines. Detailed failures stored in `imaging/p04/evidence/P04_V5_SEMANTIC_QA_FAIL.json`. **0/10 V5 images are approved for production or external upload.** This is an important success of the quality gate, not a creative acceptance pass.

## Gate 6 — Future human+AI engineering image direction: V6 pilot complete, owner review pending

- Two new actual LOCAL Radeon/ComfyGPU experiments in `C:\Users\yashi\Documents\futureworks-p04-data\collection-v6-concept-first`.
- **V6 01** orbital lattice weaver and **V6 02** cooperative civic swarm infrastructure depot.
- Corrected architecture: first establish speculative geometry using original SD1.5, then apply low-denoise photorealistic img2img via Realistic Vision, then RealESRGAN x4 to **1920 × 1080**. The current V6 montage shows coherent engineered lattice and eco-civic structures, a significant conceptual improvement over V5, but not yet explicit recognizable working machinery and scale cues. **Do not render ten further samples until owner reviews the two representative V6 candidates.**
- Owner file `V6_CONCEPT_FIRST_AB_CONTACT_SHEET.png` shows side-by-side concept vs photoreal output. Actual individual 1080p photos `V6_01_1920x1080.png`, `V6_02_1920x1080.png`. These are still AI fictional designs, not documentary evidence of existing technology.
- No new Runway upload, no charged API call, no production activation. The original signed three-asset Runway pilot and its owner-approved clips remain unchanged.

## Regression / source control

- Inherited offline P01–P05 268 tests, existing scoped P04 6 tests, P05 real pilot 5 tests, n8n reference gateway 5 tests, camera vocabulary 10 tests, new P04 local ten-image writer 6 tests: **300 isolated checks total** in complete source-control verification run, zero failures if latest log validates this result.
- Draft PR includes source adapters, evidence metadata and rejection record. **Do not merge automatically.** Keep source PNGs and all API/HMAC/Custom Auth secrets outside Git.

## Locked phase exit status

P04 technical generation and authenticated local batch write: **PASS** (ten genuine images and n8n receipt). P04 creative semantic-quality acceptance: **FAIL/HOLD**. New approved immutable 10-asset manifest, full production P04-to-P05 automatic eligible handoff and production runtime wiring: **HOLD**.

P05 real Gen-4.5 pilot: **PASS** for genuine three 5-second clips, owner continuity signoff, verified $1.80 spend; production integration remains **HOLD**. **No publication or production workflow activation authorized.**

Next owner decision: review V6 01/02 full-resolution images and choose `V6-01=APPROVE|REVISE|HOLD; V6-02=APPROVE|REVISE|HOLD`, with detail-oriented notes on advanced morphology, materials, scale and plausible function. No additional paid permission required.
