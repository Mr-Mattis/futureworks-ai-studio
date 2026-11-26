# Future Works AI Studio — VQ-04.05 Native Cloth Bake

**Development completed locally:** November 23, 2026, El_Corredor / Blender 5.3.
**Status:** VQ04.05 engineering POC **PASS**, cinematic physical realism **HOLD**.
**Branch:** `dev/vq04-05-cloth-bake` (isolated, stacked on VQ04.04).
**Scope:** Simulation infrastructure only; no paid Runway/HeyGen, no external media uploads, no n8n production changes, no user asset deletion, no publication.

## Why this checkpoint matters

VQ04.04 used 425-vertex *shape-key poses* and geometric contact approximations. That was NOT cloth physics. This checkpoint creates an independent development film mesh with a **genuine Blender Cloth modifier and 72-frame disk-backed physics cache**, running under gravity, stretch/shear/bending terms and moving boundary conditions. Tests reopen the saved Blender scene and compare 72 actual evaluated frames, so visual deformation cannot be mistaken for authored keys.

The approved FWAI-M001 V2 character master is still unchanged and SHA256 locked to:

`480263bdd7637bfb2d90cc2deecdeb616eef03492a35216dbebfd3b1f44c555c`.

The mech remains nominally **6′5″ (1.9558 m)**, and the stationary Nissan source scene was not modified.

## What was built

| Feature | Actual implementation | Limitation |
|---|---|---|
| Film | 425 vertices, 384 quads, approximately 1.2m × 0.4m | Still a coarse structural grid |
| Thickness | 0.25mm **render shell** added after cloth solve | Material bending model is not lab-calibrated automotive cast vinyl |
| Pin boundary | 153 vertices constrained near the flat passenger door | Adhesive strength, peel and transfer not modeled |
| Gripper boundary | 17 loose-edge vertices driven by a Hook before Cloth | Driver is **animated kinematic proxy**, NOT linked to robot hand/finger force |
| Simulation | Blender **CLOTH** modifier, gravity, mass/spring damping and native cloth point cache | Self-collision off; material parameters illustrative |
| Collider | Separate stationary duplicate door-plane box with Blender **COLLISION** modifier | Current 72-frame motion does **not** actually load collider to test impact/repulsion |
| Render | Normal Blender view + optional temporary post-cloth Catmull–Clark smoothing | Smoothing improves pixels, not physical calibration |
| Animation | 72 frames × 24fps = three seconds, two actual H.264 MP4s | Character/vehicle are still non-photoreal proxy assets |

**Modifier order** on the physical film is `HOOK → CLOTH → SOLIDIFY`, deliberately with **no shape keys**. Pinned adhesion boundary vertices and moving loose-edge control are kinematic constraints; the middle of the sheet is the true cloth-solver result.

The **temporary visual smoothing** changes view-only modifier ordering to `HOOK → CLOTH → SUBSURF → SOLIDIFY`. It is not written to the source `.blend` and does not rebake or alter the solver. Smoothing is also exposed via the new Blender sidebar.

## Verified numerical results (all 72 frames)

Read independent `VQ04_05_SIMULATION_DIAGNOSTIC.json` and `VQ04_05_FRAME_TRACE.json`. All were computed from the **reopened** baked `.blend` and Blender's evaluated mesh:

- `point_cache.is_baked = True` both before and after reopening the scene; 72 persistent disk cache frame files totaling ~500,237 bytes.
- The evaluated central cloth vertex had **72 distinct positions** across frames 1–72 (the shape was dynamically computed).
- Maximum constrained adhered-edge drift: **0.000125m (0.125mm)**.
- Maximum free-region mean displacement from reference rest: **0.154078m**.
- No solver-film surface vertices crossed the current **simplified planar door-front AABB** during the 72 tested frames; minimum surface gap **0.002209m (2.209mm)**.
- **Crucial boundary:** Since gap remained positive throughout, this does **not** validate collision response under loaded contact, no hand-to-film contact, and no adhesion peel/friction forces.

## Test and app verification

