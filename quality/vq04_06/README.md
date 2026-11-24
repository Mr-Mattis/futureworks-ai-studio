# Future Works AI Studio — VQ-04.06 Mech-Coupled Cloth / EP001 Autonomous Local Producer

**Execution:** November 23, 2026, El_Corredor / Blender 5.3.
**Development result:** VQ04.06 mechanical rig-to-film coupling **PASS**; full EP001 cinematic delivery **NOT COMPLETE**.
**Branch:** `dev/vq04-06-controlled-production`, stacked on VQ04.05 draft PR #32.
**Protection:** no paid Runway calls, third-party uploads, production n8n changes, publishing, deletion of old work, or overwriting approved files.

## Locked creative destination

This project continues **FWAI-M001-EP001 — “Precision in Motion — Passenger-Side Vinyl Wrap,”** not a new speculative concept:

- **30 seconds, 16:9, 24 fps = 720 frames**, exactly six five-second stages.
- **Latest owner-approved mech identity:** `FWAI_M001_LOCKED_V2_CHARACTER_KEYFRAME_00002_.png`, SHA-256 `5dcefd9309510754d7b5dd5dd549eae6f3244d1a4a3b6f9056c2055d620ba12b`. This **supersedes** the older 2D V2 character board (supplementary only). Geometry is a proxy, not yet a perfect 3D match.
- **Car:** pearl-white Nissan 370Z NISMO, **RIGHT PASSENGER DOOR**, exact same car in every shot, original front/rear, wheels, NISMO red accents, unchanged geometry. Any cyberpunk/widebody revision is a separate later branch.
- **Wrap:** charcoal satin, one continuous physical sheet covering only the passenger door; no wheel, hood, front/rear fender or roof wrapping.
- **Environment:** one consistent indoor vinyl/wrap workshop (A/B style), not garage doors that appear randomly or inconsistent camera plates.
- **Mech:** 6′5″, realistic knee/hip bend and planted feet, fingers actually contacting the film, integrated forearm squeegee, enclosed electric heat-forming tool (no open flame), paint-safe trim and final hands-off reveal.
- Shot actions: **S01 establish → S02 lay film → S03 squeegee → S04 heat-form → S05 trim → S06 final reveal.**

Source production contract and film QA gate on El_Corredor: `Documents\futureworks-p04-data\FWAI-M001_EP001_PREPRODUCTION\03_RUNWAY_PROMPTS\PRODUCTION_MANIFEST.json`, `04_APPROVAL_GATES\QA_CHECKLIST.md`, and the 2026-11-22 S01 owner revision directives.

## What actually changed in VQ04.06

VQ04.05's 72-frame film **moved under a separately animated Hook**. In this checkpoint the Hook driver is **parented directly to the true Blender rigged R-index fingertip mesh**, so the film's gripped upper-left corner follows actual robot hand motion. We fitted an **independent right-hand IK proxy** at frame 1 to align the pad in front of the loose film corner, with about **14.2mm center-to-corner separation** reflecting the modeled fingerpad radius and gap.

The IK proxy follows the original animated R-hand IK object through a parent transform; original animation keys are unchanged. The film control has **no independent location animation**. The whole sheet uses 425 mesh vertices, native Blender **CLOTH**, 72 disk-baked physical frames, with 17 loose-edge vertices Hook-driven and **170 right-door-edge pinned vertices**. The mesh is dark charcoal satin in a newly created study material, matching visual intent much better than the original blue film, though not lab-calibrated.

**A genuine problem was found and remediated:** the first coupling bake exhibited **2 film vertices crossing the simplistic door-front plane** on 6 of 72 frames, concentrated at the i=15 boundary just before the pinned region. In VQ04.06 V2 we extended the constrained region by one column (from i>=16 to i>=15), **rebaked the derivative into a new file**, and independently verified **0 door-front intrusions across all 72 frames**. No older scene or bake was overwritten.

### Verified numerical outcomes

- **72/72 baked and independently loaded frames**, and 72 distinct central cloth vertex positions.
- Index pad remains at ~14.2–14.25mm center-to-film corner, with **max offset change 0.003222m (3.222mm)** throughout 72 frames. These are geometry-based proximity metrics, **not pinch-force proof**.
- Planar passenger door collision-proxy check: **zero** film vertices penetrating the front plane across all frames.
- Old approved source `.blend`, latest owner mech image SHA and historical V2 design board preserved.
- Local **24/24 engineering acceptance checks PASS** and **29/29 native Blender sidebar/bridge security tests PASS**.
- A **three-second, 72-frame, 24fps H.264 film** was rendered locally from actual Blender evaluated cloth plus temporary, post-physics smoothing. It is a real local motion proof but still looks like coarse CGI.
- Live Blender 5.3 GUI confirmed commands to inspect the baked scene and change frames and camera via our local file bridge with `gui_visible:true`. No live video stream into ChatGPT.

### What this does NOT prove

