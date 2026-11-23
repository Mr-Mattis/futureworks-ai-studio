# Future Works AI Studio — VQ-02 / BL-01 / WLM-01 isolated proof

**Engineering disposition:** PASS for a reproducible one-command local Blender → ComfyUI → pixel-locked composite → quality gate → read-only workspace inventory workflow. **Creative disposition:** HOLD. The mech's legs/feet, physical contact, and vinyl realism do not yet meet approval criteria. No paid provider, production activation, automatic deletion, or publication.

## Actual hardware and evidence

- Blender 5.3.0 generated an editable mech armature with limb meshes parented to bones, transparent pose plate, and a second render with a rotated leg bone. The two renders have different SHA256 hashes, proving a change to the bone drives visible geometry. It is a **blocking proxy**, not a production 3D mech or validated physics simulation.
- Local Radeon RX 9070 XT + ComfyUI generated a real output on the pinned existing SD1.5 local checkpoint. The successful BL05 GPU task is recorded at `poc-bl05-gpu-baseline/BL01_P04_GPU_RECEIPT.json`. The proof uses a pose-guide overlay, SD1.5 img2img and masked composite.
- QA verified **zero pixels changed outside the defined mask**, original source SHA unchanged, image geometry, completed GPU receipt, gross flat-fill detection, and no paid Runway calls. **13/13 integration assertions passed** in `test_vq_wlm.py`.
- Source, approved mech model references, and clean Nissan images remain untouched; large PNGs, .blend files, local receipts, model binaries, credentials, and private review dashboard stay outside Git.
- Review dashboard: `%USERPROFILE%\Documents\futureworks-maintenance\poc-bl05-gpu-baseline\VQ02_ENGINEERING_REVIEW.html`.

## Run the local integrated proof

Open **Windows PowerShell**:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Documents\futureworks-maintenance\run_bl05_poc.ps1"
```

The script checks that Blender and ComfyUI are installed, preserves completed model receipts rather than resubmitting, exercises the rig evidence and GPU compositor, runs the gross-artifact detector, refreshes read-only asset inventory, executes 13 assertions, and prints a review image location. BL05 is idempotent when previously generated input hashes still match. The ComfyUI development instance must be running at `127.0.0.1:8188` for *new* generations.

## Documented failed experiments

- **BL01** — original FLUX.3 Klein masked-inpainting route completed but generated a flat gray fill over the mech leg. Detector recorded a 19.84% dominant color within the masked area and correctly rejected the gross defect.
- **BL02** — FLUX.3 Klein full img2img exceeded the 720-second bound; interruption requested after identifying the exact local job and verifying no other queued tasks. Terminal timeout/interrupted receipt preserved, no blind resubmission. Local-only ComfyUI development server restarted with the same localhost arguments.
- **BL05** — successful SD1.5 backup in ~10 seconds on the local AMD GPU. No gray fill; however duplicate/ghosted leg and foot appearance remains visible. **It is not suitable for Runway input or publication** without further geometry/material refinement.

## Workspace lifecycle and safe cleanup

- `wlm01_inventory.py` scans P04/P05 *data* folders without moving/deleting files. It writes a CSV asset ledger and JSON with SHA256 duplicate groupings, protected paths and review-only cache candidates.
- Initial real inventory: **395 files / 222,793,950 bytes**, including **115 protected**, **261 review-only**, **19 cache-review**, **10 duplicate groups**, **0 errors**. Duplicates are NOT automatic delete candidates.
- `wlm02_worktrees.py` inventories WSL Git worktrees; result includes active/dirty flags and commit reachability, not deletion eligibility. Initial review: 18 worktrees including this new isolated proof worktree, one dirty.
- `WLM02_n8n_readonly_snapshot.json` records 27 workflow metadata entries, 2 active and 25 inactive at inspection. No workflow was modified or archived.
- Windows Task Scheduler task `FutureWorks-WLM01-ReadOnlyInventory` runs **daily at 03:30** local time. First manual invocation had exit code 0. The task runs inventory only.
- **Deletion, quarantine, and automatic worktree removal are disabled.** Later retention/quarantine requires dependency verification, recoverable backups, explicit owner-approved policy and isolated tests.

## Acceptance gates

| Gate | State |
| --- | --- |
| Native Blender mesh follows bone pose | PASS |
| Actual local AMD GPU completion | PASS (SD1.5 fallback) |
| Pixel-for-pixel preservation outside mask | PASS |
| Gross flat-gray artifact detector | PASS (BL05 only) |
| 13 offline integrated assertions | PASS |
| Production photorealism, realistic vinyl and hand/leg physics | **HOLD** |
| Runway / n8n production integration | **NOT AUTHORIZED, NOT IMPLEMENTED** |
| Automatic permanent deletion | **DISABLED** |

This is a reviewable local technical proof, not a final cinematographic asset or a released automation.