- Local native Blender viewer/security regression: **29 / 29 PASS**.
- Integrated source, cache, 72-frame geometry, video, immutability and visible GUI acceptance: **24 / 24 PASS**.
- Physical simulation file is independently reopened, and an actual visible Blender 5.3 process acknowledged live commands to inspect, switch to detail camera, smooth and scrub frames **1, 18, 36, 54, 72** with `gui_visible:true`.
- Two *actual 72-frame* H.264 3-second videos were rendered from Blender; frame files and SHA receipts live on El_Corredor.
- Final one-command `run_vq05_poc.ps1` returned exit code 0 and printed `FWAI_VQ04_05_CLOTH_TECHNICAL_PASS`.

No claims of studio-quality photorealism or production-approved simulated adhesive film were made.

## Watch inside Blender (user request)

On the authorized Windows machine **El_Corredor**, open the newest Blender window titled `FWAI_VQ04_05_CLOTH_BAKED`. Open manually if needed:

`%USERPROFILE%\Documents\futureworks-vq04-05\scene\FWAI_VQ04_05_CLOTH_BAKED.blend`

The sibling directory `blendcache_FWAI_VQ04_05_CLOTH_BAKED` contains the 72 baked cache files; keep it alongside the .blend. **Do not move only the .blend without its point cache.**

In Blender: press **N → Future Works → VQ04.05 — Baked Vinyl Physics**. Use `HOLD` (1), `REACH` (36), `LAY` (72), `Play / Pause`, `Detail Cam`, `Smooth View` or `Raw Grid`. These are actual interactive native controls with unsaved view changes. Live sync also permits the assistant to change frames and camera on El_Corredor while actively executing development, via an allowlisted local command file—not a live video stream in ChatGPT.

Optional manual PowerShell commands:

```powershell
$python = "$env:USERPROFILE\Documents\futureworks-p04-comfyui\.venv\Scripts\python.exe"
$send = "$env:USERPROFILE\Documents\futureworks-vq04-05\send_live_cloth.py"
& $python $send --detail
& $python $send --smooth
& $python $send --frame 1
& $python $send --frame 36
& $python $send --frame 72
& $python $send --inspect
```

The sender waits for a real GUI acknowledgement; `gui_visible:true` and `status:ok` indicate that the actual visible Blender app processed a command. The add-on listens only to a local JSON file in `Documents\futureworks-vq04-05\live_bridge`; no network socket or arbitrary Python.

## Local review and reproduction

Open:

`%USERPROFILE%\Documents\futureworks-vq04-05\evidence\VQ04_05_REVIEW.html`

The dashboard contains both actual three-second videos, three smoothed stills, 24-test acceptance, 29-test UI evidence, detailed full-frame simulation traces, bake manifest and live GUI receipt.

To reproduce the engineering acceptance and inspect the visible GUI:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Documents\futureworks-vq04-05\run_vq05_poc.ps1"
```

If the Blender add-on was not installed or Blender was reinstalled, run `install_vq05.ps1` and then open a **new** Blender window. The one-command runner never silently overwrites a baked scene if its SHA differs: it fails closed.

## File safety / source control

The repository commits **code and documentation only** under `quality/vq04_05/`.

The original approved V2 PNG, baseline scene `.blend`, binary baked `.blend`, physical cache directory, 72 frame PNGs, rendered MP4s, personal dashboard and JSON evidence receipts remain **local on El_Corredor**. No cloud upload, paid provider, production automation changes, or clean-up deletions. Blender creates its own `.blend1` backup, which is preserved for manual review rather than auto-deleted.

## VQ04.06 acceptance backlog

1. **Physical collision under load:** run an A/B collider stress rig and verify actual contact impulse/deflection, not just absence of penetration.
2. **Hand-to-film coupling:** bind the moving gripper boundary to robot rig fingertips using measured constraints, grip continuity across all 72 frames, and continuous full hand/collision checks.
3. **Material calibration:** tune real cast/wrap-vinyl stiffness, elastic recovery and deformation against user-supplied vinyl application footage; eliminate implausible collapse/wrinkles at the pin boundary.
4. **True adhesion/peel mechanics:** progressive staged adhered vertex constraints calibrated to car-panel curvature; no force claims until data exists.
5. **Geometry and visual QA:** faithful approved FWAI-M001 V2 3D production topology, real Nissan 370Z body mesh plus separate modular widebody, consistent workshop background and photoreal reflections. Only then consider paid Runway review with fresh explicit authorization.

**Production cinematic quality remains HOLD.** Technical proof proves that Blender's cloth solver is truly working and repeatably testable, not that we have a lifelike commercial film yet.
