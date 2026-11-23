# Future Works AI Studio — VQ-04.03 Mechanical Hands, Tool and Contact Reach POC

**Execution:** 2026-11-23 on El_Corredor. **Engineering proof:** PASS. **Creative/cinematic approval:** HOLD.

## Scope and source of truth

The authoritative character is the exact locked image `FWAI-M001_APPROVED_FINAL_MASTER_V2.0.png` and its V2 JSON specification under `%USERPROFILE%\Documents\futureworks-p04-data\character-library\FWAI-M001\v2.0`. SHA256: `480263bdd7637bfb2d90cc2deecdeb616eef03492a35216dbebfd3b1f44c555c`.

Preserve the immutable character design, **6 ft 5 in / 1.9558m**, obsidian-plum armor, cyan visor/actuators, and integrated sealed forearm tool housing. The older Nissan and the vinyl remain **development proxies**, not certified physical geometry, and the original vehicle shot remains unchanged. The widebody is future work.

VQ-04.03 is a distinct, **local and reversible** derivative project. Work was done in an isolated WSL Git worktree stacked on approved VQ04 development. This code does **not** call paid Runway, n8n production, external media APIs, publish, enable auto-deletion, or silently save any .blend.

## What was actually built

- **Two mechanically articulated five-digit hand assemblies** (one per existing mech hand anchor). Each digit has three nested independently controllable hinge pivots and matching visible phalanx segments: **30 pivot controls + 30 segment meshes** in total.
- Every finger has a visible servo, titanium/graphite housing and small rubber-like fingertip pad. The preview follows the existing VQ03 arm/hand rig via parent links, not an AI-inferred texture.
- Three keyed stages: frame **1 OPEN**, frame **36 REACH**, frame **72 PINCH / tool deployed**. The joint rotation angles and integrated squeegee cartridge slider move in Blender when the timeline advances.
- A left-forearm **flush tool docking preview** with a linear squeegee cartridge, blade-shaped rubber tip and cyan indicator. The torch and trimming knife **are not deployed or modeled**; nothing external dangles from the mech.
- An explicit **kinematic right-index fingertip reach solver at frame 36**. It adjusts the existing right-hand IK goal in memory only until a single fingertip center reaches within **3mm** of a selected vinyl vertex's 13mm front-side offset. It records/restores the original target on clear. This is **not actual fingertip/film collision validation**, not a two-sided pinch, and not pressure/friction/adhesive or cloth physics.
- Probes demonstrated the **unadjusted** target center gap was about **0.1115m at frame 36**. The actual live Blender GUI acknowledged the corrected gap as **0.001276m**; we explicitly do not claim that the other fingers or whole hand have no film penetration. Frame 1 and 72 remain reach/clearance HOLD.

## Technical acceptance, independently executed

| Test family | Result |
|---|---:|
| Finger kinematics, 3 poses, tool slider, original scene SHA, reversible preview | **23/23 PASS** |
| Reach solver, <3mm target gap, native timeline invalidation and rollback | **16/16 PASS** |
| Local safe GUI bridge, unsafe command rejection, duplicate sequence protection | **14/14 PASS** |
| Native Blender sidebar buttons (load, pose, calibrate, reset, clear) | **9/9 PASS** |
| Previously implemented 1.9558m reversible helmet height check across frames 1, 36 and 72 | **11/11 PASS** |
| **Combined local checks** | **73/73 PASS** |
| Actual visible Blender GUI reads | **PASS** |
| Film clamping under load / pressure/friction / actual collision / cloth simulation | **NOT TESTED / HOLD** |
| Production-grade FWAI-M001 V2 visual fidelity, Nissan exact geometry, final cinema | **HOLD** |

The frame-36 numerical contact target is a *single-center kinematic constraint*, not proof of mechanical grasp. The film is still a shape-key-defined surface, not a baked physically verified adhesive film.

## Watch the development in Blender

On El_Corredor, use the **newest** Blender 5.3 window named:

`FWAI_VQ04_03_HAND_CONTACT_V3`

Open `%USERPROFILE%\Documents\futureworks-vq04-03\scene\FWAI_VQ04_03_HAND_CONTACT_V3.blend` if the window is closed. Press **N → Future Works → Live Sync**. Blender's Outliner should show **FWAI LIVE PREVIEW / VQ04.03 HANDS AND TOOLS**, in addition to the earlier lower-body and V2-identity study collections.

A true local GUI process acknowledged all three hand stages, 30 finger controls/segments, and the 1.276mm frame36 reach target. This is not a video stream inside ChatGPT; it's the actual visible Blender scene reacting to allowlisted commands.

### Repeat specific live operations (PowerShell)

```powershell
$py = "$env:USERPROFILE\Documents\futureworks-p04-comfyui\.venv\Scripts\python.exe"
$cli = "$env:USERPROFILE\Documents\futureworks-vq04-03\send_live_command.py"
& $py $cli --load-hand
& $py $cli --inspect-hand
& $py $cli --hand-stage 1
& $py $cli --hand-stage 36
& $py $cli --calibrate-contact
& $py $cli --inspect-contact
& $py $cli --clear-contact
& $py $cli --hand-stage 72
& $py $cli --clear-hand
```

A safe one-command acceptance script re-runs all technical checks and drives the actual GUI (if the live window is running) without overwriting the source:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Documents\futureworks-vq04-03\run_vq04_03.ps1"
```

If Blender 5.3 gets reinstalled or the addon needs updating, run `install_vq04_03.ps1`, then open a new Blender instance. **Do not close a Blender window with unsaved user work to force a plugin reload.** The local command queue is isolated at `Documents\futureworks-vq04-03\live_bridge_v3`, separate from earlier VQ04 windows.

## Human review

Open `%USERPROFILE%\Documents\futureworks-vq04-03\evidence\VQ04_03_REVIEW.html`. It contains actual close-up Blender frames 1,36,72 and original/full shot, locked V2 character reference and evidence.

Machine-readable proof files:
- `VQ04_03_ENGINEERING_TESTS.json`
- `VQ04_03_CONTACT_TEST.json`
- `VQ04_03_BRIDGE_TESTS.json`
- `VQ04_03_VISIBLE_GUI_ACK.json`
- `VQ04_03_COMBINED_ACCEPTANCE.json`
- `VQ04_03_CLOSEUP_MANIFEST.json`

All PNGs, .blend, original images, receipts, footage and model binaries remain **outside Git**. The PR commits only scripts and docs.

## Next focused work — VQ04.04

The current hand fingers bend and one center point can be placed near the film, but the grip cannot hold/transfer load or prevent interpenetration. Next gates are (1) explicit fingertip/film proximity + intersection detection at 1/36/72, (2) two-sided constrained pinch with force/pressure proxy and contact continuity, (3) collision-compliant film deformation and adhesion contact, (4) accurate Nissan door CAD-like surface following the approved Nissan photo, before (5) ComfyUI/Runway cinematic QA. Do **not** call this photoreal production-ready without further modeling and owner visual approval.
