# Future Works AI Studio VQ03: safe repeatable local technical proof.
# Do not merge/publish/upload/delete/run paid APIs. Reuse verified immutable results.
$ErrorActionPreference = "Stop"
$root = Join-Path $env:USERPROFILE "Documents\futureworks-vq03"
$out = Join-Path $root "proof-v5"
$blender = Join-Path $env:ProgramFiles "Blender Foundation\Blender 5.3\blender.exe"
$python = Join-Path $env:USERPROFILE "Documents\futureworks-p04-comfyui\.venv\Scripts\python.exe"
$blend = Join-Path $out "FWAI_VQ03_MECH_NISSAN_VINYL.blend"
if (!(Test-Path $blender)) { throw "Blender 5.3 is not installed at the verified path" }
if (!(Test-Path $python)) { throw "Local ComfyUI Python not present" }
if (!(Test-Path $blend)) {
    & $blender --background --factory-startup --python (Join-Path $root "build_vq03_scene.py") -- $out
    if ($LASTEXITCODE -ne 0) { throw "Blender scene build failed" }
    & $blender --background $blend --python (Join-Path $root "prepare_gui.py") -- $out
    if ($LASTEXITCODE -ne 0) { throw "Blender review workspace preparation failed" }
}
& $blender --background $blend --python (Join-Path $root "validate_blender_vq03.py") -- $out
if ($LASTEXITCODE -ne 0) { throw "Blender structural tests failed" }
& $python (Join-Path $root "comfy_vq03.py")
if ($LASTEXITCODE -ne 0) { throw "ComfyUI local image stage failed; inspect persistent task receipt before any retry" }
$movie = Join-Path $out "VQ03_three_pose_3sec.mp4"
if (!(Test-Path $movie)) {
    & $blender --background $blend --python (Join-Path $root "render_video.py") -- $out
    if ($LASTEXITCODE -ne 0) { throw "Blender video frame rendering failed" }
    $wslRoot = "/mnt/c/Users/" + $env:USERNAME + "/Documents/futureworks-vq03/proof-v5"
    & wsl.exe -d Ubuntu -- ffmpeg -hide_banner -loglevel error -framerate 24 -i "$wslRoot/frames/F_%04d.png" -vcodec libx264 -pix_fmt yuv420p -crf 19 "$wslRoot/VQ03_three_pose_3sec.mp4"
    if ($LASTEXITCODE -ne 0) { throw "WSL FFmpeg video assembly failed" }
}
& $python (Join-Path $root "test_vq03.py")
if ($LASTEXITCODE -ne 0) { throw "Integrated acceptance checks failed" }
Write-Output "FWAI_VQ03_TECHNICAL_POC_PASS"
Write-Output ("BLENDER_FILE=" + $blend)
Write-Output ("REVIEW_DASHBOARD=" + (Join-Path $out "VQ03_REVIEW.html"))
Write-Output "CREATIVE_QA=HOLD; VINYL_PHYSICS=HOLD; WIDEBODY=BACKLOG; PAID_CALLS=0"
