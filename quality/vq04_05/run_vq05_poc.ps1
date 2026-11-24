# Future Works AI Studio VQ04.05 — reproducible LOCAL cloth proof and live Blender viewer.
# Safe by construction: no source replacement, no production actions, no paid calls.
$ErrorActionPreference="Stop"
$root=Join-Path $env:USERPROFILE 'Documents\futureworks-vq04-05'
$out=Join-Path $root 'evidence'
$blender=Join-Path $env:ProgramFiles 'Blender Foundation\Blender 5.3\blender.exe'
$py=Join-Path $env:USERPROFILE 'Documents\futureworks-p04-comfyui\.venv\Scripts\python.exe'
$master=Join-Path $env:USERPROFILE 'Documents\futureworks-p04-data\character-library\FWAI-M001\v2.0\FWAI-M001_APPROVED_FINAL_MASTER_V2.0.png'
$prior=Join-Path $env:USERPROFILE 'Documents\futureworks-vq04-04\scene\FWAI_VQ04_04_CONTACT_V2.blend'
$base=Join-Path $root 'scene\FWAI_VQ04_05_CLOTH_SOURCE.blend'
$baked=Join-Path $root 'scene\FWAI_VQ04_05_CLOTH_BAKED.blend'
if(!(Test-Path $blender) -or !(Test-Path $py) -or !(Test-Path $prior) -or !(Test-Path $master)){
 throw 'Missing required tools or approved reference assets'
}
$canonHash=(Get-FileHash $master -Algorithm SHA256).Hash
if($canonHash -ne '480263BDD7637BFB2D90CC2DEECDEB616EEF03492A35216DBEBFD3B1F44C555C'){
 throw 'Canonical V2 master SHA mismatch; stop work'
}
$priorHash=(Get-FileHash $prior -Algorithm SHA256).Hash
if(!(Test-Path $base)){Copy-Item $prior $base}
if(!(Test-Path $baked)){
 & $blender --background $base --python (Join-Path $root 'build_bake_cloth.py')
 if($LASTEXITCODE -ne 0){throw 'Native Blender cloth baking failed'}
}
$manifest=Get-Content (Join-Path $out 'VQ04_05_BAKE_MANIFEST.json') -Raw|ConvertFrom-Json
if((Get-FileHash $baked -Algorithm SHA256).Hash -ne $manifest.sha256){
 throw 'Baked scene SHA mismatch; no overwrite or cache clear allowed'
}
& $blender --background $baked --python (Join-Path $root 'validate_baked_cloth.py')
if($LASTEXITCODE -ne 0){throw 'Full-range cloth validation failed'}
& $blender --background --factory-startup $baked --python (Join-Path $root 'test_vq05_ui.py')
if($LASTEXITCODE -ne 0){throw 'Blender viewer and safety regression failed'}
if(!(Test-Path (Join-Path $out 'VQ04_05_RENDER_PROOF.json'))){
 & $blender --background $baked --python (Join-Path $root 'render_baked_cloth.py')
 if($LASTEXITCODE -ne 0){throw 'Raw cloth render failed'}
}
if(!(Test-Path (Join-Path $out 'VQ04_05_SMOOTH_RENDER.json'))){
 & $blender --background $baked --python (Join-Path $root 'render_smooth_stills.py')
 if($LASTEXITCODE -ne 0){throw 'Smooth render failed'}
}
$movieRaw=Join-Path $out 'VQ04_05_BAKED_CLOTH_3SEC.mp4'
$movieSmooth=Join-Path $out 'VQ04_05_SMOOTH_CLOTH_3SEC.mp4'
$wslBase="/mnt/c/Users/"+$env:USERNAME+"/Documents/futureworks-vq04-05/evidence"
if(!(Test-Path $movieRaw)){
 & wsl.exe -d Ubuntu -- ffmpeg -hide_banner -loglevel error -framerate 24 -i "$wslBase/frames/F_%04d.png" -vcodec libx264 -pix_fmt yuv420p -crf 19 "$wslBase/VQ04_05_BAKED_CLOTH_3SEC.mp4"
 if($LASTEXITCODE -ne 0){throw 'Raw FFmpeg encoding failed'}
}
if(!(Test-Path $movieSmooth)){
 & wsl.exe -d Ubuntu -- ffmpeg -hide_banner -loglevel error -framerate 24 -i "$wslBase/frames_smooth/S_%04d.png" -vcodec libx264 -pix_fmt yuv420p -crf 19 "$wslBase/VQ04_05_SMOOTH_CLOTH_3SEC.mp4"
 if($LASTEXITCODE -ne 0){throw 'Smooth FFmpeg encoding failed'}
}
$running=@(Get-Process blender -ErrorAction SilentlyContinue|Where-Object {$_.MainWindowTitle -like '*FWAI_VQ04_05_CLOTH_BAKED*'})
if($running.Count -eq 0){
 Start-Process -FilePath $blender -ArgumentList ('"'+$baked+'"') -WindowStyle Normal
 Start-Sleep -Seconds 3
}
& $py (Join-Path $root 'send_live_cloth.py') --inspect
if($LASTEXITCODE -ne 0){throw 'Visible Blender GUI did not acknowledge live review'}
& $py (Join-Path $root 'test_vq05_acceptance.py')
if($LASTEXITCODE -ne 0){throw 'Final acceptance regression failed'}
if((Get-FileHash $master -Algorithm SHA256).Hash -ne $canonHash){throw 'Approved master changed'}
if((Get-FileHash $prior -Algorithm SHA256).Hash -ne $priorHash){throw 'Previous scene changed'}
Write-Output 'FWAI_VQ04_05_CLOTH_TECHNICAL_PASS'
Write-Output ('REVIEW='+(Join-Path $out 'VQ04_05_REVIEW.html'))
Write-Output ('BLENDER='+$baked)
Write-Output 'PHYSICAL_CLOTH=BAKED_72_FRAMES; ADHESIVE_FORCE=HOLD; CINEMA_APPROVAL=HOLD'
