# P04 — Local AI Image Generation: Development Acceptance Evidence

**Date:** November 15, 2026 (New York time). **Scope:** development-only, frozen synthetic P01 concept. **Decision:** P04.01–P04.06 *implemented and demonstrated* in the isolated local setup; **locked phase exit remains OPEN** pending an actually approved manifest, secure n8n-to-image-batch credentials, validated consistency/quality, and formal merge approval. No production deployment, commercial model authorization, paid-provider calls or publishing.

## Hardware / engine / licensing

- PC: AMD Radeon RX 9070 XT, 16 GB VRAM, gfx1201, Windows-host ROCm 7.2, PyTorch 2.9.1+rocmsdk20260116, native GPU backend (not a CPU image fixture).
- ComfyUI 0.45.0, cloned official source SHA `e9afbccc2669677076feb08e52658f129cd8c12b`, isolated folder `C:\Users\yashi\Documents\futureworks-p04-comfyui`; virtual environment uses existing Windows ROCm PyTorch, no driver replacement. Offline and custom nodes disabled. Local API exposed on 127.0.0.1:8188 and reachable from n8n Docker via host.docker.internal.
- Baseline model Stable Diffusion 1.5 `v1-5-pruned-emaonly.safetensors`, from `stable-diffusion-v1-5/stable-diffusion-v1-5`; downloaded on authorized PC and independently SHA256-verified: `6ce0161689b3853acaa03779ec93eafe75a02f4ced659bee03f50797806fa2fa`. License label CreativeML OpenRAIL M; production/commercial-use restrictions still require owner/legal acceptance. Optional SDXL candidate's bytes and SHA were **not** validated; model selection for advanced photorealism/machinery remains provisional.
- Four source-controlled image workflows: `thumbnail`, `establishing`, `mechanical`, `texture`. Prompts explicitly label images fictional AI concept art; no factual mechanical engineering substantiation.

## Actual ten-image batch — P04.05/P04.06

- Run `P04_GPU_001`, frozen P01 project `FWAI-EP-0001`, five S01–S05 scenes and all ten distinct deterministic seeds.
- **Ten real GPU-generated ComfyUI PNGs** were received through the actual local `/prompt` → `/history` → `/view` APIs, checked for PNG structure/chunk CRC and planned dimensions, downloaded and SHA256-indexed in dedicated SQLite metadata. Each asset records complete prompt text, seed, model SHA, Comfy prompt UUID, license, scene ID, template and reference relationship.
- Windows output: `C:\Users\yashi\Documents\futureworks-p04-data\images` and SQLite `C:\Users\yashi\Documents\futureworks-p04-data\p04-dev.sqlite3`; binaries are **not** in the public GitHub repository. One real-image contact sheet `P04_GPU_001_CONTACT_SHEET.png` was created for *human* visual QA.
- Index: `VISUAL_DIRECTOR_HANDOFF_P04_GPU_001.json` — ten unique images, ten unique Comfy receipts, ten different PNG SHA256 digests and all five scene IDs. Source evidence `evidence/P04_GPU_001.json` lists the ten actual hashes and UUIDs.
- Actual local Ollama `qwen3.6:latest` Visual Director metadata-based model run produced exactly ten shots covering all ten image asset IDs. It failed once when too few references were used; strict schema and exact reference constraints were added, then re-run passed. The result was canonical P01.02 validated, **execution=blocked**, all authorization false, no spending. Saved locally as `VISUAL_DIRECTOR_PLAN_P04_GPU_001.json`; P04 provenance is an outer envelope so the canonical P01 result schema remains intact. The model **did not inspect image pixels** and cannot approve quality/rights without a separate review.
- The ten images vary in robot morphology and material composition; no claim of perfect character consistency, technical correctness, rights clearance or production readiness.

## n8n evidence, carefully separated

