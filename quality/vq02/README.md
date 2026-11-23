# Future Works AI Studio — VQ-02 / BL-01 / WLM-01 local proof

## Architecture and scope

A reproducible, local-only development experiment uses Blender 5.3 to create an actual editable articulated pose armature and a transparent scene plate, then ComfyUI FLUX.3 Klein + original mech/car references to refine the masked leg region on the **existing** Nissan scene, then pixel-level composition to guarantee that no pixel strictly outside the selected mask changes. QA tests and a read-only file/worktree audit follow.

This **does not prove final cinematographic realism**, real-world vinyl physics, an accurate 3D car model, video motion, or approved end-to-end publication. The mech is a proxy rig in image-aligned blocking space, not a verified production mechanical skeleton. The Blender guide is distinct from final compositing.

## Run on the authorized Windows development machine

From Windows PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Documents\futureworks-maintenance\run_bl02_poc.ps1"
```

This one command reuses immutable rendered Blender scene and Comfy GPU receipt when already complete, rebuilds the read-only inventory, and executes acceptance tests. A previous paid-run approval **does not** carry over: no Runway request, external media upload, n8n activation, permanent deletion, or publication is in scope.

The isolated output lives under `%USERPROFILE%\Documents\futureworks-maintenance\poc-bl02`:

- `BL01_mech_pose.blend` — editable Blender source with four articulated limb chains.
- `BL01_mech_pose_overlay.png` — rendered transparent 1024×576 pose guide.
- `BL01_pose_manifest.json` — deterministic pose control points and scene artifact SHA256.
- `BL01_guided_input.png`, `BL01_edit_mask.png` — original Nissan scene with pose guide and edit mask.
- `BL01_comfy_raw.png` — raw local GPU image result.
- `BL02_P04_composite.png` — pixel-locked finished candidate, **unapproved**.
- `BL01_P04_review_triptych.png` — original, Blender guided, and composite side by side.
- `BL01_P04_GPU_RECEIPT.json` — immutable task ID, source hashes, audit status, approval false.

The first experimental version (`poc-bl01`) is retained for traceability: latent inpaint produced an unacceptable flat gray region within the edit mask. The second experiment (`poc-bl02`) changes to image-to-image conditioning followed by pixel-protected regional blending. No failed outputs were silently removed or relabeled successful.

## Acceptance gates

1. Native Blender scene and rendered pose manifest exist and match SHA.
2. Real local Comfy GPU task receipt has terminal success and a valid PNG.
3. Result maintains identical pixel values outside the mask.
4. Reference source SHA256 still matches before/after.
5. No paid-provider calls, web uploads, or active n8n changes.
6. Thirteen offline code/data checks pass, including a verified articulated-bone rotation that changes visible mesh geometry.
7. **Human creative QA remains required**: plausibility, mech identity, vinyl contact/coverage, vehicle integrity, and workshop continuity. A passing technical gate is not a creative approval.

## Workspace lifecycle

`wlm01_inventory.py` scans P04/P05 *data* roots read-only and writes `WLM01_report.json` plus `WLM01_inventory.csv`. It conservatively identifies protected records, files requiring review, regenerable cache candidates, and hash-identical duplicate groups.

`wlm02_worktrees.py` audits the WSL Git worktree graph. A commit reachable from `main` is **not proof** a worktree is safe to remove. Worktree status includes dirty state, branch and current commit; no branch/worktree deletion is implemented.

A Windows Scheduled Task named `FutureWorks-WLM01-ReadOnlyInventory` was created to run the inventory daily at 03:30 local time; its first manual execution returned exit code 0. Read-only n8n workflow metadata snapshot `WLM02_n8n_readonly_snapshot.json` is stored locally outside the public repository. Inactive workflow does not mean obsolete. Active production definitions are protected; no workflow is modified.

**Retention policy is not active.** Quarantine, deletion, and cleanup scheduling remain disabled until dependency verification and owner-reviewed recovery testing. It is unsafe to automatically delete generated media and historical receipts based on age or filename patterns alone.

## Isolation and control

- This branch contains only source code and documentation; the original approved images, characters, source media, model binaries, receipts, credentials, and generated .blend/.png remain outside Git.
- The original Nissan source file and original master mech image are never overwritten.
- Outputs are not licensed, marked approved, or passed to Runway.
- Git/n8n production is unchanged by this local proof.