- The thumb is not yet providing an independently measured two-sided gripping force and its contact pressure/friction are not validated.
- Animated Hook parenting is a **kinematic boundary condition**, not gripping via a realistic contact or friction solver.
- The small 425-vertex simulated sheet and current block-shaped door are not production-accurate Nissan CAD or real cast-wrap vinyl.
- Full mech and car photoreal quality, true door handles/edges, squeegee/heat/trim mechanics and real adhesion/peel stress simulation still require additional work.
- The final 30-second motion-picture **does not exist yet**, and is not being falsely claimed as complete.

## Watch the actual interactive Blender proof

On El_Corredor open the newest Blender 5.3 window titled:

`FWAI_VQ04_06_COUPLED_CLOTH_BAKED_V2`

If needed open this existing derivative file manually:

`%USERPROFILE%\Documents\futureworks-vq04-06\scene\FWAI_VQ04_06_COUPLED_CLOTH_BAKED_V2.blend`

**Keep the sibling `blendcache_FWAI_VQ04_06_COUPLED_CLOTH_BAKED_V2` directory with the file.** Blender's cached physics will be missing if only the `.blend` is copied.

Press **N → Future Works → VQ04.06**. Use Detail Cam, Smooth View, frames 1/36/72 or Play/Pause. All view changes are unsaved and reversible.

Local command sender (PowerShell):

```powershell
$py = "$env:USERPROFILE\Documents\futureworks-p04-comfyui\.venv\Scripts\python.exe"
$sender = "$env:USERPROFILE\Documents\futureworks-vq04-06\send_live_coupled.py"
& $py $sender --detail
& $py $sender --smooth
& $py $sender --frame 36
& $py $sender --inspect
```

## Production dashboard, explicit autonomy

Open `%USERPROFILE%\Documents\futureworks-vq04-06\evidence\VQ04_06_REVIEW.html`. It includes the 3-second H.264 motion proof, three actual Blender stills, and the *best unapproved photographic S01 candidate F* as a visual target, plus all acceptance artifacts.

The **local production preflight** in `producer_preflight.py` reads the exact production manifest and latest owner-master source SHA. It emits a deterministic six-shot task/authorization ledger:

`evidence\FWAI_EP001_AUTONOMOUS_PRODUCTION_GATES.json`.

**At this checkpoint, every final shot remains blocked for cinematic release:** S01 still fails the two-hand grip and 5–8% safe framing gate, and S02–S06 lack owner-approved keyframes and finished motion clips. Local development and draft renders are authorized; paid Runway uploads/API, n8n production workflow changes and publishing remain OFF.

Use one PowerShell command to reproduce and check all local acceptance:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Documents\futureworks-vq04-06\run_vq06.ps1"
```

## Local evidence / provenance (not committed to Git)

- `VQ04_06_COUPLED_BAKE_MANIFEST_V2.json` — exact derivative source file and baked cache.
- `VQ04_06_COUPLING_DIAGNOSTICS.json` — all-frame summary including 0 door penetration.
- `VQ04_06_FRAME_TRACE.json` — all 72 frame measurements.
- `VQ04_06_ACCEPTANCE.json` — 24/24 integration QA.
- `VQ04_06_UI_TESTS.json` — 29/29 native UI/unsafe-command QA.
- `VQ04_06_COUPLED_RENDER.json` — three source-hashed stills and render-only smoothing.
- `VQ04_06_MECH_COUPLED_CLOTH_3SEC.mp4` — genuine local 3-second motion (24 FPS).
- `FWAI_EP001_AUTONOMOUS_PRODUCTION_GATES.json` — full six-shot production status and release authorization boundaries.
- `live_bridge\ack.json` — actual GUI command receipt.

**Git records scripts and documentation, not private source images, local render outputs, binary baked .blend or cashable point caches.** Neither old files nor unused workflows are deleted by scripts.

## Next autonomous critical path (without accumulating endless exploratory prototypes)

1. **Resolve S01 photograph** with a reference-locked workshop plate, physical two-hand film contact, knee/hip posing and full-car margins. Owner-approved photo reference is already available; DO NOT replace character identity.
2. **Elevate geometry assets:** acquire/license or build 370Z NISMO accurate door body + handle mesh; reproduce the exact current photographed car. Keep widebody/cyberpunk as separate revision.
3. **Complete contact & adhesion:** separate thumb pressure, film-to-hand kinematic coupling, collision stress under load, squeegee adhesion front; calibrated material and tool deployment/retreat.
4. **Build all six production-accepted keyframes** with locked character/car/workshop; preserve unchanged pixels and crop accepted wide view wherever possible.
5. **Motion and offline edit:** preview local where feasible; Runway Gen-4.5 image-to-video and external asset upload only after owner explicitly approves use of credits, uploads, and spending cap. Six 5-second shots, 24 FPS timeline, consistent color/foley and 1080p target export.
6. **Final human gate** only for creative approval and publishing, not for ordinary local engineering checkpoints.

**The user is authorizing autonomous *local development* through further checkpoints, not automatic paid charges or publication.** Follow fail-closed production safeguards.
