# Future Works AI Studio — VQ-04.01 Live Geometry Preview

**Owner mandate:** Continue development after merged PRs #26/#27; maintain FWAI-M001's fixed **6 ft 5 in (1.9558 m)** and protect its approved V2 visual design. The user wants to **watch actual changes live in Blender** (not only read generated screenshots). Do not spend on paid providers, publish, or delete assets.

**Disposition:** VQ-04.01 technical proof **PASS**. Overall mech/Nissan/vinyl cinematic quality remains **HOLD**.

## Verified real implementation (El_Corredor, November 23, 2026)

The VQ03 bridge could only change pose, timeline and IK targets in a visible GUI. VQ04 adds the ability to **generate new mesh geometry as a data-only asset and insert it into the already running Blender GUI without reopening a project or executing arbitrary Python supplied by a command**.

- Imported 70 new mechanical details around both legs (hydraulic-style pistons, thigh/shin rails, segmented knee/ankle pivot rings, foot braces and treads) attached to existing left/right thigh, shin, and foot bones.
- The parts were generated from a **strictly validated**, SHA256-pinned 19,849-byte JSON payload, with hardcoded allowlisted asset ID, palette, bone names, and object counts.
- Existing FWAI-M001 approved V2 reference PNG is read-only verified by SHA256 `480263bdd7637bfb2d90cc2deecdeb616eef03492a35216dbebfd3b1f44c555c`; the VQ03 .blend and VQ04 .blend are not overwritten by preview injection.
- Blender background test: **21/21** passes, including SHA mismatch rejection, unknown asset rejection, unknown parent bone, nonfinite geometry, rig hierarchy, visible mesh movement across frame poses, duplicate-reload prevention, reversible removal, source preservation and preview render generation.
- Actual Blender GUI acknowledged `load_preview`, `inspect_preview`, `clear_preview`, repeated load, and pose changes, with `gui_visible=true`; the readback reported **70** parts in the in-memory collection.
- No Runway calls, publication, external media uploads, n8n production changes, or automatic deletion. VQ03 reference, Nissan and overall movie scene are still illustrative **proxies**, not production-accurate CAD or certified physics.

## Watch it live in Blender

Use the **FWAI_VQ04_LIVE_SCENE** Blender window on El_Corredor, not the older VQ03 window.

1. Open `%USERPROFILE%\Documents\futureworks-vq04\scene\FWAI_VQ04_LIVE_SCENE.blend` in Blender 5.3.
2. In the 3D viewport press **N** → **Future Works** → **Future Works — Live Sync**.
3. Leave the VQ04 window open. When ChatGPT issues the local command, the newly generated preview appears in Blender *in place*, while the GUI remains usable. In the Outliner, look for `FWAI LIVE PREVIEW / VQ04 LOWER BODY` (70 editable objects bound to the existing rig).
4. Moving the timeline to frame 1, 36, or 72 changes rig posture. Preview parts move with their parented bones.
5. Scene updates are **unsaved**, so you can safely discard them by closing without saving, or issue the precise clear command.

Optional local PowerShell commands:

```powershell
$python = "$env:USERPROFILE\Documents\futureworks-p04-comfyui\.venv\Scripts\python.exe"
$sender = "$env:USERPROFILE\Documents\futureworks-vq04\send_live_command.py"
& $python $sender --inspect-preview
& $python $sender --clear-preview
& $python $sender --load-preview
& $python $sender --pose 36
```

All sender commands expect a visible GUI acknowledgement; `status:ok` and `gui_visible:true` are proof that an actual Blender window processed the request, not a screen recording. The add-on polls a **local file** twice per second, **not a network port**. The VQ04 protocol has its own isolated queue at `Documents\futureworks-vq04\live_bridge`; the previous VQ03 live window may coexist without conflicting.

### Reproducible one-command proof

Run in Windows PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Documents\futureworks-vq04\run_vq04_poc.ps1"
```

The launcher regenerates the data-only payload, verifies it via a **background Blender copy** of the unchanged VQ03 scene, then posts a safe command to the visible VQ04 Blender window and checks its reply. It explicitly verifies original and derivative blend file hashes do not change. It does **not** save into the user's active Blender project.

Install the reviewed add-on, if Blender 5.3 is reinstalled:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Documents\futureworks-vq04\install_vq04.ps1"
```

The installer copies the source reviewed add-on and geometry helper into Blender's user add-on directory, enables it in Blender preferences, and prints results. **Open a new Blender window** to load the updated plugin code; don't kill windows with unsaved changes.

## Source and evidence

Source (Git): `quality/vq04/` in isolated `dev/vq04-live-geometry` worktree. Remote local evidence remains out of Git:

- `Documents\futureworks-vq04\evidence\VQ04_REVIEW.html` — side-by-side generated Blender renders and acceptance results.
- `Documents\futureworks-vq04\evidence\VQ04_LOWER_BODY_LIVE_PREVIEW.png` — 1280×720 frame 36 rendered after mesh injection.
- `Documents\futureworks-vq04\evidence\VQ04_ENGINEERING_TESTS.json` — the 21 test results.
- `Documents\futureworks-vq04\evidence\VQ04_VISIBLE_GUI_ACK.json` — real GUI readback.
- `Documents\futureworks-vq04\evidence\VQ04_LOCAL_PROOF_SUMMARY.json` — canonical and derivative SHA256 values.
- `Documents\futureworks-vq04\staging\FWAI_M001_LOWER_BODY_DETAIL_V1.json` — data-only 70-part preview manifest.

## Security and implementation boundaries

The JSON importer refuses unknown asset IDs, paths, code, unexpected fields, unapproved bone attachments, NaN/Inf, excessive coordinates, excessive file size, and invalid hash. It allocates a preview collection, stages objects before replacing any earlier preview, and removes **only its own preview collection** on request. It is deliberately limited to cylinders made from mesh data. No automatic filesystem cleanup and no `.blend` autosave is performed by the bridge.

**Not yet solved:** the actual V2 character's photorealistic body geometry and hand rig; an accurate Nissan 370Z mesh and a modular widebody kit; true film/adhesive tension and collision simulation; reliable rendered-material pass. Current preview parts are engineering primitives (visual plausibility improves slightly, but they are NOT approved as a canonical representation). The live bridge does not stream full remote video into ChatGPT, and background modeling renders do not automatically appear until a safe preview command is sent.

**Next creative checkpoint:** VQ-04.02 — improve faithful physical model reconstruction against approved FWAI-M001 V2 orthographic and detail references, starting with legs/hip and arm tool geometry, while keeping preview import safety and 6'5" height.
