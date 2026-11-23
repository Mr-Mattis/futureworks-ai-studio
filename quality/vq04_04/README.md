# Future Works AI Studio — VQ-04.04 Narrow Film Geometry + Contact Diagnostics

**Date:** 2026-11-23. **Device:** El_Corredor. **Scope:** reversible Blender proof. **Creative/cinematic acceptance: HOLD.** No production changes, paid Runway calls, external media uploads or asset deletion.

## Source-of-truth lock

- Approved character: `FWAI-M001_APPROVED_FINAL_MASTER_V2.0.png`, immutable SHA256 `480263bdd7637bfb2d90cc2deecdeb616eef03492a35216dbebfd3b1f44c555c`.
- Fixed character height: **6 ft 5 in = 1.9558m**; source Nissan/door remain unchanged.
- The original 3mm-thick, door-wide visual proxy vinyl is *not* overwritten or deleted. It is temporarily hidden while the new replacement material is previewed; its initial visibility is restored when clearing the preview. The current Nissan vehicle is an intentionally simplified **proxy**, not geometrically correct 370Z CAD.

## What VQ-04.04 actually implemented

1. **Independent partial film.** Native Blender 25x17 grid (425 vertices, 384 quads) and 0.25mm solidify thickness, cobalt-blue PBR-inspired material. Three authored shape-key stages at timeline frames **1 HOLD**, **36 REACH**, **72 PARTIAL APPLY**. The film's right portion is restrained close to the proxy passenger-door surface; the left edge remains free for the mech to hold. User requirement of NOT covering the entire door is enforced.
2. **Stationary door and penetration proxy.** Door front is the flat physical proxy plane at Y=-0.379m. For each stage, validate film vertices over door X/Z bounds are at least 1.1mm **toward the camera** from this plane. **0 of 425 vertices penetrate the front-plane test across all 3 frames.** Approximate projected coverage-upper-bound fractions: **27.84% / 28.35% / 29.06%** (stages 1/36/72). These are estimates using the projected overlap bounding box, *not measured real adhesive coverage*.
3. **BVH fingertip collision tests.** Use Blender's evaluated triangular surface + nearest-surface BVH to test **all ten modeled fingertip spheres** at all three stages for sphere-vs-film overlap. The 1/36/72 preview states initially have no detected fingertip-sphere overlap. This tests only fingertip sphere approximations, not full hand/interpenetration or midframe continuity.
4. **Two-sided geometric pinch stage at frame36.** A separate temporary right-hand IK goal moves the real R-index pad to the front of the loose film corner (final target error **1.768mm**). The R-thumb root changes position within a bounded **82mm** adjustment until its pad reaches the opposite side of the film (target error approximately **1 micron**). BVH clearances relative to the sheet are **1.633mm index** and **0.863mm thumb**, with no modeled finger sphere penetration. This is a geometry alignment *only* — no Newton-force result, pressure, friction, tensile strength, two-sided force clamp or adhesive load validated.
5. **Render-time pose persistence fix.** VQ04.03 directly moved an existing animated IK target; Blender reset that value when rendering and the pinch was visibly lost. VQ04.04 instead temporarily rebinds the R-hand IK constraint to its own **unkeyed proxy target**, preserving the correct geometric pose during render evaluations. When the preview is cleared, the original IK constraint target is restored and the temporary object is deleted. The original animated IK object, its keyframes and source .blend are never modified.
6. **Real native Blender UI.** Future Works > Live Sync contains Load Narrow Film, HOLD / REACH / LAY, Stage 2-Sided Grip, Door Collision Check, Reset Pinch, Remove Narrow Film. Live command bridge accepts the same narrowly allowlisted actions. No arbitrary Python, internet service, filesystem deletion or automatic save.

## Actual local acceptance (all completed)

| Test family | Pass |
|---|---:|
| Narrow-film geometry, source visibility restoration, sample frame coverage and door-front clearance | **37 / 37** |
| Finger/film BVH diagnostics, opposing sides, safe IK proxy, rollback and preservation | **21 / 21** |
| Native Blender UI operators and malicious-command rejection | **18 / 18** |
| VQ04.03 hand/finger regression | **23 / 23** |
| VQ04.02 fixed 1.9558m helmet-fin height regression | **11 / 11** |
| **Combined** | **110 / 110** |

