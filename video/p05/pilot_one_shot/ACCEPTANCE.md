# Future Works AI Studio — P05 real Runway pilot technical acceptance

**Evidence date:** 2026-11-16 (America/New_York).
**Scope:** Owner granted rights for the original three selected P04 references and explicitly authorized an aggregate **$5 maximum** Runway trial comprising **three 5-second Gen-4.5 clips**. No publishing, production activation, retry or further expenditure approved. All work isolated to local owner PC and authorized paid Runway account; no production n8n changes.

## Results: real provider, not FFmpeg previews

- Successful authenticated read-only organization GET before running: 1000 credits.
- Three authenticated Runway `POST /v1/image_to_video` requests were submitted **once each** (no automatic retries) using exactly three original `P04_GPU_001` PNG reference bytes, selected and SHA-verified against the canonical Visual Director handoff.
- Gen-4.5, duration 5s each, ratio 1280:720, version 2024-11-06, positive prompts emphasizing realistic hardware materials, visible mechanisms, camera motion and distinct S01/S02/S03 staging. Local encoded image data passed directly through promptImage; no public static asset hosting or exposed media URLs.
- Three unique real Runway task receipts successfully reached `SUCCEEDED`, with status polling handling `RUNNING` and `THROTTLED` without blindly submitting again.
- Output downloaded from authenticated task receipts through the existing P05 restricted HTTPS/host/redirect policy; each real MP4 SHA256 verified and inspected using ffprobe: 1280x720, approximately 5 seconds, unique file bytes.
- Read-only Runway balance after all three creations: **820 credits**. Decrease **180 credits ($1.80)** — strictly within authorized 500-credit ($5) ceiling. No other paid operations, no retries.
- Each MP4 saved exclusively outside Git: `C:\Users\yashi\Documents\futureworks-p05-data\real-runway-pilot-001\S0x_<runway-task-uuid>.mp4`; redacted hashes, receipts, dimensions, cost ledger in `video/p05/evidence/P04_P05_REAL_PILOT_REDACTED_EVIDENCE.json`.
- Owner-friendly 3×3 review montage: `C:\Users\yashi\Documents\futureworks-p05-data\real-runway-pilot-001\RUNWAY_P05_THREE_CLIP_REVIEW_CONTACT_SHEET.png`. Each source MP4 should be played in full for human temporal consistency, flicker and artifact review; still frames are insufficient.
- This `pilot_one_shot` code is a reproducible **owner-specific development test harness**, not an activated P05 production workflow. Generated credentials, HMAC secrets, private rights approval records, short-lived Runway output URLs and media files are excluded from Git.

## Owner approval and manifest provenance

1. Frozen original P01 example manifest remained `pending_review`, unmodified and hash-indexed.
2. A local operator-created scoped HMAC attestation records the **real owner statements** approving creative manifest, rights to original images, exactly three asset uploads and $5 max generation. It binds the original manifest and each SHA256 source. The HMAC is a machine integrity attestation, **not an assertion the human independently possessed or signed with a cryptographic key**.
3. The first local approved-manifest derivative omitted some P01 schema fields and **failed P01 schema validation**. It was retained as audit history and was *not* silently fixed in place.
4. A second immutable derivative `approved-manifest-derivative-v2.json` and separately signed lineage record `signed-scope-authorization-v2.json` were created locally; this **passed the real P01 manifest validator** and exact SHA/HMAC independent verification. Neither derivative overwrote the source fixture. Only the owner-scoped pilot is authorized, not public production.
5. The legacy locked `imaging/p04/approval_gate.py` still binds only the pending source manifest and therefore **does not independently accept the new derivative**. Adapt verifier/schema and add positive/negative tests before claiming full P04 exit gate.
6. P04's inactive, managed-credential n8n image batch writer and authenticated automatic handoff are still untested end-to-end; existing negative rejection tests do not count as a successful live test.

## Human QA / outstanding closeout

- **P05 real generation requirement: PASS** (three actual provider-rendered clips, validated receipts, saved immutable media).
- **P05 expenditure guard: PASS**, 180 of 500 maximum credits consumed.
- **P05 human continuity requirement: HOLD** until owner reviews actual 3 clips and approves/rejects.
- **P04 native+AI-upscaled images: PENDING OWNER QUALITY REVIEW**. V3 RealESRGAN images look clearer but the owner now requests material/photographic realism: real tire tread geometry, panel fasteners/joins, hydraulic/servo internals, brushed/weathered metal and authentic manufacturing. New model A/B proof should use licensed photoreal-specific checkpoint (e.g., Realistic Vision) and independent third-party model SHA; do not silently replace the approved original pilot images.
- **P04 n8n authorized handoff: HOLD**, engineer-owned; build isolated managed credential and demonstrate one genuinely authenticated batch/handoff.
- **P04/P05 formal CLOSED: NO** until all locked acceptance gates and human review pass. Publication and production activation remain blocked.

## Source-control / tests

- All three Runway video outputs are real, not mock. `pilot_one_shot` scripts are deliberately fixed to these three authorized SHA hashes, five-second duration and $5 cap; no duplicate paid retries.
- Fresh P01–P05 Bubblewrap **268/268 regression suite passed** on the real-pilot worktree, followed by **5/5 isolated pilot-specific contract tests** (273/273 total), zero failures. Original first sandbox attempt omitted HOME and failed before test execution; setting HOME=/tmp inside the networkless sandbox resolved the harness issue without changing application code. Local log `/tmp/fwai-real-pilot-all-regressions.log`. Rerun after any acceptance-gate/production adapter changes.
- PR review is separate from paid-media acceptance; do not interpret a merge as publishing or production approval.
