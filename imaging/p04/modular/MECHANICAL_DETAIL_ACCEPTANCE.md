# P04.06 — Mechanical Detail Specification: Owner Review Gate

**Current checkpoint:** conceptual mechanical-detail architecture for **FWAI-T001 Civilian Orbital Lattice Weaver** only.

## Verified approval provenance

The exact owner-approved geometry specification remains unchanged and is bound to SHA256:
`7bc0379c02632018e78dfbea6eab467071ec0ffe9f97b3c9522c1634bf51b77e`.

The owner explicitly approved **technology geometry only**. Their limits remain binding: `MATERIAL_RENDER=NOT_AUTHORIZED`, `ENVIRONMENT_RENDER=NOT_AUTHORIZED`, `PUBLISH=NOT_AUTHORIZED`. No extrapolation of render authority is permitted. This step does not run ComfyUI, upload assets or invoke a paid API.

## Completed mechanical-design proposal

- Six uniquely anchored fabrication arms, tied to ring anchors R1–R6, with exact joint coordinates preserved from the approved owner geometry. Each has **two dimensioned linkage spans** computed from those coordinates (in the orthographic plane).
- For each arm: conceptual replaceable shoulder motor, elbow-bearing cartridge, shielded power-service loops and interchangeable precision fabrication end-effector. Load path explicitly traces tool → distal segment → elbow → proximal segment → shoulder → truss.
- Human maintenance access retains the approved **2-meter airlock** in the central hub. Power isolation and lockout are required before a cartridge exchange.
- Explicit interfaces for six subsystem categories: **structure, actuation, power, telemetry, thermal and service**. Six thermal radiator connection points are interface reservations only; actual heat rejection remains uncalculated.
- Mechanical detail source and receipt use immutable SHA256 hashes; prior geometry remains untouched.
- **Scope of verification:** diagrammatic component connectivity, line lengths, interfaces and owner policy. No 3D swept-volume collisions, orbital dynamics, stress/strain analysis, thrust/thermal balance, material properties, or manufacturability verification. The resulting fictional mechanism is NOT certified as buildable.
- The owner requested **real-life-like physical technology**, not merely a "photorealistic" aesthetic. No material rendering may begin without a separate explicit grant. Detail specification serves as a structural/functional target for later geometry-conditioned image rendering.

## Exact local files

Owner review dashboard:
`C:\Users\yashi\Documents\futureworks-p04-data\p04-06-modular-preview\P04_06_MECHANICAL_DETAIL_REVIEW.html`

Machine-readable contract:
`C:\Users\yashi\Documents\futureworks-p04-data\p04-06-modular-preview\FWAI-T001_mechanical_detail.json`

Acceptance receipt:
`C:\Users\yashi\Documents\futureworks-p04-data\p04-06-modular-preview\FWAI-T001_mechanical_detail_receipt.json`

Review uses **Approve / Revise / Hold**, and yields a single human-copyable SHA-bound message. The owner has **not yet approved this mechanical detail**.

## Test acceptance

Fifteen new unit/security tests exercise owner hash binding, six connected arm assemblies, altered joint positions or link lengths, cable protection, power isolation, serviceability, scale, missing subsystem interfaces, and disallowed material/environment/render, external upload, paid work or certification claims. They run inside the same Bubblewrap isolated test runner as the earlier 14 geometry tests. All 29 P04.06 tests passed in isolation.

Prior cross-phase suite: 303 inherited tests, 14 geometry tests, and now 15 new mechanical tests. Full cross-phase regression acceptance is recorded only once the current source-control branch run completes successfully; a local test pass alone does not assert live n8n or paid-provider acceptance.

## What remains on HOLD

Human mechanical-design acceptance, geometry-conditioned real-life-like materials, independent environments, compositing, cinematography production integration, promotion into P05, publication and P04/P05 formal phase closure.

**Next authorized step:** owner reviews the mechanical proposal. The assistant may fix tests and documentation while leaving all rendering and environment operations blocked.