A separate **actual running Blender GUI** on El_Corredor acknowledged staged assets and every requested pose, door-front diagnostic, fingertip BVH diagnostic, two-sided frame36 calibration and index target gap readback. Importantly, the actual Blender render proof shows **both pre-render and post-render two-sided geometry staging TRUE**, showing the temporary IK constraint fix survives a full render without writing source files.

All 110 structural tests concern deterministic proxy geometry and software integrity, **not** photorealism. The full forearm/hand mesh, door trim, adhesive model and cloth dynamics remain unvalidated.

## Inspect the work in Blender

Use the newest Blender 5.3 window on El_Corredor titled **FWAI_VQ04_04_CONTACT_V2**. Open `%USERPROFILE%\Documents\futureworks-vq04-04\scene\FWAI_VQ04_04_CONTACT_V2.blend` in a new window if needed. Press **N → Future Works → Live Sync** in the viewport. Both earlier VQ04.01/VQ04.02 collections and the articulated hand preview can be loaded, along with the new narrow material preview collection **FWAI LIVE PREVIEW / VQ04.04 FILM CONTACT**.

**To replay live through PowerShell** (allowed local operations, no network):

```powershell
$py = "$env:USERPROFILE\Documents\futureworks-p04-comfyui\.venv\Scripts\python.exe"
$cli = "$env:USERPROFILE\Documents\futureworks-vq04-04\send_live_command.py"
& $py $cli --load-hand
& $py $cli --load-film
& $py $cli --film-stage 1
& $py $cli --film-stage 36
& $py $cli --calibrate-two-sided
& $py $cli --inspect-two-sided
& $py $cli --film-door-diagnostic 36
& $py $cli --film-finger-diagnostic 36
& $py $cli --clear-two-sided
& $py $cli --film-stage 72
& $py $cli --clear-film
```

**Reproduce all local acceptance checks** from Windows PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Documents\futureworks-vq04-04\run_vq04_04.ps1"
```

If the add-on is missing from the sidebar, run `install_vq04_04.ps1`, reopen the VQ04.04 scene in a **new** Blender window (do not kill windows with unsaved work), and repeat the run. The VQ04.04 command file lives only under `Documents\futureworks-vq04-04\live_bridge_v2`; earlier versions use distinct queues.

## Local review / evidence (outside Git)

Open `%USERPROFILE%\Documents\futureworks-vq04-04\evidence\VQ04_04_REVIEW.html`.

- `VQ04_04_PARTIAL_SHEET_HOLD.png`, `VQ04_04_PARTIAL_SHEET_REACH.png`, `VQ04_04_PARTIAL_SHEET_PARTIAL_APPLY.png`: real Blender scene renders.
- `VQ04_04_GRIP_DETAIL.png`: 1280x720 Blender orthographic close-up.
- `VQ04_04_FILM_TESTS.json`: clearance and coverage figures, source SHA, 37 tests.
- `VQ04_04_FINGER_DIAGNOSTICS.json`: ten fingertip BVH probes across 3 stages, 21 tests.
- `VQ04_04_UI_SECURITY_TESTS.json`: 18 Blender operator/security tests.
- `VQ04_04_RENDER_MANIFEST.json`: image hashes, actual pre/post render geometric-contact proof.
- `VQ04_04_LIVE_GUI_ACK.json`: visible Blender live readback.
- `VQ04_04_COMBINED_ACCEPTANCE.json`: complete 110-test technical disposition.

Git commits only the source `quality/vq04_04/`, not private original footage, canonical images, binary scenes, proof renders, test receipts, credentials or model weights.

## Remaining VQ-04.05 and onward quality gates

- Implement and bake an actual physical thin-film simulation using an appropriate Blender cloth/bending/adhesive model, with constraints calibrated against user-provided reference photos (and validate scale, tension, wrinkles, contact over every animation frame).
- Model the Nissan 370Z with production-accurate passenger door body and collision shell (the current proxy is inaccurate). Preserve its stationary body and existing approved photographic look. Widebody kit as a modular **later** variant.
- Replace rough faceted robot geometry with detailed V2 design-faithful topology and a high-quality skeletal/collision rig. The actual hand currently remains visually simplified.
- Implement full hand, tool and film **continuous** intersection testing (not just fingertip spheres or frames 1/36/72), plus two-sided physical clamping forces and grip under tension. Only then enable photorealistic motion/post-processing and carefully controlled optional Runway review. No paid Runway calls without separate user approval.
