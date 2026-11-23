# Future Works AI Studio — VQ-03 engineering proof (2026-11-23)

**Branch:** `dev/vq03-metric-rig-vinyl` (isolated). No paid provider, production workflow changes, public uploads, source reference replacement, publishing or file deletion.

## Owner requirements

- Recurring mech FWAI-M001 must be exactly **6 ft 5 in (77 inches / 1.9558 m)**. Blender uses real metric units; a fixed height witness and mesh crest are aligned at that limit.
- Preserve character visual identity against the **approved V2 canonical image** (SHA-256 `480263bdd7637bfb2d90cc2deecdeb616eef03492a35216dbebfd3b1f44c555c`); it is an image reference, **not yet a matching production 3D mesh**.
- Nissan photo appearance is approved as a baseline; a **widebody redesign is postponed** until mechanics and vinyl pass creative review.
- Blender UI must be inspectable on El_Corredor. Native Rigify and Node Wrangler and the locally developed **Future Works** sidebar add-on are installed/enabled. The real `.blend` project was launched visibly. Press **N → Future Works** in 3D viewport and choose poses A/B/C to watch the timeline. Select rig to see edit controls. It is a working Blender project, not a static screenshot.

## What we implemented and tested

| Checkpoint | Development evidence | Formal creative exit |
|---|---|---|
| VQ-03.01 6ft5in mech | Native editable armature, visible parented meshes, 4 IK targets/constraints and three keyed pose states; true 1.9558m reference height | **HOLD**: design not yet a faithful 3D reconstruction of the V2 approved reference |
| VQ-03.02 Nissan scene | Dimensional 4.25m approximate vehicle and passenger door collision geometry, fixed camera and workshop | **HOLD**: it is a simple proxy, not approved photographic Nissan body or CAD geometry |
| VQ-03.03 vinyl mechanics | Independent 435-vertex flexible film, 3mm solidify thickness, anchored section, shape-key deformation phases, Blender cloth/collision modifier scaffold | **HOLD**: cloth simulation not baked, adhesive contact and finger grips not physically validated |
| VQ-03.04 motion | **72 real Blender frames** at 24fps, 3-second H.264 MP4; crouch lowers pelvis while IK foot target positions remain constant | **HOLD**: foot ground collisions and realistic full-body movement not yet proven |
| VQ-03.05 ComfyUI | Real local SD1.5 GPU img2img on frame B, preserved all source pixels strictly outside the edit mask (1024×576 working image), image receipts and before/after montage | **HOLD**: local enhancements do not yield photoreal final footage |

We validated **21/21 Blender scene checks** and **17/17 integrated Python checks**. This confirms the technical pipeline and provenance, not production realism. An actual 3-second playback file exists, and Blender GUI launched with the scene opened.

## Local assets and usage

Location on the authorized workstation: `%USERPROFILE%\Documents\futureworks-vq03\proof-v5`.

- `FWAI_VQ03_MECH_NISSAN_VINYL.blend` — interactive Blender source, frame 36 camera view on opening.
- `VQ03_A_HOLD.png`, `VQ03_B_CROUCH.png`, `VQ03_C_CONTACT.png` — real Blender still frames.
- `VQ03_three_pose_3sec.mp4` — 72-frame, 24fps, three-second local blocking animation.
- `VQ03_B_LOCAL_COMFY_PREVIEW.png`, `VQ03_COMFY_BEFORE_AFTER.png` — actual ComfyUI photoreal enhancement stage.
- `VQ03_PROOF_MANIFEST.json`, `VQ03_ACCEPTANCE.json`, `VQ03_COMFY_RECEIPT.json`, `VQ03_COMBINED_TEST_RESULTS.json` — machine-readable evidence.
- `VQ03_REVIEW.html` — local interactive review dashboard with images and video.

Run the end-to-end technical proof on the authorized workstation (from Windows PowerShell):

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Documents\futureworks-vq03\run_vq03_poc.ps1"
```

The launcher uses the existing source/proof assets and refuses ambiguous Comfy GPU states; it does not resubmit completed work. It calls Blender's verification, local ComfyUI, WSL FFmpeg only if video is absent, and Python tests. Blender, the current local ComfyUI stack, and WSL Ubuntu need to be installed and available. If reproducing elsewhere, first place the source files in the documented local development directory and adjust hardware paths. This is a development harness, not a production-ready portable installer.

## Blender add-ons and viewer

- Audited: Blender 5.3.0, built-in cloth, collision, IK armatures, Cycles, Eevee, FBX/glTF export. All core requirements were available.
- Installed/enabled: **Rigify**, **Node Wrangler**, and the custom **FWAI VQ03** Sidebar UI. No third-party unknown add-ons were downloaded, and no unapproved external API usage was required.
- Blender UI now exposes pose navigation, rig selection, timeline playback and a direct link to local review assets under **Future Works**.
- Current scene contains approved mech and Nissan source images as **immutable referenced external images**, not as new canonical render or geometry. A change to the canonical 2D character appearance requires separate owner authorization.

## Guardrails and next actual creative steps

1. Build a faithful, topology-clean 3D mesh from the approved V2 character design with real working hand/finger joints. Revalidate height including fins.
2. Obtain or model 370Z-shaped body geometry and align camera/collision to the existing approved photo; only then design a separate modular widebody body-kit variation.
3. Calibrate independent vinyl film grip hooks, collision and physically plausible wrinkles; bake a cloth simulation and verify contact/no penetration over time.
4. Compare poses frame-by-frame, reject foot sliding, mesh intersections and identity drift; then rerender with high quality PBR materials/lighting.
5. Re-validate ComfyUI local enhancement as a strictly masked surface-only pass. No paid Runway clips or production/publishing until human approval.

**There are still substantive creative HOLD conditions.** Technical proofs should not be conflated with an accepted photorealistic production animation.
