# P04.06 — FWAI-T001 Local Material Look-Development Acceptance

**Scope authorized by owner (2026-11-18):** Material rendering for the already-approved `FWAI-T001` machine using the local GPU only. **No environments, paid API calls, external uploads, publishing or production activation.** Technology geometry and conceptual mechanics were previously approved; actual physics/manufacturability remain unverified.

## What was rendered

- Exact owner-approved mechanical specification SHA256: `07dc8ea721e2d2d69d47585bc67268c31a2ceb9d96e0724a5ffc55fd17465c5f`.
- Exact owner-approved geometry specification SHA256: `7bc0379c02632018e78dfbea6eab467071ec0ffe9f97b3c9522c1634bf51b77e`.
- Deterministically reconstructed the six-sided lattice, six mechanical manipulators, six radiator anchors, central 2 m service hatch and protected cable paths in an isolated neutral virtual product view.
- Generated two source color/material designs: **graphite alloy** and **ceramic titanium**.
- Passed each source through **native AMD Radeon RX 9070 XT / Windows ComfyUI Realistic Vision V6.0 low-denoise image-to-image**; then neural **RealESRGAN x4** image-space super-resolution, 1920×1080. Pinned model, VAE and upscaler SHA256 verified locally.
- Created separately hashed **transparent foreground cutouts** from deterministic source silhouette masks (projected over the refined material assets) for eventual independent scene composition; these masks are approximations and still require precise edge inspection.
- Two independent ComfyUI task UUIDs and on-disk SHA256 render proofs persisted under `P04_06_MATERIAL_AB_VERIFIED_ASSETS.json`. No image files, external signed URLs or credentials committed to Git.

## Human review files

On El_Corredor:

`C:\Users\yashi\Documents\futureworks-p04-data\p04-06-material-lookdev\P04_06_MATERIAL_REVIEW.html`

Full 1080p generated images:
- `FWAI-T001_MATERIAL_graphite_alloy_1920x1080.png`
- `FWAI-T001_MATERIAL_ceramic_titanium_1920x1080.png`

Transparent cutouts:
- `FWAI-T001_MATERIAL_graphite_alloy_CUTOUT_1920x1080.png`
- `FWAI-T001_MATERIAL_ceramic_titanium_CUTOUT_1920x1080.png`

Side-by-side uncropped full-subject comparison: `FWAI-T001_MATERIAL_AB_CONTACT_SHEET.png`.

## Quality assessment

**Technical acceptance: PASS.** Two real local GPU material renders completed and each SHA256, model hash, prompt receipt and dimensions were verified. Independent cutouts exist. No environment scene was generated.

**Real-life-like quality acceptance: HOLD.** Inspection of the images shows consistent mechanical rings and credible metallic color separation, but the surfaces and lighting still read somewhat like a clean digital product illustration. The orthographic two-dimensional view alone does not establish believable mass, perspective, physical load paths, volume or depth. Upscaling from 896×512 does not create true optical detail. Neither rendering is automatically approved as final artwork.

Next quality improvement, after owner review: establish **3D depth and camera-accurate material shading** based on the approved geometry, e.g. a parametric 3D model and physically based rendering (PBR). This is a recommendation, **not** authorization to alter machine geometry, create environmental scenes, upload media or publish.

## Source-control acceptance

- All original geometry, mechanics, source images and three approved P05 Runway clips remain unchanged.
- All artifact references are immutable SHA256-bound and have source paths on the owner's PC.
- New material code includes robust no-resubmit recovery guard, hashes, restricted ComfyUI loopback URL, and zero cloud provider calls.
- A local offline acceptance HTML collects Approve / Revise / Hold for **each** material style. No automated approval or publication.
- No further image generation is authorized from this acceptance record; it is a report of work performed under the owner grant.

**Formal P04/P05 exit:** OPEN. Stage 03 environment: BLOCKED. External uploads/publishing: BLOCKED.
