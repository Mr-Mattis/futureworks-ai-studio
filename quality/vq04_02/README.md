# Future Works AI Studio — VQ04.02 Character-identity Geometry Development

**Status 2026-11-23:** locally executed, source-grounded, 6′5″ height verified, live Blender GUI proof complete. **Technical POC: PASS (54/54).** **Artistic reconstruction: HOLD.** No paid calls, video publication, real production changes, or source master replacement.

## Approved input — do not mutate

Read and grounded against:
- `%USERPROFILE%\Documents\futureworks-p04-data\character-library\FWAI-M001\v2.0\FWAI-M001_FINAL_VISUAL_DESIGN_LOCK_v2.json`
- The **exact** V2 canonical PNG `FWAI-M001_APPROVED_FINAL_MASTER_V2.0.png` SHA256 `480263bdd7637bfb2d90cc2deecdeb616eef03492a35216dbebfd3b1f44c555c`.
- Approved height: **77 inches = 1.9558 m**.

The V2 design lock protects a slender humanoid industrial vinyl technician with obsidian-plum armor, angular cyan visor, swept-back finned titanium-accented helmet, circular sensors, upper-spine cyan conduits, mechanically detented vents, high-torque actuator joints and a **flush forearm squeegee/torch/knife tool dock**. The design is an image master, **not** a certified/complete 3D character.

## New VQ04.02 staged work

- Generated a deterministic **70-part** data-only identity study from these categories: angular layered chest and hip plates; neck chassis/cover; swept-back fin and visor surfaces; two side sensors; six routed upper-spine coolant conduits plus return connectors; cooling-vent slit assemblies; paired shoulder shells; integrated forearm-tool housings, piston rails and emissive trims.
- Existing VQ04.01 adds **70 lower-body mechanical components**, bringing new visible details in the VQ04.02 live Blender window to **140 additive objects** across two independent removable collections.
- A read-only SHA-pinned JSON manifest is guarded against unknown asset IDs, unexpected shape/fields, bad bone/material attachment, unbounded or nonfinite coordinates, oversized files, and unknown path injection. There is no arbitrary Python from a command message or network listener. The Blender side is a narrow geometry importer with explicit types.
- The old VQ03 mech had a **hidden height violation**: fin geometry reached about **1.9729m**, not 1.9558m. VQ04.02 includes a live, **reversible in-memory** fin clamp to exactly **1.9558m**, verified at pose frames **1, 36 and 72** using evaluated mesh vertices (the cached Blender bounding box was misleading). This does not overwrite original .blend files.
- The V2 approved PNG remains byte-identical; original VQ03 and derivative VQ04.02 scene files remain untouched by live operations.

## Actual acceptance

| Proof | Result |
|---|---:|
| Identity stage Blender tests (bad payloads, parenting, pose, source, staging) | **30 / 30 PASS** |
| Height correction across three frames, reversion, source SHA check | **11 / 11 PASS** |
| V2 lock features & master hash audit | **13 / 13 PASS** |
| Total | **54 / 54 PASS** |
| Real local visible Blender GUI recognized 70 old + 70 new parts and bounded fins | **PASS** |
| Owner creative approval of identity fidelity | **HOLD** |
| Nissan true automotive mesh / vinyl simulation / cinematic visual acceptance | **NOT DONE** |

This only establishes presence of reference-inspired features in a better mechanical proxy. It **does not establish an exact geometrical match** to the high-detail approved V2 concept, realistic contact/adhesion, production-grade head/forearm mechanics, or real automotive fidelity.

## Where to watch live

Use the **newest** Blender 5.3 window named `FWAI_VQ04_02_IDENTITY_SCENE` on El_Corredor. To reopen:

`%USERPROFILE%\Documents\futureworks-vq04-02\scene\FWAI_VQ04_02_IDENTITY_SCENE.blend`

Press **N → Future Works → Live Sync**. The new objects are in:
- `FWAI LIVE PREVIEW / VQ04 LOWER BODY` — 70 from VQ04.01
- `FWAI LIVE PREVIEW / VQ04.02 V2 IDENTITY` — 70 new V2-inspired elements

These are *live transient previews*, not persisted in the .blend. Observe pose changes at timeline frames **1, 36, 72**. The newest add-on uses its own dedicated file queue `Documents\futureworks-vq04-02\live_bridge_v2` so previous Blender windows cannot inadvertently consume its commands.

Repeat local PowerShell commands:

```powershell
$python = "$env:USERPROFILE\Documents\futureworks-p04-comfyui\.venv\Scripts\python.exe"
$sender = "$env:USERPROFILE\Documents\futureworks-vq04-02\send_live_command.py"
& $python $sender --inspect-identity
& $python $sender --clear-identity
& $python $sender --load-identity
& $python $sender --apply-height-guard
& $python $sender --inspect-height-guard
& $python $sender --pose 36
```

Reproducible full proof:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Documents\futureworks-vq04-02\run_vq04_02.ps1"
```

To reinstall the reviewed add-on to Blender 5.3, invoke `install_vq04_02.ps1` and open a **new** Blender window. The installer does not terminate windows with unsaved work.

## Local output / evidence

`%USERPROFILE%\Documents\futureworks-vq04-02\evidence\VQ04_02_REVIEW.html` is a visual dashboard comparing actual before/after Blender proof and canonical V2 reference. JSON evidence: `VQ04_02_TESTS.json`, `VQ04_02_HEIGHT_GUARD_TEST.json`, `VQ04_02_DESIGN_COVERAGE.json`, `VQ04_02_GUI_ACK.json`, `VQ04_02_COMBINED_ACCEPTANCE.json`.

The repo contains *source and documentation only*. No PNGs, 3D binary scenes, paid assets, generated receipts, credentials, model weights or private data should be committed.

## Next real checkpoint VQ04.03

Now that the torso/head silhouette is represented and the height guard is accurate, prioritize anatomically plausible **hand/finger articulation and rigged tool housing** that preserve correct contact with a physically separate vinyl sheet. Then validate a Nissan body-accurate mesh and baked cloth/collision/adhesion mechanics. Any claim of cinematic photorealism or approved V2 identity requires owner visual review against the locked master.

## Source control note

This branch is **stacked** on `dev/vq04-live-geometry` (PR #28) because that base PR is still a GitHub draft and the connected GitHub integration could not mark it ready for review. Retarget VQ04.02 to main once #28 is merged; do not bypass the existing branch-protection/review process.
