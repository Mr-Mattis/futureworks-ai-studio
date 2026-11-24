# Future Works AI Studio — EP001 Visual Production, Not More Prototype Checkpoints

**Active method:** owner-locked photoreal keyframes + actual craft reference + native Blender engineering motion + a single persistent Blender application for visual control. Source of truth is the existing `FWAI-M001-EP001` six-shot manifest. Current final 30-second film: **NOT produced**.

## Visual source hierarchy (non-negotiable)

1. **User-approved latest FWAI-M001 mech visual** at `Documents/futureworks-p04-comfyui/output/FWAI_M001_LOCKED_V2_CHARACTER_KEYFRAME_00002_.png`, SHA256 `5dcefd9309510754d7b5dd5dd549eae6f3244d1a4a3b6f9056c2055d620ba12b`. Its proportions, helmet, body, plum/cyan finish and 6′5″ identity must be visually preserved.
2. **Original Nissan photo references** from `FWAI-M001_EP001_PREPRODUCTION/02_CLEAN_CAR_REFERENCES`; exactly one pearl-white right-passenger-side 370Z NISMO. NISMO bumpers, factory wheels, trim, spoiler, side mirrors and door handle must remain identical.
3. **S01 source composite F**: `05_LOCAL_KEYFRAMES/S01/candidate_F_leg_grip_repair/FWAI_EP001_S01_MASKED_POSE_COMPOSITE_E.png`. This is AI-authored photoreal source imagery, **not** proof of a real captured photo. Do not mutate.
4. **S01 candidate G**: locally FLUX3-inpainted **1280×720** photo-wide workshop from original F **with 539,648 core source pixels preserved exactly**, 16px feather at edge. Fresh 7% camera margin gives bumpers and mech safer framing. Still **QA HOLD for viewer-left second mechanical hand not gripping film**. Not a finished video.
5. **Blender 3D geometry** is currently a cartoon-like **engineering blockout** used for kinematic/collision/film simulations ONLY, not acceptable as the finished cinematic pixels.

No image may be described as user-approved unless specifically confirmed.

## Production reference standards (actual sources)

The local reference bible `EP001_REAL_WORLD_REFERENCE_BIBLE.json` includes direct URLs to Nissan factory specifications, 3M/Avery wrap instructions, real car-door installation videos and Boston Dynamics physical robot manipulation. Source links are studied for motion, contact and materials; never reupload or reuse copyrighted footage without a license. The original user-provided installer photos are also creative references.

- **Hands and posture:** plant feet; shift pelvis/knees BEFORE extending hand; both index/thumb grips hold material corners, no hovering; full mass/balance continuity.
- **Vinyl:** only passenger door; attached border stays near the correct door plane, free film has plausible tension and physically coherent wrinkles. No fabric teleporting, no magically flat global area.
- **Tools:** forearm squeegee emerges after contact and presses film progressively center-to-edge. Enclosed electrical heat around recess with no flame. Trim along paint-safe knifeless tape; offcut remains present until removed.
- **Camera:** same indoor workshop, fixed source car and visual master, restrained photographed dolly/tracking. Lock scale and 7% subject safety frame. No garage morphs or bumper cuts.
- **Shots:** six × 5 sec = 30 sec 16:9, 24fps.

## Real production accomplishment: S01 G

Two local, zero-cost ComfyUI image-generation runs explored lens widening. The first reference-only attempt produced blurry border artifacts and was rejected. The second **masked outpainting** produced clean shop extensions; a pixel-locked compositing step preserved the original source center exactly. The third experimental local inpaint of the second hand did NOT convincingly solve two-sided contact and was rejected. Do NOT promote or publish that hand variant. This is controlled visual QA rather than accumulating random AI guesses.

Current source files and receipts remain local (not committed to Git):
`Documents/futureworks-ep001-production/reference/S01_WIDE_PHOTO_LOCKED_CORE_CANDIDATE_G.png`,
`S01_CANDIDATE_G_QA.json`,
`S01_CANDIDATE_G_PRODUCTION_FRAMING_QA.png`,
`EP001_DIRECTOR_REFERENCE_BOARD.html`.

## A single Blender GUI — verified, persistent

On El_Corredor, **the existing Blender 5.3 PID 9648**, opened to the VQ04.06 baked scene, was reused for all work. No new Blender GUI windows were launched. Its Scripting workspace has **large photoreal reference IMAGE_EDITOR** and smaller original 3D/cloth view. A local in-memory timer subscribes to `Documents/futureworks-ep001-production/live_bridge`; only exact allowlisted image names and frames 1/18/36/54/72 may be sent. Never arbitrary code, arbitrary file paths, paid calls, deletion or automatic scene save.

To switch the large reference photo while Blender runs, in **Windows PowerShell**:

```powershell
$py="$env:USERPROFILE\Documents\futureworks-p04-comfyui\.venv\Scripts\python.exe"
$send="$env:USERPROFILE\Documents\futureworks-ep001-production\scripts\send_ep001_live.py"
& $py $send --show G
& $py $send --show MECH
& $py $send --show CAR
& $py $send --show G
& $py $send --inspect
```

These commands were executed on the existing GUI and acknowledged `pid:9648,window_count:1,gui_visible:true,windows_created:0`. The PID is **session-specific**, so on a fresh launch reinitialize the Blender bridge inside **the new already-opened GUI instance**, do not open extra windows to run headless scripts.

For a new session, open Scripting workspace, select **Python Console**, and enter:

```python
exec(open(str(__import__('pathlib').Path.home()/'Documents'/'futureworks-ep001-production'/'scripts'/'activate_director_inplace.py'),encoding='utf-8').read())
exec(open(str(__import__('pathlib').Path.home()/'Documents'/'futureworks-ep001-production'/'scripts'/'enable_persistent_bridge.py'),encoding='utf-8').read())
```

Before reusing on any other computer, adapt source manifest paths and revalidate owner master SHA and the active GUI. **Do not run a second Blender executable in the workflow.**

## Quality gate for a real finished 30-second film

The S01 composition is materially improved but the two-hand grip has **not passed**. Blender's rig/cloth is physics-control reference, not photoreal final. The film requires physically credible work through S01–S06; the system must reject mismatched character/car/workshop frames. Cloud Runway image-to-video and external upload remain disabled by existing source authorization, and publication is disabled. A final user-ready cinematic **does not yet exist**. Proceed through visual corrections and usable footage; avoid opening a new PR for each tiny checkpoint.

## Source-control safety

Only engineering scripts, director bible build code and these instructions are committed. No source reference photos, keyframes, generated frames, owner assets, binaries, videos, Blender scenes or point caches enter the repository. No automatic cleaning/deleting user folders.

Live QA receipts live under `Documents/futureworks-ep001-production/evidence` and are not meaningful until verified against the currently running single Blender process.
