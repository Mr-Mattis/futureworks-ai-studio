# Future Works AI Studio: BL02 one-command offline proof, read-only WLM included.
# No provider calls, no production changes, no deletion.
param([switch]$SkipInventory)
$ErrorActionPreference = "Stop"
$root = Join-Path $env:USERPROFILE "Documents\futureworks-maintenance"
$blender = Join-Path $env:ProgramFiles "Blender Foundation\Blender 5.3\blender.exe"
$python = Join-Path $env:USERPROFILE "Documents\futureworks-p04-comfyui\.venv\Scripts\python.exe"
$scene = Join-Path $root "poc-bl05-gpu-baseline\BL01_pose_manifest.json"
if (!(Test-Path $blender)) { throw "Blender 5.3 executable missing" }
if (!(Test-Path $python)) { throw "Local ComfyUI Python missing" }
if (!(Test-Path $scene)) {
    & $blender --background --factory-startup --python (Join-Path $root "blender_pose_plate.py") -- (Join-Path $root "poc-bl05-gpu-baseline")
    if ($LASTEXITCODE -ne 0) { throw "Blender step failed" }
}
$rigEvidence = Join-Path $root "poc-bl04-rig-test\BL01_pose_manifest.json"
if (!(Test-Path $rigEvidence)) {
    & $blender --background --factory-startup --python (Join-Path $root "blender_pose_plate.py") -- (Join-Path $root "poc-bl04-rig-test")
    if ($LASTEXITCODE -ne 0) { throw "Blender articulated pose verification failed" }
}
& $python (Join-Path $root "bl05_comfy_baseline.py")
if ($LASTEXITCODE -ne 0) { throw "ComfyUI + pixel-lock step failed" }
& $python (Join-Path $root "quality_gate.py") poc-bl05-gpu-baseline
if ($LASTEXITCODE -ne 0) { throw "Visual gross-artifact quality test failed" }
$qc = Get-Content (Join-Path $root "poc-bl05-gpu-baseline\VQ02_GROSS_ARTIFACT_QA.json") -Raw | ConvertFrom-Json
if ($qc.gross_flat_fill_test -ne 'PASS') { throw "Gross artifact found; creative review blocked" }
if (!$SkipInventory) {
    & $python (Join-Path $root "wlm01_inventory.py")
    if ($LASTEXITCODE -ne 0) { throw "Inventory step failed" }
}
& $python (Join-Path $root "test_vq_wlm.py")
if ($LASTEXITCODE -ne 0) { throw "Proof validation failed" }
Write-Output "FWAI_BL05_POC_PIPELINE_PASS"
Write-Output ("REVIEW_IMAGE=" + (Join-Path $root "poc-bl05-gpu-baseline\BL01_P04_review_triptych.png"))
Write-Output "APPROVAL=REQUIRED: No publishing or spending authorized."
