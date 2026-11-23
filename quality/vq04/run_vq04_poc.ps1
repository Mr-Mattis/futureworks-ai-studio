# Future Works AI Studio — VQ04 live geometry injection POC (safe local-only).
# Runs staged data-only mesh tests, then demonstrates an actual visible GUI update.
# Does not save Blender scene or modify original canonical references.
$ErrorActionPreference = "Stop"
$root = Join-Path $env:USERPROFILE "Documents\futureworks-vq04"
$blend = Join-Path $root "scene\FWAI_VQ04_LIVE_SCENE.blend"
$source = Join-Path $env:USERPROFILE "Documents\futureworks-vq03\proof-v5\FWAI_VQ03_MECH_NISSAN_VINYL.blend"
$blender = Join-Path $env:ProgramFiles "Blender Foundation\Blender 5.3\blender.exe"
$py = Join-Path $env:USERPROFILE "Documents\futureworks-p04-comfyui\.venv\Scripts\python.exe"
$sender = Join-Path $root "send_live_command.py"
if (!(Test-Path $source)) { throw "VQ03 source scene missing" }
if (!(Test-Path $blender)) { throw "Blender 5.3 missing" }
if (!(Test-Path $py)) { throw "Local Python environment missing" }
if (!(Test-Path $blend)) {
    New-Item (Split-Path $blend) -ItemType Directory -Force | Out-Null
    Copy-Item $source $blend
}
$sourceHash = (Get-FileHash $source -Algorithm SHA256).Hash
$blendHash = (Get-FileHash $blend -Algorithm SHA256).Hash
& $py (Join-Path $root "generate_lower_body.py")
if ($LASTEXITCODE -ne 0) { throw "Data-only preview manifest generation failed" }
& $blender --background $source --python (Join-Path $root "test_vq04_preview.py")
if ($LASTEXITCODE -ne 0) { throw "Blender geometry regression failed" }
$running = @(Get-Process blender -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -like "*FWAI_VQ04_LIVE_SCENE*"})
if ($running.Count -eq 0) {
    Start-Process -FilePath $blender -ArgumentList ('"' + $blend + '"') -WindowStyle Normal
    Start-Sleep -Seconds 4
}
& $py $sender --load-preview
if ($LASTEXITCODE -ne 0) { throw "Visible Blender did not acknowledge geometry injection" }
& $py $sender --inspect-preview
if ($LASTEXITCODE -ne 0) { throw "Visible Blender did not confirm its preview count" }
$ack = Get-Content (Join-Path $root "live_bridge\ack.json") -Raw | ConvertFrom-Json
if ($ack.gui_visible -ne $true -or $ack.message -notmatch "Live preview parts: 70") {
    throw "Live GUI inspection failed; do not claim visible update"
}
if ((Get-FileHash $source -Algorithm SHA256).Hash -ne $sourceHash) {throw "Original VQ03 scene was mutated"}
if ((Get-FileHash $blend -Algorithm SHA256).Hash -ne $blendHash) {throw "Live preview unexpectedly saved the derived .blend"}
Write-Output "FWAI_VQ04_LIVE_GEOMETRY_POC_PASS"
Write-Output ("VISIBLE_BLENDER=" + $blend)
Write-Output ("PREVIEW_RENDER=" + (Join-Path $root "evidence\VQ04_LOWER_BODY_LIVE_PREVIEW.png"))
Write-Output "CANONICAL_ASSETS_PRESERVED=TRUE; NO_AUTOSAVE=TRUE; CREATIVE_QA=HOLD; PAID_CALLS=0"