| Workflow | ID | Actual test | Interpretation |
| --- | --- | --- | --- |
| `FWAI-DEV — P04 ComfyUI GPU and Queue Probe` | `DAJg1GLB6xalPFVw` | **Execution 72 SUCCESS** | Real n8n HTTP GET → Windows ComfyUI `/system_stats` and `/queue`; AMD GPU and API verified. |
| `FWAI-DEV — P04 ComfyUI Async Adapter` | `7BXr7LTYCKQFLQHb` | **Executions 70/71 SUCCESS, PINNED** | Frozen input, dev async submission acknowledgement and monitoring logic validated with simulated HTTP responses only. Actual authenticated n8n POST → P04 batch API **not configured**; its auth header remains placeholder. |
| `FWAI-DEV — P04 Ten Real ComfyUI History Audits` | `eKgk6RwTsfZg7ulU` | **Execution 74 SUCCESS** | Real n8n HTTP GET → ten exact ComfyUI history UUIDs; each one returned `success`, `completed=true` and correctly named image output. Did NOT download/transfer PNG bytes via n8n; actual local Python pipeline did that automatically. |

All three development workflows remained inactive after manual test execution. No production workflows or paid external endpoints were modified or invoked.

## Engineering acceptance

- Reusable source: `engine.py`, `cli.py`, `api.py`, `visual_bridge.py`, `repack_visual.py`, `contact_sheet.py`, JSON model catalog and n8n SDK graphs. Sources contain no credentials.
- Atomic SQLite idempotency, immutable frozen manifest hash, fail-closed Comfy uncertainty, no blind retries, strict downloaded PNG integrity, tamper checks, canonical P01 Visual Director envelopes, and disabled spend/publish gates.
- P04 isolated offline tests: **36**, including fake transport/PNG fixtures *separately* identified from the ten real ComfyUI PNGs. n8n Code nodes tested inside a Node VM. Regression coverage for poisoned results, unauthorized input, duplicate jobs, missing references, malformed model output and asynchronous mock completion.
- **Full current-branch cross-phase re-run PASSED: 226 isolated tests**, zero failures: P01 six contracts 65 (4+10+12+7+15+17); P02 Executive Producer 21; P02 worker 23; P02 atomic concurrency 11; P02 nine-role 21; P03 orchestration 49; P04 image/Visual/n8n/API 36. Each suite was actually invoked on the authorized WSL worktree with read-only Bubblewrap isolation and cleared environment. P04's corrupted-PNG test additionally checks fail-closed `needs_review` and no duplicate submission.
- No unapproved external image APIs, real provider charges, production workflow activation, publishing, automatic asset licensing approvals or `main` merge.

## P04 checkpoint disposition

| Requirement | Development finding | Gate |
| --- | --- | --- |
| P04.01 compatible ComfyUI and AMD hardware acceleration | **VERIFIED** through actual local engine and GPU-generated PNGs | Development done |
| P04.02 select/license-check models for realism/machinery | **BASELINE VERIFIED** SD1.5 model hash and license metadata; SDXL and higher-fidelity model not benchmarked | Provisional model choice |
| P04.03 four reusable image templates | **VERIFIED** all four produced GPU images | Development done |
| P04.04 n8n API adapter and async monitoring | **IMPLEMENTED; PIN-TESTED**, real n8n read-only monitoring verified; authenticated n8n→batch-writer unconfigured | Integration remains open |
| P04.05 image provenance and indexed storage | **VERIFIED** from ten actual images | Development done |
| P04.06 ten downloaded and indexed images handed to Visual Director without manual transfers | **VERIFIED** through local pipeline, real Ollama metadata-only Visual Director and P01.02 validation; n8n read-back independently confirmed ten Comfy receipts | Human pixel/rights review pending |

**Locked P04 full exit:** an actually *approved* canonical manifest must drive the image batch, then images must be automatically visible to the subsequent video-generation service. The acceptance concept still has `approval_state.status=pending_review`, and there is no secure n8n write integration or production video-generation adapter. **Do not close that gate** on the strength of this development proof.

**Next:** formal dev PR review and separate owner authorization before any merge or activation. P05 not authorized.
